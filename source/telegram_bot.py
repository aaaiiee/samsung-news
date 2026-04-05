"""텔레그램 봇 폴링 서버 — "삼성뉴스" 수동 트리거"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN, MANUAL_TRIGGER_COMMAND
from scraper import collect_articles
from filter import filter_articles
from summarizer import summarize_article
from formatter import format_message
from notion_writer import write_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("telegram_bot")


async def handle_samsung_news(update: Update, context) -> None:
    """'삼성뉴스' 메시지를 받으면 파이프라인을 실행한다."""
    logger.info("수동 트리거 수신: %s", update.message.text)
    await update.message.reply_text("📰 삼성 뉴스 수집 중... 잠시만 기다려주세요.")

    # ① 기사 수집
    articles = collect_articles()
    if not articles:
        await update.message.reply_text("⚠️ 뉴스룸 접속 실패. 나중에 다시 시도해주세요.")
        return

    # ② 필터링 (수동 모드: 3일치)
    filtered, is_fallback = filter_articles(articles, mode="manual")
    if not filtered:
        await update.message.reply_text("⚠️ 최근 3일간 기사가 없습니다.")
        return

    # ④⑤ 본문 수집 + AI 요약
    summaries = []
    for article in filtered:
        from scraper import fetch_article_body
        body = fetch_article_body(article.get("url", ""))
        article["body"] = body
        summary = summarize_article(article["title"], body)
        summary["url"] = article.get("url", "")
        summaries.append(summary)

    # ⑥ 메시지 조립 + 전송
    message = format_message(summaries, is_fallback, mode="manual")
    await update.message.reply_text(message)

    # ⑧ 노션 기록
    recorded = write_articles(filtered, summaries, mode="manual", is_fallback=is_fallback)
    logger.info("노션 기록: %d/%d건", recorded, len(filtered))


async def handle_start(update: Update, context) -> None:
    """/start 명령 처리."""
    await update.message.reply_text(
        '안녕하세요! 삼성전자 뉴스룸 브리핑 봇입니다.\n\n'
        '"삼성뉴스"를 입력하면 최근 생활가전 뉴스를 요약해드립니다.'
    )


def main():
    """텔레그램 봇 폴링 서버 시작."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # /start 명령
    app.add_handler(CommandHandler("start", handle_start))

    # "삼성뉴스" 메시지 핸들러
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(MANUAL_TRIGGER_COMMAND),
        handle_samsung_news,
    ))

    logger.info("텔레그램 봇 시작 (폴링 모드)... '삼성뉴스' 대기 중")
    app.run_polling()


if __name__ == "__main__":
    main()
