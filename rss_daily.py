import os
import random
import time
from datetime import datetime

import feedparser
import requests

from md2html import md2html

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44',
    'Connection': 'close'
}

keywords = [
    'secure', 'security', 'privacy', 'protect', 'defense', 'attack', 'robust',
    'biometric', 'steal', 'extraction', 'membership infer', 'federate', 'fair',
    'interpretability', 'explainability', 'watermark', 'diffusion'
]
categories = ['cs.CV', 'cs.CL', 'cs.CR', 'cs.LG']


def find_keyword(summary):
    summary = summary.lower()
    for keyword in keywords:
        if keyword in summary:
            return keyword
    return None


def check_title(title):
    words = title.split('(')[-1].split()
    if len(words) > 2:
        return False
    category = words[1][1:6]
    if category in categories:
        return True
    return False


def get_code_url(short_id):
    base_url = 'https://arxiv.paperswithcode.com/api/v0/repos-and-datasets/'
    time.sleep(random.random())
    data = requests.get(base_url + short_id, headers=headers).json()
    if data and 'code' in data:
        if data['code'] and 'official' in data['code']:
            if data['code']['official'] and 'url' in data['code']['official']:
                return data['code']['official']['url']
    return None


def main():
    rss_addr = 'http://export.arxiv.org/rss/'
    paper_ids = set()
    keywords_bin = {k: list() for k in keywords}
    for category in categories:
        data = feedparser.parse(f'{rss_addr}{category}')
        if data and hasattr(data, 'entries') and len(data.entries) > 0:
            for entry in data.entries:
                if entry.id in paper_ids:
                    continue
                if not check_title(entry.title):
                    continue
                keyword = find_keyword(entry.title)
                if keyword is None:
                    keyword = find_keyword(entry.summary)
                if keyword is None:
                    continue
                item = '### Title: {}\n'.format(entry.title)
                item += '* Paper URL: [{}]({})\n'.format(
                    entry.link, entry.link)
                code_url = get_code_url(entry.id.split('/')[-1])
                if code_url is not None:
                    item += f'* Code URL: [{code_url}]({code_url})\n'
                else:
                    item += f'* Code URL: null\n'
                item += f'* Copy Paste: `<input type="checkbox">[[{entry.link.split("/")[-1]}] {entry.title.split(".")[0]}]({entry.link}) #{keyword}`\n'
                item += f'* Summary: {entry.summary}\n\n'
                keywords_bin[keyword].append(item)
                paper_ids.add(entry.id)

    now = datetime.utcnow()
    with open('README.md', 'w') as fp:
        fp.write(f'# arxiv-daily\n')
        fp.write(f'updated on {now}\n')
        fp.write(f'| keyword | count |\n')
        fp.write(f'| - | - |\n')
        for keyword in keywords:
            fp.write(f'| {keyword} | {len(keywords_bin[keyword])} |\n')
    os.makedirs('rss/', exist_ok=True)
    file = '{}.md'.format(datetime.strftime(now, '%Y-%m-%d'))
    with open(f'rss/{file}', 'w', buffering=1) as fp:
        for keyword in keywords:
            fp.write(f'## {keyword}\n')
            for item in keywords_bin[keyword]:
                fp.write(item)

    md2html(file, 'rss', 'html')


if __name__ == '__main__':
    main()
