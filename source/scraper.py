"""삼성전자 뉴스룸 스크래핑 모듈"""

import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from config import NEWSROOM_URL, REQUEST_TIMEOUT, REQUEST_HEADERS, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


def fetch_page(url: str) -> str | None:
    """URL에서 HTML을 가져온다. 실패 시 재시도."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("접속 실패 (시도 %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


def parse_article_list(html: str) -> list[dict]:
    """메인 페이지 HTML에서 기사 목록을 파싱한다."""
    soup = BeautifulSoup(html, "html.parser")

    titles_el = soup.find_all(class_="article_title")
    categories_el = soup.find_all(class_="article_category")
    dates_el = soup.find_all(class_="article_data")

    articles = []
    for i, title_el in enumerate(titles_el):
        title = _clean_text(title_el.get_text())

        # URL 추출: 부모 <a> 태그에서 href
        link_el = title_el.find_parent("a") or title_el.find("a")
        url = link_el["href"] if link_el and link_el.has_attr("href") else ""

        # 카테고리
        category = categories_el[i].get_text().strip() if i < len(categories_el) else ""

        # 날짜 (YYYY/MM/DD)
        date = ""
        if i < len(dates_el):
            date_match = re.search(r"(\d{4}/\d{2}/\d{2})", dates_el[i].get_text())
            if date_match:
                date = date_match.group(1)

        articles.append({
            "title": title,
            "url": url,
            "date": date,
            "category": category,
        })

    # 중복 제거 (제목 기준)
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    return unique


def fetch_article_body(url: str) -> str:
    """개별 기사 URL에서 본문 텍스트를 추출한다."""
    html = fetch_page(url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 스크립트/스타일 제거
    for tag in soup(["script", "style"]):
        tag.decompose()

    # 기사 본문 영역 탐색
    body_el = (
        soup.find(class_="article_view_body")
        or soup.find(class_="article_body")
        or soup.find("article")
        or soup.find(class_="entry-content")
    )

    if body_el:
        return body_el.get_text(separator="\n", strip=True)

    return ""


def collect_articles() -> list[dict]:
    """뉴스룸 메인 페이지에서 기사 목록을 수집한다."""
    html = fetch_page(NEWSROOM_URL)
    if not html:
        logger.error("뉴스룸 페이지 접속 실패")
        return []

    articles = parse_article_list(html)
    logger.info("수집 완료: %d건", len(articles))
    return articles


def _clean_text(text: str) -> str:
    """HTML 엔티티 및 불필요한 공백 정리."""
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("&amp;", "&")
    return text.strip()
