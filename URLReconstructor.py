import requests
from urllib.parse import urlparse, urljoin


class URLReconstructor:
    """
    1. 다운로드를 위한 Absolute URL 파싱
    2. CSS 파일 내 URL 파싱을 위한 처리

    url : 속성, 태그 콘텐트 등에 정의된 URL
        --> 상대 경로나 절대 경로, 혹은 fragment(#), javascript function call 등이 해당됨
        --> 이는 파싱의 대상이 되는 URL
    base : 사이트 루트 주소
        e.g. https://static.naver.net/css/base.css 파일이라면
             base는 https://static.naver.net/
             '/'으로 종료하여야함
    assetBase : 에셋을 저장할 경로 e.g. /tmp/UID (마지막은 '/'가 아니어야 함, 있을 경우 자동 변환)

    """
    saveAssetBase = ''

    def __init__(self, url, base, assetBase, cssMode=False, cssBase=None):
        self.availableExtensions = [
            'html',
            'css',
            'js',
            'bmp',
            'webp',
            'svg',
            'png',
            'jpg',
            'jpeg',
            'gif',
            'ico',
            'eot',
            'ttf',
            'otf',
            'woff'
        ]

        if not isinstance(url, str):
            print(url)

            raise Exception("[Error] url이 string / None이 아닙니다.")
        else:
            self.url = url
            self.original_url = url

        if not isinstance(base, str):
            raise Exception("[Error] base가 string이 아닙니다.")
        else:
            if base[-1] != '/':
                raise Exception(f"[Error] base는 '/'로 종료되어야합니다. - {base}")
            else:
                self.base = base

        if not isinstance(assetBase, str):
            raise Exception("[Error] assetBase가 string이 아닙니다.")
        else:
            if assetBase[-1] == '/':
                self.saveAssetBase = assetBase[0:-1]
            else:
                self.saveAssetBase = assetBase

        if not isinstance(cssMode, bool):
            raise Exception("[Error] cssMode이 bool이 아닙니다.")
        else:
            self.cssMode = cssMode

        if cssBase is not None:
            if not isinstance(cssBase, str):
                raise Exception("[Error] cssBase가 string이 아닙니다.")
            else:
                self.cssBase = urljoin(self.base, cssBase)

    def get_original_url(self):
        return self.original_url

    def checkScheme(self):
        maxCount = 5
        countCursor = 0
        locationCursor = self.base
        while countCursor < maxCount:
            r = requests.head(locationCursor)
            if 300 < r.status_code < 400:
                locationCursor = r.headers['location']
                if locationCursor.startswith("./") or \
                    locationCursor.startswith("../") or \
                    locationCursor.startswith("/"):
                    locationCursor = urljoin(self.base, locationCursor)
                countCursor += 1
            else:
                break
        return urlparse(locationCursor).scheme


    def isValidURL(self):
        if self.url.startswith("javascript") or self.url.startswith("#"):
            return False
        else:
            return True

    def isExternalURL(self):
        o = urlparse(self.base)
        ot = urlparse(self.url)
        if ot.netloc in o.netloc:
            return False
        else:
            return True

    def reconstruct(self):
        reconstructed = ''
        if 'img/v2/set_hd' in self.url:
            print("멈춰")
        # URLs for downloading assets
        if not self.cssMode:
            if self.url.startswith("http"):
                reconstructed = self.url
            # Absolute Path
            elif self.url.startswith("//"):
                scheme = self.checkScheme()
                reconstructed = f"{scheme}://{self.url[2:]}"
            # Relative Path
            elif self.url.startswith("./") or\
                    self.url.startswith("../") or\
                    self.url.startswith("/"):
                reconstructed = urljoin(self.base, self.url)
            # Relative Path
            elif len(self.url) > 0 and self.url[0].isalpha():
                reconstructed = f"{self.base}{self.url}"
        else:
            if self.url.startswith("http"):
                # External Link
                reconstructed = self.url
            elif self.url.startswith("//"):
                scheme = self.checkScheme()
                reconstructed = f"{scheme}://{self.url[2:]}"
            elif self.url.startswith("./") or \
                    self.url.startswith("../") or \
                    self.url.startswith("/") or \
                    (len(self.url) > 0 and self.url[0].isalpha()):
                # Relative Path
                reconstructed = urljoin(self.cssBase, self.url)

        if urlparse(reconstructed).path.split('.')[-1] in self.availableExtensions:
            return reconstructed
        else:
            return None
