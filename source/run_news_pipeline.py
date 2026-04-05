"""삼성전자 뉴스룸 생활가전 뉴스 자동 브리핑 - 메인 파이프라인"""

import argparse
import asyncio
import logging
import sys

from config import OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, NOTION_API_KEY
from scraper import collect_articles, fetch_article_body
from filter import filter_articles
from summarizer import summarize_article
from formatter import format_message
from telegram_sender import send_message, send_error_alert
from notion_writer import write_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


async def run_pipeline(mode: str = "auto", dry_run: bool = False) -> None:
    """전체 파이프라인을 실행한다."""
    logger.info("파이프라인 시작 (mode=%s, dry_run=%s)", mode, dry_run)

    # ① 기사 목록 수집
    logger.info("① 기사 목록 수집...")
    articles = collect_articles()
    if not articles:
        error_msg = "뉴스룸 기사 수집 실패 (0건)"
        logger.error(error_msg)
        if not dry_run:
            await send_error_alert("수집", error_msg)
        return
    logger.info("   수집 완료: %d건", len(articles))

    # ② + ③ 필터링 + 폴백
    logger.info("② 생활가전 필터링...")
    filtered, is_fallback = filter_articles(articles, mode)
    if not filtered:
        error_msg = "필터링 후 기사 0건"
        logger.error(error_msg)
        if not dry_run:
            await send_error_alert("필터링", error_msg)
        return
    logger.info("   필터링 완료: %d건 (폴백: %s)", len(filtered), is_fallback)

    # ④ 기사 본문 수집
    logger.info("④ 기사 본문 수집...")
    for article in filtered:
        if article.get("url"):
            body = fetch_article_body(article["url"])
            article["body"] = body
            logger.info("   본문 수집: %s (%d자)", article["title"][:30], len(body))
        else:
            article["body"] = ""

    # ⑤ AI 요약 생성
    logger.info("⑤ AI 요약 생성...")
    summaries = []
    for article in filtered:
        summary = summarize_article(article["title"], article.get("body", ""))
        summary["url"] = article.get("url", "")
        summaries.append(summary)
        logger.info("   요약: %s → %d포인트, %d태그",
                     article["title"][:30], len(summary["points"]), len(summary["tags"]))

    # ⑥ 텔레그램 메시지 조립
    logger.info("⑥ 메시지 조립...")
    message = format_message(summaries, is_fallback, mode)
    logger.info("   메시지 조립 완료 (%d자)", len(message))

    if dry_run:
        print("\n" + "=" * 50)
        print("📋 드라이런 결과 (실제 전송 안 함)")
        print("=" * 50)
        print(message)
        print("=" * 50)
        logger.info("드라이런 완료")
        return

    # ⑦ 텔레그램 전송
    logger.info("⑦ 텔레그램 전송...")
    sent = await send_message(message)
    if sent:
        logger.info("   텔레그램 전송 성공")
    else:
        logger.warning("   텔레그램 전송 실패")

    # ⑧ 노션 기록
    logger.info("⑧ 노션 기록...")
    recorded = write_articles(filtered, summaries, mode, is_fallback)
    logger.info("   노션 기록: %d/%d건", recorded, len(filtered))

    logger.info("파이프라인 완료!")


def main():
    parser = argparse.ArgumentParser(description="삼성전자 뉴스룸 생활가전 뉴스 자동 브리핑")
    parser.add_argument("--mode", choices=["auto", "manual"], default="auto",
                        help="실행 모드 (auto: 전날 기사, manual: 3일치)")
    parser.add_argument("--dry-run", action="store_true",
                        help="드라이런 (실제 전송/기록 안 함)")
    args = parser.parse_args()

    asyncio.run(run_pipeline(mode=args.mode, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
