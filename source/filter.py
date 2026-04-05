"""생활가전 키워드 필터링 + 폴백 모듈"""

import logging
from datetime import datetime, timedelta
from config import (
    APPLIANCE_KEYWORDS,
    MAX_ARTICLES,
    AUTO_DATE_RANGE_DAYS,
    MANUAL_DATE_RANGE_DAYS,
)

logger = logging.getLogger(__name__)


def filter_by_date(articles: list[dict], mode: str = "auto") -> list[dict]:
    """실행 모드에 따라 날짜 범위로 필터링한다."""
    days = AUTO_DATE_RANGE_DAYS if mode == "auto" else MANUAL_DATE_RANGE_DAYS
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y/%m/%d")

    filtered = [a for a in articles if a.get("date", "") >= cutoff_str]
    logger.info("날짜 필터 (%s, %d일): %d → %d건", mode, days, len(articles), len(filtered))
    return filtered


def filter_by_keywords(articles: list[dict]) -> list[dict]:
    """생활가전 키워드로 기사를 필터링한다."""
    matched = [
        a for a in articles
        if any(kw in a.get("title", "") for kw in APPLIANCE_KEYWORDS)
    ]
    logger.info("키워드 필터: %d → %d건", len(articles), len(matched))
    return matched


def apply_fallback(
    all_articles: list[dict],
    filtered_articles: list[dict],
) -> tuple[list[dict], bool]:
    """필터링 결과가 0건이면 전체 카테고리에서 대체한다."""
    if filtered_articles:
        return filtered_articles[:MAX_ARTICLES], False

    logger.info("생활가전 기사 0건 → 전체 카테고리 폴백")
    fallback = all_articles[:MAX_ARTICLES]
    return fallback, True


def filter_articles(articles: list[dict], mode: str = "auto") -> tuple[list[dict], bool]:
    """전체 필터링 파이프라인. (결과 기사 목록, 폴백 여부) 반환."""
    dated = filter_by_date(articles, mode)
    keyword_matched = filter_by_keywords(dated)
    result, is_fallback = apply_fallback(dated, keyword_matched)
    logger.info("최종 결과: %d건 (폴백: %s)", len(result), is_fallback)
    return result, is_fallback
