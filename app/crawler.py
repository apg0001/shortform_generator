# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse


# class Crawler:
#     def __init__(self, user_agent=None):
#         self.headers = {
#             "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#         }

#     def get_domain(self, url):
#         return urlparse(url).netloc

#     def fetch_html(self, url):
#         try:
#             response = requests.get(url, headers=self.headers, timeout=5)
#             response.raise_for_status()
#             return response.text
#         except requests.RequestException as e:
#             print(f"[ERROR] 요청 실패: {e}")
#             return None

#     def parse(self, html, domain):
#         soup = BeautifulSoup(html, "html.parser")

#         if "naver.com" in domain:
#             return self.extract_naver(soup)
#         elif "daum.net" in domain:
#             return self.extract_daum(soup)
#         elif "chosun.com" in domain:
#             return self.extract_chosun(soup)
#         else:
#             return self.extract_generic(soup)

#     def extract_naver(self, soup):
#         article = soup.find("article")
#         if article:
#             return article.get_text(strip=True)
#         div = soup.find("div", {"id": "dic_area"})  # 대체 영역
#         return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

#     def extract_daum(self, soup):
#         div = soup.find("section", {"dmcf-ptype": "general"})
#         return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

#     def extract_chosun(self, soup):
#         div = soup.find("div", class_="par")
#         return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

#     def extract_generic(self, soup):
#         # 가장 긴 <p> 요소 기준으로 추출
#         paragraphs = soup.find_all("p")
#         if not paragraphs:
#             return "[ERROR] 본문 추출 실패"
#         longest = max(paragraphs, key=lambda p: len(p.get_text()))
#         return longest.get_text(strip=True)

#     def extract_article(self, url):
#         domain = self.get_domain(url)
#         html = self.fetch_html(url)
#         if not html:
#             return "[ERROR] HTML 로딩 실패"
#         return self.parse(html, domain)

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


NOISE_PATTERNS = [
    "무단전재", "재배포", "기사제보", "구독", "클릭", "바로가기", "무단 전재", "Copyright",
]
MIN_P_LEN = 15


class Crawler:
    def __init__(self, user_agent=None):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def get_domain(self, url):
        return urlparse(url).netloc

    def fetch_html(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=7)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"[ERROR] 요청 실패: {e}")
            return None

    def parse(self, html, domain):
        soup = BeautifulSoup(html, "html.parser")

        # <br>를 줄바꿈으로 보정 (일부 매체는 <p>안에 br로 문단 구분)
        for br in soup.find_all("br"):
            br.replace_with("\n")

        if "naver.com" in domain:
            return self.extract_naver(soup)
        elif "daum.net" in domain:
            return self.extract_daum(soup)
        elif "chosun.com" in domain:
            return self.extract_chosun(soup)
        else:
            return self.extract_generic(soup)

    # -----------------------
    # 공통 유틸
    # -----------------------
    def _paragraphs_from_root(self, root):
        """루트 요소에서 <p> 기반 문단 리스트 추출 + 노이즈 필터링"""
        if not root:
            return []

        paras = []
        for p in root.find_all("p"):
            # get_text에 separator 주면 <br>로 들어온 개행도 살림
            txt = p.get_text(separator=" ", strip=True)
            if not txt:
                continue
            if len(txt) < MIN_P_LEN:
                continue
            if any(bad in txt for bad in NOISE_PATTERNS):
                continue
            # 공백 정규화
            txt = re.sub(r"[ \t]+", " ", txt).strip()
            paras.append(txt)

        # 문단이 하나도 없으면 기사 컨테이너 전체 텍스트 fallback
        if not paras:
            whole = root.get_text(separator="\n", strip=True)
            whole = re.sub(r"\n{2,}", "\n", whole)
            if len(whole) >= MIN_P_LEN:
                paras = [whole]

        return paras

    def _join_paragraphs(self, paragraphs):
        """문단 리스트 → 단락 구분 보존한 단일 문자열"""
        return "\n\n".join(paragraphs) if paragraphs else "[ERROR] 본문 추출 실패"

    # -----------------------
    # 도메인별 추출
    # -----------------------
    def extract_naver(self, soup):
        # 기사 본문 컨테이너 후보
        root = soup.find("article") or soup.find("div", id="dic_area") or soup
        paras = self._paragraphs_from_root(root)
        return self._join_paragraphs(paras)

    def extract_daum(self, soup):
        # Daum은 일반적으로 section[dmcf-ptype=general] 아래 본문
        root = soup.find("section", {"dmcf-ptype": "general"}) or soup
        paras = self._paragraphs_from_root(root)
        return self._join_paragraphs(paras)

    def extract_chosun(self, soup):
        # 조선은 기사 본문에 class 'article-body' 등의 변형 존재
        root = soup.find("div", class_="article-body") or soup.find("div", class_="par") or soup
        paras = self._paragraphs_from_root(root)
        return self._join_paragraphs(paras)

    def extract_generic(self, soup):
        # 가장 텍스트가 많은 컨테이너 추정: <main>/<article>/<div> 중 텍스트 길이가 큰 것
        candidates = []
        for sel in ["article", "main", "div#content", "div.article", "section", "div"]:
            for node in soup.select(sel):
                text_len = len(node.get_text(separator=" ", strip=True))
                if text_len > 500:
                    candidates.append((text_len, node))
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            root = candidates[0][1]
        else:
            root = soup

        paras = self._paragraphs_from_root(root)
        return self._join_paragraphs(paras)

    # -----------------------
    # 외부 노출 API
    # -----------------------
    def extract_article(self, url):
        domain = self.get_domain(url)
        html = self.fetch_html(url)
        if not html:
            return "[ERROR] HTML 로딩 실패"
        return self.parse(html, domain).replace("\n", "\n\n")

    # def extract_article_paragraphs(self, url):
    #     """필요하면 문단 리스트 그대로 받고 싶을 때 사용"""
    #     domain = self.get_domain(url)
    #     html = self.fetch_html(url)
    #     if not html:
    #         return []
    #     soup = BeautifulSoup(html, "html.parser")
    #     for br in soup.find_all("br"):
    #         br.replace_with("\n")

    #     if "naver.com" in domain:
    #         root = soup.find("article") or soup.find("div", id="dic_area") or soup
    #     elif "daum.net" in domain:
    #         root = soup.find("section", {"dmcf-ptype": "general"}) or soup
    #     elif "chosun.com" in domain:
    #         root = soup.find("div", class_="article-body") or soup.find("div", class_="par") or soup
    #     else:
    #         root = soup

    #     return self._paragraphs_from_root(root)


if __name__ == "__main__":
    crawler = Crawler()
    url = "https://n.news.naver.com/article/584/0000033842?cds=news_media_pc&type=editn"
    content = crawler.extract_article(url)
    print(content)
