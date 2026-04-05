"""텔레그램 메시지 조립 모듈"""

from datetime import datetime
from config import TELEGRAM_MAX_LENGTH


def format_message(
    summaries: list[dict],
    is_fallback: bool = False,
    mode: str = "auto",
) -> str:
    """요약 데이터를 텔레그램 메시지 문자열로 조립한다."""
    today = datetime.now().strftime("%Y/%m/%d")
    category = "전체 — 생활가전 기사 없음" if is_fallback else "생활가전"
    mode_label = "자동 실행" if mode == "auto" else "수동 실행"

    lines = [f"📰 삼성 뉴스룸 ({category}) - {today}", ""]

    for i, s in enumerate(summaries, 1):
        lines.append(f"{i}. {s['title']}")
        for p in s.get("points", []):
            lines.append(f"• {p}")
        if s.get("tags"):
            lines.append(" ".join(s["tags"]))
        if s.get("url"):
            lines.append(f"🔗 {s['url']}")
        lines.append("")

    lines.append("---")
    lines.append(f"⏰ {mode_label} | 📊 총 {len(summaries)}건")

    message = "\n".join(lines)

    # 텔레그램 4096자 제한 처리
    if len(message) > TELEGRAM_MAX_LENGTH:
        message = _truncate_message(summaries, category, today, mode_label)

    return message


def _truncate_message(
    summaries: list[dict],
    category: str,
    today: str,
    mode_label: str,
) -> str:
    """메시지가 너무 길면 기사 수를 줄인다."""
    for count in range(len(summaries), 0, -1):
        truncated = summaries[:count]
        lines = [f"📰 삼성 뉴스룸 ({category}) - {today}", ""]
        for i, s in enumerate(truncated, 1):
            lines.append(f"{i}. {s['title']}")
            for p in s.get("points", []):
                lines.append(f"• {p}")
            if s.get("tags"):
                lines.append(" ".join(s["tags"]))
            if s.get("url"):
                lines.append(f"🔗 {s['url']}")
            lines.append("")
        lines.append("---")
        lines.append(f"⏰ {mode_label} | 📊 총 {count}건 (일부 생략)")
        msg = "\n".join(lines)
        if len(msg) <= TELEGRAM_MAX_LENGTH:
            return msg
    return f"📰 삼성 뉴스룸 ({category}) - {today}\n\n기사 요약을 불러올 수 없습니다."
