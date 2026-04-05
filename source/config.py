"""삼성전자 ���스룸 생활가전 뉴스 자동 브리핑 - 설정 모듈"""

import os
from dotenv import load_dotenv

load_dotenv()

# 삼성전자 뉴스룸 URL
NEWSROOM_URL = os.getenv("SAMSUNG_NEWSROOM_URL", "https://news.samsung.com/kr/")

# 생활가전 필터 키워드
APPLIANCE_KEYWORDS = [
    "가전", "냉장고", "세탁기", "에어컨", "건조기",
    "TV", "비스포크", "무풍", "히트펌프", "식기세척기",
    "청소기", "에어드레서",
]

# 수집 설정
MAX_ARTICLES = 5
AUTO_DATE_RANGE_DAYS = 1   # 자동 모드: 전날 이후
MANUAL_DATE_RANGE_DAYS = 3  # 수동 모드: 최근 3일

# HTTP 설정
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_RETRIES = 3
RETRY_DELAY = 10  # 초

# API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")

# 텔레그램 메시지 설정
TELEGRAM_MAX_LENGTH = 4096
MANUAL_TRIGGER_COMMAND = "삼성뉴스"

# AI 요약 프롬프트
SUMMARY_PROMPT = """아래 삼성전자 뉴스 기사를 요약해주세요.

[규칙]
- 핵심 내용을 3개의 불릿 포인트로 요약 (각 30자 이내)
- 기사에서 가장 중요한 사실, 수치, 제품명을 우선 포함
- 해시태그 3~5개 생성 (기사 핵심 키워드)
- 감탄사, 수식어 없이 정보 중심으로

[출력 형식 - 반드시 이 형식만 사용]
• 포인트 1
• 포인트 2
• 포인트 3
#태그1 #태그2 #태그3

[기사 제목]
{title}

[기사 본문]
{body}"""
