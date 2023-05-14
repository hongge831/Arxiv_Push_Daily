import datetime
import os
import random
from io import BytesIO

import arxiv
import openai
import pdfplumber
from requests.packages import urllib3

from md2html import md2html

urllib3.disable_warnings()
import re
import requests
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
import time

# 设置 OpenAI 的 API key
os.environ['OPENAI_API_KEY'] = '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'
openai.api_key = os.getenv('OPENAI_API_KEY')
# OPENAI_API_KEY = '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'
headers = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44',
    'Connection': 'close'
}


def add_cat_query(base_query, cat_lst):
    ans_query = base_query
    if len(cat_lst) == 0:
        return ans_query
    cat_len = len(cat_lst)
    ans_query += r' AND ('
    for idx, cat in enumerate(cat_lst):
        if idx != cat_len - 1:
            ans_query += r"""cat:'{}' OR """.format(cat)
        else:
            ans_query += r"""cat:'{}'""".format(cat)

    ans_query += r')'

    return ans_query


def add_ti_query(base_query, keyword_lst):
    ans_query = base_query
    if len(keyword_lst) == 0:
        return ans_query
    cat_len = len(keyword_lst)
    ans_query += r' AND ('
    for idx, cat in enumerate(keyword_lst):
        if idx != cat_len - 1:
            ans_query += r"""ti:'{}' OR """.format(cat)
        else:
            ans_query += r"""ti:'{}'""".format(cat)

    ans_query += r')'

    return ans_query


def make_query_str(cat_lst, keyword_lst):
    today = datetime.date.today()
    oneday = datetime.timedelta(days=3)
    yesterday = today - oneday
    today_str = str(today)
    yesterday_str = str(yesterday)
    today_str = today_str.replace('-', '')
    yesterday_str = yesterday_str.replace('-', '')

    # query_results = """submittedDate:[20230501 TO 20230510] AND (cat:'cs.AI' OR cat:'CV') AND (ti:'diffusion' OR ti:'A') """

    ans_query = r"""submittedDate:[{} TO {}]""".format(yesterday_str, today_str)

    ans_query = add_cat_query(ans_query, cat_lst)
    ans_query = add_ti_query(ans_query, keyword_lst)

    return ans_query


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def get_pages(comment):
    num_pages = -1
    if comment is None:
        return num_pages
    pattern_lst = ['\d+\spages', '\d+\spgs' '\d+\spage', '\d+\spg']
    for pattern in pattern_lst:
        out = re.findall(pattern, comment)
        if len(out) > 0:
            num_pages = int(out[0].split()[0])
            break
    return num_pages


def get_accept_info(comment):
    accept_info = None
    if comment is None:
        return accept_info
    pattern_lst = ['\w+\s\d{4}']
    for pattern in pattern_lst:
        out = re.findall(pattern, comment)
        if len(out) == 1:
            accept_info = out[0]
    return accept_info


def get_affiliation_by_langchain(text):
    template = """
        Extract the first organization name from the given text: {content}.
        if you can not find any organization, just return 'None' without any other information.
        """
    prompt = PromptTemplate(
        input_variables=["content"],
        template=template,
    )
    llm_chain = LLMChain(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
        prompt=prompt
    )
    output = llm_chain.predict(content=text[:200])

    institutions = [o.strip() for o in output.split("\n")]

    author_affiliation = list(set(institutions))

    return author_affiliation


def get_abstract_by_langchain(abstract):
    template = """Write a concise summary of the following:
    
    "{content}"
    
    Please answer in Chinese.
    CONCISE SUMMARY:"""
    prompt = PromptTemplate(
        input_variables=["content"],
        template=template,
    )
    llm_chain = LLMChain(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
        prompt=prompt
    )
    output = llm_chain.predict(content=abstract)

    return output


def open_pdf_and_get_affiliation_and_abstruct(paper_key, abstract_en):
    affiliation = ['placeholder']
    abstract_zh = 'placeholder'
    pdf_url = "https://arxiv.org/pdf/{}.pdf".format(paper_key)
    time.sleep(random.random())
    response = requests.get(pdf_url, verify=False)
    pdf_content = BytesIO(response.content)
    # 使用 pdfplumber 提取 PDF 文本
    with pdfplumber.open(pdf_content) as pdf:
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()
        num_pages = len(pdf.pages)
        affiliation = get_affiliation_by_langchain(first_page_text)
        time.sleep(21)
        abstract_zh = get_abstract_by_langchain(abstract_en)

    return num_pages, affiliation[0], abstract_zh


def get_code_url(short_id):
    base_url = 'https://arxiv.paperswithcode.com/api/v0/repos-and-datasets/'
    time.sleep(random.random())
    data = requests.get(base_url + short_id, headers=headers).json()
    if data and 'code' in data:
        if data['code'] and 'official' in data['code']:
            if data['code']['official'] and 'url' in data['code']['official']:
                return data['code']['official']['url']
    return None


def get_daily_arxiv_papers(cat_lst, keyword_lst, keywords_bin, paper_set, max_results=100):
    query_results = make_query_str(cat_lst, keyword_lst)

    search_engine = arxiv.Search(
        query=query_results,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    for idx, result in enumerate(search_engine.results()):
        paper_id = result.get_short_id()
        if paper_id in paper_set:
            continue
        paper_set.add(paper_id)
        paper_title = result.title
        paper_url = result.entry_id
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category
        comment = result.comment
        num_pages = get_pages(comment)

        accept_info = get_accept_info(comment)
        publish_time = result.published.date()
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]
        affiliation = ['placeholder']
        abstract_zh = 'placeholder'
        code_url = 'null'

        num_pages, affiliation, abstract_zh = open_pdf_and_get_affiliation_and_abstruct(paper_key, paper_abstract)

        if num_pages < 7:
            continue
        code_url = get_code_url(paper_key)
        print("idx = ", idx,
              "Time = ", publish_time,
              " title = ", paper_title,
              " author = ", paper_first_author,
              " code_url = ", code_url,
              " accept_info = ", accept_info,
              " pages = ", num_pages)
        print(affiliation)
        print(abstract_zh)

        item = '### 标题: {}\n'.format(paper_title)
        item += '* 文章链接: [{}]({})\n'.format(
            paper_url, paper_url)
        item += '* 主要机构: {}\n'.format(affiliation)
        item += '* 页数: {}\n'.format(num_pages)
        item += '* 论文接收情况: {}\n'.format(accept_info)

        if code_url is not None:
            item += f'* 代码链接: [{code_url}]({code_url})\n'
        else:
            item += f'* 代码链接: null\n'
        item += f'* 点击拷贝: `<input type="checkbox">[[{paper_url.split("/")[-1]}] {paper_title.split(".")[0]}]({paper_url}) #{keyword_lst[0]}`\n'
        item += f'* 中文总结: {abstract_zh}\n\n'
        keywords_bin[keyword_lst[0]].append(item)

    return keywords_bin, paper_set


def make_md_and_html(keyword_lst, keywords_bin):
    now = datetime.datetime.utcnow()
    with open('README.md', 'w') as fp:
        fp.write(f'# arxiv-daily\n')
        fp.write(f'updated on {now}\n')
        fp.write(f'| keyword | count |\n')
        fp.write(f'| - | - |\n')
        for keyword in keyword_lst:
            fp.write(f'| {keyword} | {len(keywords_bin[keyword])} |\n')
    os.makedirs('rss/', exist_ok=True)
    file = '{}.md'.format(datetime.datetime.strftime(now, '%Y-%m-%d'))
    with open(f'rss/{file}', 'w', buffering=1) as fp:
        for keyword in keyword_lst:
            fp.write(f'## {keyword}\n')
            for item in keywords_bin[keyword]:
                fp.write(item)

    md2html(file, 'rss', 'html')


def main():
    cat_lst = ['cs.CV', 'cv.AI', 'cs.CL']
    # cat_lst = ['cs.CV', 'cv.AI']
    keyword_lst = ['diffusion', 'data-free', 'generative', 'language model', 'transformer']
    # keyword_lst = []
    keywords_bin = {k: list() for k in keyword_lst}
    paper_set = set()
    max_results = 100
    for key in keyword_lst:
        key_words_in_lst = [key]
        keywords_bin, paper_set = get_daily_arxiv_papers(cat_lst, key_words_in_lst, keywords_bin, paper_set,
                                                         max_results)

    make_md_and_html(keyword_lst, keywords_bin)


if __name__ == '__main__':
    main()
