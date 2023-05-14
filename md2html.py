import markdown
import os


def md2html(file, in_dir, out_dir):
    name, ext = file.split('.')
    with open(os.path.join(in_dir, file)) as fp:
        text = fp.read()

    html = markdown.markdown(text)
    html = html.replace('&lt;', '<').replace('&gt;', '>')

    with open(os.path.join(out_dir, f'{name}.html'), 'w') as fp:
        fp.write(html)
        fp.write(
            '\n<script src="https://cdn.staticfile.org/clipboard.js/2.0.4/clipboard.min.js"></script>\n'
        )
        fp.write(
            '<script>new ClipboardJS(\"#copy\",{text:function(trigger){var res=\"[[%s]]\\n\\n\";var input=document.querySelectorAll(\"input\");for(var i=0;i<input.length;i++){if(input[i].type==\"checkbox\"&&input[i].checked){res+=\"- \"+input[i].nextSibling.nodeValue+\"\\n\"}}res+=\"\\n\";return res}}).on(\"success\",function(e){e.clearSelection()});</script>\n' % name
        )
        fp.write('<button id="copy">Copy All</button>\n')

    with open('index.html') as fp:
        text = fp.read()

    with open('index.html', 'w') as fp:
        fp.write(f'<div><a href="./{out_dir}/{name}.html">{name}</a></div>\n')
        fp.write(text)


def main():
    in_dir = 'rss'
    out_dir = 'html'
    os.makedirs(out_dir, exist_ok=True)
    for file in sorted(os.listdir(in_dir)):
        md2html(file, in_dir, out_dir)


if __name__ == '__main__':
    main()
