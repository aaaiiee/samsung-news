"""텔레그램 전송 + 수동 트리거 봇 모듈"""

import asyncio
import logging
import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


async def send_message(text: str) -> bool:
    """텔레그램으로 메시지를 전송한다."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("텔레그램 설정 미완료 (BOT_TOKEN 또는 CHAT_ID 없음)")
        return False

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode=None,
            )
            logger.info("텔레그램 전송 성공")
            return True
        except Exception as e:
            logger.warning("텔레그램 전송 실패 (시도 %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    logger.error("텔레그램 전송 최종 실패")
    return False


async def send_error_alert(step: str, error: str) -> None:
    """에러 알림을 텔레그램으로 전송한다."""
    from datetime import datetime
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    text = f"⚠️ 삼성 뉴스 자동 브리핑 오류\n- 오류 단계: {step}\n- 오류 내용: {error}\n- 시간: {now}"
    await send_message(text)
