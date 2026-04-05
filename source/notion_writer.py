"""노션 페이지 기록 모듈 (블록 추가 방식, URL 중복 체크 포함)"""

import logging
from datetime import datetime
from notion_client import Client
from config import NOTION_API_KEY, NOTION_DB_ID

logger = logging.getLogger(__name__)

notion = Client(auth=NOTION_API_KEY) if NOTION_API_KEY else None

# NOTION_DB_ID를 페이지 ID로 사용 (블록 추가 대상)
PAGE_ID = NOTION_DB_ID

# 기록된 URL 캐시 (세션 내 중복 방지)
_recorded_urls: set[str] = set()


def check_duplicate(url: str) -> bool:
    """노션 페이지에 이미 기록된 URL인지 확인한다."""
    if not url:
        return False

    # 세션 내 캐시 확인
    if url in _recorded_urls:
        return True

    if not notion or not PAGE_ID:
        return False

    try:
        blocks = notion.blocks.children.list(PAGE_ID)
        for block in blocks.get("results", []):
            block_type = block.get("type", "")
            rich_texts = block.get(block_type, {}).get("rich_text", [])
            for rt in rich_texts:
                text = rt.get("text", {})
                link = text.get("link", {})
                if link and link.get("url") == url:
                    return True
                if text.get("content", "") == url:
                    return True
        return False
    except Exception as e:
        logger.warning("노션 중복 체크 실패: %s", e)
        return False


def write_article(article: dict, summary: dict, mode: str = "auto") -> bool:
    """기사 데이터를 노션 페이지에 블록으로 추가한다."""
    if not notion or not PAGE_ID:
        logger.warning("노션 설정 미완료 (API_KEY 또는 PAGE_ID 없음)")
        return False

    title = article.get("title", "제목 없음")
    url = article.get("url", "")
    date = article.get("date", "")
    category = article.get("category", "")
    points = summary.get("points", [])
    tags = summary.get("tags", [])

    # URL 중복 체크
    if url and check_duplicate(url):
        logger.info("중복 기사 건너뛰기: %s", title[:30])
        return True

    blocks = [
        # 기사 제목 (heading_3)
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": f"📰 {title}"}}]
            },
        },
        # 메타 정보
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"📅 {date}  |  🏷️ {category}  |  ⚙️ {mode}"}}
                ]
            },
        },
    ]

    # 요약 포인트
    for point in points:
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": point}}]
            },
        })

    # 해시태그
    if tags:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": " ".join(tags)}}]
            },
        })

    # 원문 링크
    if url:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "🔗 원문: ", "link": None}},
                              {"type": "text", "text": {"content": url, "link": {"url": url}}}]
            },
        })

    # 구분선
    blocks.append({"object": "block", "type": "divider", "divider": {}})

    try:
        notion.blocks.children.append(block_id=PAGE_ID, children=blocks)
        if url:
            _recorded_urls.add(url)
        logger.info("노션 기록 성공: %s", title[:30])
        return True
    except Exception as e:
        logger.error("노션 기록 실패: %s", e)
        return False


def write_header(mode: str, is_fallback: bool, count: int) -> bool:
    """날짜별 헤더를 추가한다."""
    if not notion or not PAGE_ID:
        return False

    today = datetime.now().strftime("%Y/%m/%d %H:%M")
    category = "전체 — 생활가전 기사 없음" if is_fallback else "생활가전"
    mode_label = "자동 실행" if mode == "auto" else "수동 실행"

    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {
                    "content": f"📰 삼성 뉴스룸 ({category}) - {today} | {mode_label} | {count}건"
                }}]
            },
        },
    ]

    try:
        notion.blocks.children.append(block_id=PAGE_ID, children=blocks)
        return True
    except Exception as e:
        logger.error("노션 헤더 기록 실패: %s", e)
        return False


def write_articles(
    articles: list[dict],
    summaries: list[dict],
    mode: str = "auto",
    is_fallback: bool = False,
) -> int:
    """여러 기사를 노션 페이지에 기록한다. 성공 건수 반환."""
    write_header(mode, is_fallback, len(articles))

    success = 0
    for article, summary in zip(articles, summaries):
        if write_article(article, summary, mode):
            success += 1
    logger.info("노션 기록 완료: %d/%d건", success, len(articles))
    return success
