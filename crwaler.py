import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class Crawler:
    def __init__(self, user_agent=None):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def get_domain(self, url):
        return urlparse(url).netloc

    def fetch_html(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[ERROR] 요청 실패: {e}")
            return None

    def parse(self, html, domain):
        soup = BeautifulSoup(html, "html.parser")

        if "naver.com" in domain:
            return self.extract_naver(soup)
        elif "daum.net" in domain:
            return self.extract_daum(soup)
        elif "chosun.com" in domain:
            return self.extract_chosun(soup)
        else:
            return self.extract_generic(soup)

    def extract_naver(self, soup):
        article = soup.find("article")
        if article:
            return article.get_text(strip=True)
        div = soup.find("div", {"id": "dic_area"})  # 대체 영역
        return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

    def extract_daum(self, soup):
        div = soup.find("section", {"dmcf-ptype": "general"})
        return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

    def extract_chosun(self, soup):
        div = soup.find("div", class_="par")
        return div.get_text(strip=True) if div else "[ERROR] 본문 추출 실패"

    def extract_generic(self, soup):
        # 가장 긴 <p> 요소 기준으로 추출
        paragraphs = soup.find_all("p")
        if not paragraphs:
            return "[ERROR] 본문 추출 실패"
        longest = max(paragraphs, key=lambda p: len(p.get_text()))
        return longest.get_text(strip=True)

    def extract_article(self, url):
        domain = self.get_domain(url)
        html = self.fetch_html(url)
        if not html:
            return "[ERROR] HTML 로딩 실패"
        return self.parse(html, domain)
    
if __name__ == "__main__":
    crawler = Crawler()
    url = "https://n.news.naver.com/article/009/0005537920?cds=news_media_pc&type=editn"
    content = crawler.extract_article(url)
    print(content)