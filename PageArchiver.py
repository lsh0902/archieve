import re
import os
import sys
import chardet
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from AssetDownloader import AssetDownloader
from URLReconstructor import URLReconstructor

CURRENT_DIRECTORY = os.path.dirname(__file__)

urlRegex = 'url\((.*?)\)'
importRegex = r"@import\s*(url)?\s*\(?([^;]+?)\)?;"

def cssFileParser(path, base, rootURL):
    """
    Reconstruct Link from External CSS File
    path : Location of downloaded CSS e.g. /tmp/UID/../something.css
    base : Base Directory of archive e.g. /tmp/UID/
    rootURL : Location of CSS aspect of page on network
        e.g. if file is from http://static.naver.net/css/base.css then
            rootURL will be http://static.naver.net/
    """
    encoding = ''
    with open(path, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']

    css = open(path, 'rt', encoding=encoding)
    content = css.read()
    content = re.sub(r'\/\*.*?\*\/', '', content)
    # Read Stream 끊김 방지
    css.close()

    cssBase = f"{'/'.join(path.split(base)[-1].split('/')[0:-1])}/"
    for regex in [importRegex, urlRegex]:
        for item in re.findall(regex, content):
            if isinstance(item, tuple):
                item = item[-1].replace('"', '').replace("'", '')
            else:
                item = item.replace('"', '').replace("'", '')

            reconstructor = URLReconstructor(item, rootURL, base, cssMode=True, cssBase=cssBase)
            url = reconstructor.reconstruct()

            downloader = AssetDownloader(url, base, url_from=path.split(base)[-1])
            _ = downloader.download()

            if _ is None:
                pass
            else:
                ot = urlparse(url)
                #상대경로 수정 로직
                if item.startswith('/'):
                    cnt = len(path.split('/')) - 2
                    add = ""
                    for i in range(cnt) :
                        add += '../'
                    replaceTo = f"{add}{ot.path}"
                elif item.startswith('../') or item.startswith('./'):
                    replaceTo = f"{item}"
                elif item.startswith('//'):
                    cnt = len(path.split('/')) - 2
                    add = ""
                    for i in range(cnt):
                        add += '../'
                    tmp = item.replace('//', '').split('/')[1:]
                    tmp = '/'.join(tmp)
                elif item[0].isalpha() :
                    #루트로 가서 처리
                    print("FD")

                print(content)
                replaceTo = re.sub(item, replaceTo, content)
                print(replaceTo)
                # 다돌고 저장
                with open(path, 'w', encoding=encoding) as f:
                    f.write(replaceTo)


if __name__ == "__main__":
    """
    Page Archiver V3
    Created by J.W.Jeon at 05.30.2021.
    
    Usage:
    python3 [file] [URL] [Directory Name to save assets]
    """
    # Archive Page
    test_arr = ["https://bbs.ruliweb.com/community/board/300143/read/52187725",
                "https://m.pann.nate.com/talk/359435076?currMenu=search&page=1&q=%EC%9A%B0%EB%A6%AC%20%EC%95%88%EB%85%95%EC%9E%90%EB%91%90%EC%95%BC",
                "https://www.inven.co.kr/webzine/news/?news=256401"]

    url = ''
    # DEBUG ONLY #
    index = 1
    url = test_arr[index]
    o = urlparse(url)
    rootURL = f"{o.scheme}://{o.netloc}{o.path}/"

    directory = os.path.join(CURRENT_DIRECTORY, str(index))
    if not os.path.exists(directory):
        os.makedirs(directory)
    # DEBUG ONLY #

    # if sys.argv and len(sys.argv) == 3:
    #     # python3 PageArchiver.py(sys.argv[0]) [URL](sys.argv[1]) [Archive Directory](sys.argv[2])
    #     url = sys.argv[1]
    #     o = urlparse(url)
    #     directory = os.path.join(CURRENT_DIRECTORY, sys.argv[2])
    #
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    # else:
    #     print("[Error] Argument Needed")
    #     exit(-1)

    try:
        r = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'})
    except Exception as e:
        print(type(e).__name__)
        print(str(e))
        exit(-1)
    else:
        if 'bobaedream' in o.netloc:
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, 'html.parser', from_encoding="utf-8")
        else:
            soup = BeautifulSoup(r.text, 'html.parser')
        tasks = [
            soup.select("[href]"),
            soup.select("[src]"),
            soup.select("[content]"),
            soup.select("[data]"),
            # soup.select("[srcset]"),
            soup.select("style"),
            soup.select("[style]"),
            soup.select("[poster]"),
            soup.select("script:not([src])"),
        ]

        # Tasks [href / src attributes]
        print("[Notice] href / src attributes")
        for tags in tasks[0:3]:
            for tag in tags:
                if 'href' in tag.attrs:
                    url = tag['href']
                elif 'content' in tag.attrs:
                    url = tag['content']
                elif 'src' in tag.attrs:
                    url = tag['src']
                elif 'data' in tag.attrs:
                    url = tag['data']
                    p = re.compile(r"(http(s)?:\/\/)([a-z0-9\w]+\.*)+[a-z0-9]{2,4}")
                    m = p.match(url)
                    if m.group(0):
                        url = str(url)

                if tag.name == 'iframe':
                    continue

                reconstructor = URLReconstructor(url, rootURL, directory)
                # Link의 javascript, fragment(#) 배제
                if reconstructor.isValidURL():
                    # Reconstruct URL
                    url = reconstructor.reconstruct()

                    # Download Asset
                    downloader = AssetDownloader(url, directory)
                    path = downloader.download()

                    # Already Downloaded
                    if path is None:
                        pass
                    else:
                        # Parse CSS if the file extension is CSS (href only)
                        ot = urlparse(url)
                        if ot.path.split('.')[-1] == 'css':
                            rootURL = f"{ot.scheme}://{ot.netloc}{'/'.join(ot.path.split('/')[0:-1])}/"
                            cssFileParser(path, directory, rootURL)
                else:
                    continue

                if url is not None:
                    ot = urlparse(url)
                    replaceTo = f".{ot.path}"

                    if 'href' in tag.attrs:
                        tag['href'] = replaceTo
                    elif 'src' in tag.attrs:
                        tag['src'] = replaceTo

        # Tasks [Style / poster Attributes, style tag content]
        print("[Notice] Style / poster Attributes, style tag content")
        for tags in tasks[4:6]:
            for tag in tags:
                if 'style' in tag.attrs:
                    # For style attribute
                    text = tag["style"]
                elif 'poster' in tag.attrs:
                    # For poster attribute
                    text = tag["poster"]
                else:
                    # For style tag content
                    text = tag.string

                for regex in [urlRegex, importRegex]:
                    for url in re.findall(regex, text):
                        url = url.strip('"').strip("'")

                        reconstructor = URLReconstructor(url, rootURL, directory)

                        replacePath = ''
                        # Link의 javascript, fragment(#) 배제
                        if reconstructor.isValidURL():
                            # Reconstruct URL
                            url = reconstructor.reconstruct()

                            # Download Asset
                            downloader = AssetDownloader(url, directory)
                            path = downloader.download()

                            if path is None:
                                pass
                            else:
                                # Parse CSS if the file extension is CSS (@import only)
                                ot = urlparse(url)
                                replacePath = ot.path
                                if ot.path.split('.')[-1] == 'css':
                                    rootURL = f"{ot.scheme}://{ot.netloc}{'/'.join(ot.path.split('/')[0:-1])}/"
                                    cssFileParser(path, directory, rootURL)
                        else:
                            continue

                        if url is not None:
                            replaceTo = f"url('.{replacePath}')"

                            text = re.sub(regex, replaceTo, text)
                            if 'style' in tag.attrs:
                                # For style attribute
                                tag["style"] = text
                            elif 'poster' in tag.attrs:
                                # For poster attribute
                                tag["poster"] = text
                            else:
                                # For style tag content
                                tag.string = text

        # Tasks [Scripts]
        print("[Notice] Scripts")
        for tag in tasks[-1]:
            if tag.string is not None:
                for url in re.findall(urlRegex, tag.string):
                    if len(url) == 0 :
                        continue
                    url = url[-1]
                    reconstructor = URLReconstructor(url, rootURL, directory)
                    url = reconstructor.reconstruct()

                    downloader = AssetDownloader(url, directory)
                    _ = downloader.download()

                    if url is not None:
                        replaceTo = url
                        tag.string = re.sub(urlRegex, url, replaceTo)

        with open(os.path.join(directory, 'index.html'), 'wt', encoding='utf-8') as f:
            f.write(str(soup))

        print("[Completed] Parse all assets in the page")