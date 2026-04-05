---
title: "Plan: Samsung News Pipeline"
feature: samsung-news-pipeline
phase: plan
created: "2026-04-05"
status: active
---

## Executive Summary

| Feature | samsung-news-pipeline |
|---------|----------------------|
| Start Date | 2026-04-05 |
| Target Completion | 2026-04-06 |
| Estimated Duration | 1일 |

| Results Summary | |
|-----------------|--|
| Total Modules | 6개 (scraper, filter, summarizer, formatter, telegram, notion) |
| Total Files | 8개 |
| Total Estimated Lines | ~400 LOC |

| Perspective | Description |
|-------------|-------------|
| **Problem** | 매일 삼성전자 뉴스룸에 직접 접속하여 생활가전 기사를 확인하는 반복 작업에 약 19분/일 소요, 기사 놓침 및 주제 필터링 불가 |
| **Solution** | Python 스크립트로 뉴스 수집→필터링→AI 요약→텔레그램 전달→노션 기록 자동화, cron 스케줄 + 텔레그램 수동 트리거 |
| **Function UX Effect** | 아침 8시 텔레그램 알림으로 생활가전 뉴스 3줄 요약 수신, "삼성뉴스" 명령으로 즉시 조회 가능 |
| **Core Value** | 매일 19분 절약 (연 ~80시간), 기사 놓침 제로, 노션 DB에 자동 아카이빙 |

---

## 1. 목표

인터뷰→워크시트→자동화 설계→도구 연결→오케스트레이션 드라이런→Agent 변환까지 완료된 `삼성전자 뉴스룸 생활가전 뉴스 자동 브리핑` 파이프라인을 **실제 실행 가능한 Python 스크립트**로 구현한다.

### 성공 기준

- [ ] 삼성전자 뉴스룸에서 생활가전 기사 수집 성공
- [ ] AI 요약 (3줄 + 해시태그) 생성 성공
- [ ] 텔레그램 메시지 전송 성공
- [ ] 노션 DB 기록 성공
- [ ] cron/launchd 스케줄 등록 (매일 오전 8시)
- [ ] 텔레그램 "삼성뉴스" 수동 트리거 작동

---

## 2. 참조 문서

| 문서 | 경로 | 역할 |
|------|------|------|
| 워크시트 | `output/worksheet.md` | 업무 정의 상세 |
| 자동화 설계 | `output/workflow_rules.md` | 처리 흐름 + 예외 정책 |
| 도구 연결표 | `output/tool_connection.md` | 도구 매핑 + 환경변수 |
| 오케스트레이션 결과 | `output/orchestration_run.md` | 드라이런 결과 + 사이트 분석 |
| Agent 변환 | `output/agent_conversion.md` | Agent 구조 + 검증 체크리스트 |
| Orchestrator Agent | `.claude/agents/samsung-news-orchestrator.md` | 메인 Agent 정의 |

---

## 3. 구현 범위

### 3-A. 파일 구조

```text
source/
├── run_news_pipeline.py      # 메인 실행 스크립트 (CLI 진입점)
├── scraper.py                # 뉴스룸 스크래핑 모듈
├── filter.py                 # 생활가전 키워드 필터링 + 폴백
├── summarizer.py             # AI 요약 모듈
├── formatter.py              # 텔레그램 메시지 조립
├── telegram_sender.py        # 텔레그램 전송 + 수동 트리거 봇
├── notion_writer.py          # 노션 DB 기록 + 중복 체크
└── config.py                 # 설정 (키워드, 템플릿, URL)
.env                          # 환경변수
requirements.txt              # Python 패키지
```

### 3-B. 모듈별 구현 계획

| 순서 | 모듈 | 파일 | 핵심 기능 | 의존성 |
|------|------|------|-----------|--------|
| 1 | 설정 | `config.py` | 키워드 목록, URL, 메시지 템플릿, 환경변수 로드 | python-dotenv |
| 2 | 스크래퍼 | `scraper.py` | 뉴스룸 HTML 파싱, 기사 목록 + 본문 수집 | requests, beautifulsoup4 |
| 3 | 필터 | `filter.py` | 키워드 매칭, 날짜 필터, 중복 제거, 폴백 | — |
| 4 | 요약기 | `summarizer.py` | AI 기반 3줄 요약 + 해시태그 생성 | openai |
| 5 | 포맷터 | `formatter.py` | 텔레그램 메시지 문자열 조립 | — |
| 6 | 텔레그램 | `telegram_sender.py` | 메시지 전송 + "삼성뉴스" 봇 폴링 | python-telegram-bot |
| 7 | 노션 | `notion_writer.py` | DB 행 추가 + URL 중복 체크 | notion-client |
| 8 | 메인 | `run_news_pipeline.py` | CLI 진입점, 전체 파이프라인 오케스트레이션 | 위 모듈 전체 |

### 3-C. 구현 순서 (의존성 기반)

```text
Phase 1: 기반 (config → scraper → filter)
  └── 외부 API 없이 로컬에서 즉시 테스트 가능

Phase 2: 처리 (summarizer → formatter)
  └── AI 요약 API 연결, 메시지 조립

Phase 3: 전달 (telegram_sender → notion_writer)
  └── 외부 서비스 연결 (API 키 필요)

Phase 4: 통합 (run_news_pipeline)
  └── 전체 파이프라인 end-to-end 실행

Phase 5: 운영 (cron + 텔레그램 봇)
  └── 스케줄 등록 + 수동 트리거 서버
```

---

## 4. 기술 스택

| 구분 | 도구 | 버전 |
|------|------|------|
| 언어 | Python | 3.13+ |
| HTTP | requests | >=2.31.0 |
| HTML 파싱 | beautifulsoup4 | >=4.12.0 |
| AI 요약 | openai | >=1.0.0 |
| 텔레그램 | python-telegram-bot | >=20.0 |
| 노션 | notion-client | >=2.0.0 |
| 환경변수 | python-dotenv | >=1.0.0 |
| 스케줄러 | Mac cron/launchd | OS 내장 |

---

## 5. 환경변수 (.env)

```text
OPENAI_API_KEY=           # AI 요약용 LLM API 키
TELEGRAM_BOT_TOKEN=       # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID=         # 텔레그램 채팅 ID
NOTION_API_KEY=           # 노션 API 키
NOTION_DB_ID=             # 노션 데이터베이스 ID
```

---

## 6. 예외 처리 정책 (자동화 설계 반영)

| 단계 | 예외 | 처리 |
|------|------|------|
| 수집 | 사이트 접속 불가 | 3회 재시도 → 텔레그램 에러 알림 |
| 수집 | HTML 구조 변경 | 파싱 결과 0건 → 에러 알림 |
| 필터 | 생활가전 기사 0건 | 전체 카테고리 최신 기사로 폴백 |
| 요약 | AI API 실패 | 1회 재시도 → 제목만 전달 |
| 전송 | 텔레그램 실패 | 3회 재시도 → 에러 로그 |
| 기록 | 노션 실패 | 텔레그램은 계속, 노션만 로그 |
| 기록 | 중복 기사 | URL 기준 건너뛰기 |

---

## 7. 테스트 계획

| 테스트 | 방법 | 기대 결과 |
|--------|------|-----------|
| 스크래핑 단위 | `python3 -c "from scraper import ..."` | 기사 목록 반환 |
| 필터링 단위 | 키워드 매칭 확인 | 생활가전 기사만 선택 |
| 요약 단위 | 단일 기사 요약 | 3줄 + 해시태그 |
| 텔레그램 단위 | 테스트 메시지 전송 | 봇에서 메시지 수신 |
| 노션 단위 | 테스트 행 추가 | DB에 행 생성 |
| E2E 자동 모드 | `python3 run_news_pipeline.py --mode auto` | 텔레그램 수신 + 노션 기록 |
| E2E 수동 모드 | `python3 run_news_pipeline.py --mode manual` | 3일치 기사 수신 |

---

*Samsung News Pipeline - PDCA Plan | 2026-04-05*
