import os
import shutil
import socket
import tempfile
from urllib.parse import urlparse
from urllib.request import urlretrieve, urlopen, Request
import requests
import urllib

class AssetDownloader:
    """
    Retrieve Site URL Assets into directory
    url : URL that is considered to be downloaded (Absolute)
    assetBase : Directory which asset will be saved e.g. /tmp/UID
    """
    def __init__(self, url, assetBase, url_from='page_markup'):
        socket.setdefaulttimeout(5)

        if not isinstance(url, str) and url is not None:
            raise Exception("[Error] url이 string이 아닙니다.")
        else:
            self.url = url

        if not isinstance(url_from, str):
            raise Exception("[Error] url_from이 string이 아닙니다.")
        else:
            self.url_from = url_from

        if not isinstance(assetBase, str):
            raise Exception("[Error] assetBase이 string이 아닙니다.")
        else:
            if assetBase[-1] != '/':
                self.assetBase = f"{assetBase}/"
            else:
                self.assetBase = assetBase

    def download(self):
        if self.url is not None:
            if 'ruli' in self.url and '.js' in self.url:
                return

            o = urlparse(self.url)
            target = f"{self.assetBase[0:-1]}{o.path}"
            dirname, filename = os.path.split(target)

            if not os.path.exists(dirname):
                os.makedirs(dirname)

            if not os.path.exists(target):
                try:
                    urlretrieve(self.url, target)
                except Exception:
                    try:
                        r = requests.get(self.url, headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'})
                        if r.status_code == 200:
                            with open(target, 'wb') as f:
                                r.raw.decode_content = True
                                shutil.copyfileobj(r.raw, f)
                        elif r.status_code == 404 :
                            raise urllib.error.HTTPError(self.url)

                    except Exception as e:
                        print(f"[Error] 다운로드 에러 {self.url} - from {self.url_from}")
                        print(str(e))
                    else:
                        print(f"[Retrieved] {self.url} -- {target}")
                        return target
                else:
                    print(f"[Retrieved] {self.url} -- {target}")
                    return target
            else:
                # print(f"[WARN] Already Downloaded {o.path}")
                pass

        return None

