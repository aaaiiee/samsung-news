"""AI 기사 요약 모듈"""

import re
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, SUMMARY_PROMPT

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def summarize_article(title: str, body: str) -> dict:
    """기사 본문을 3줄 요약 + 해시태그로 변환한다."""
    if not client:
        logger.warning("OPENAI_API_KEY 미설정 → 제목만 반환")
        return _fallback_summary(title)

    prompt = SUMMARY_PROMPT.format(title=title, body=body[:3000])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip()
        return _parse_summary(text, title)
    except Exception as e:
        logger.warning("AI 요약 실패: %s → 1회 재시도", e)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
            )
            text = response.choices[0].message.content.strip()
            return _parse_summary(text, title)
        except Exception as e2:
            logger.error("AI 요약 재시도 실패: %s → 제목만 반환", e2)
            return _fallback_summary(title)


def _parse_summary(text: str, title: str) -> dict:
    """AI 응답 텍스트에서 포인트와 태그를 파싱한다."""
    lines = text.strip().split("\n")
    points = []
    tags = []

    for line in lines:
        line = line.strip()
        if line.startswith("•") or line.startswith("-"):
            points.append(line.lstrip("•- ").strip())
        elif line.startswith("#"):
            tags = re.findall(r"#\S+", line)

    # 태그가 별도 줄이 아닌 경우 전체에서 추출
    if not tags:
        tags = re.findall(r"#\S+", text)

    # 포인트가 3개 미만이면 텍스트에서 보충
    if len(points) < 3:
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and line not in points:
                points.append(line)
            if len(points) >= 3:
                break

    return {
        "title": title,
        "points": points[:3],
        "tags": tags[:5],
    }


def _fallback_summary(title: str) -> dict:
    """AI 없이 제목 기반 폴백 요약."""
    return {
        "title": title,
        "points": [title],
        "tags": ["#삼성전자", "#뉴스"],
    }
