# AI 개발 분석서 자동 생성 시스템

> 요구사항을 입력하면 AI가 개발 분석서를 자동으로 만들어 드립니다.

---

## 이게 뭔가요?

현업 담당자가 "파일 첨부 기능 추가해줘" 한 마디를 하면, 개발팀은 보통 1~2주를 분석에 씁니다.

이 시스템은 그 과정을 **2~3분**으로 단축합니다.

```
입력: "게시판에 파일 첨부 기능 추가"
  ↓ (2~3분)
출력: 기능 요구사항 / 기술 설계 / 보안 리스크 / 영향 범위 / 일정 추정
      → Word, PDF, Markdown, HTML, JSON 형식으로 다운로드
```

---

## 주요 기능

### 멀티 에이전트 분석 파이프라인

요구사항 하나를 AI 6명이 **한 명씩 순서대로** 분석합니다:

```
기획자 → 개발자 → 영향도 분석 → 검토자 → 품질검사 → 문서화
```

- **기획자**: 핵심/기능/비기능 요구사항 추출
- **개발자**: Java/Spring/Oracle 기준 기술 설계
- **영향도 분석**: 수정이 필요한 파일/클래스/쿼리 도출
- **검토자**: 보안/성능/일정 리스크 도출
- **품질 검사**: 90점 미만 에이전트 자동 재실행
- **문서화**: 8섹션 마크다운 분석서 완성

> 에이전트는 동시에 실행되지 않고 앞 에이전트가 완료되면 다음 에이전트가 시작됩니다. CPU 자원을 효율적으로 사용합니다.

---

### 나만의 AI 비서 (핵심 기능)

사용할수록 우리 팀 스타일로 맞춰집니다.

**프로필 설정** — 관리자 > 설정 탭
```
회사명, 팀명, 기술스택, 팀 용어, 분석 스타일
→ 한 번 저장하면 모든 분석에 자동 반영
```

**원클릭 학습** — 분석 완료 화면
```
마음에 드는 분석 결과 → "이 분석 기억하기" 버튼
→ 다음 분석부터 이 스타일로 자동 생성
```

**이전 분석 자동 참조**
```
"파일첨부" 분석 후 "게시판 검색" 분석 요청
→ 이전 파일첨부 분석을 자동으로 참고해서
   충돌 없는 설계로 분석 생성
```

---

### 기타 기능

- **파일 업로드**: Word, PDF, Excel, PowerPoint, 텍스트
- **실시간 모니터링**: 에이전트별 진행 상황 SSE 스트림
- **결과 내보내기**: Markdown / HTML / PDF / Word / JSON
- **채팅 정제**: 분석 후 "S3로 바꾸면?" 같은 후속 질문
- **소스 비교**: 실제 소스코드 ZIP 업로드 → 수정 위치 자동 도출
- **관리자 대시보드**: 이력 조회, 통계, 로그, 설정

---

## 빠른 시작

### 1. Docker로 실행 (권장)

```bash
git clone https://github.com/css9596/ai-agent.git
cd ai-agent

# 시작
docker-compose up -d --build

# Ollama 모델 다운로드 (최초 1회, 5~20분)
docker-compose exec ollama ollama pull qwen2.5:7b

# 접속
# 메인:   http://localhost:8000
# 관리자: http://localhost:8000/admin
```

### 2. 로컬 Python으로 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Claude API 모드
ANTHROPIC_API_KEY=sk-ant-... python app.py

# 로컬 Ollama 모드
LLM_MODE=local LLM_MODEL=qwen2.5:7b python app.py

# 테스트 모드 (API 없이)
LLM_MODE=mock python app.py
```

---

## LLM 모드 선택

`.env` 파일에서 설정합니다:

| 모드 | 설정 | 특징 |
|------|------|------|
| `claude` | `ANTHROPIC_API_KEY=sk-ant-...` | 가장 정확, 유료 API |
| `local` | `LLM_MODE=local` + Ollama | 무료, 완전 오프라인 |
| `mock` | `LLM_MODE=mock` | 개발/테스트용 |

---

## 나만의 AI 비서 설정 방법

### 1단계: 프로필 입력

`http://localhost:8000/admin` → **설정** 탭

```
회사명:     (주)우리회사
팀명:       서버개발1팀
기술스택:   Java 17, Spring Boot, Oracle 19c, MyBatis, JSP/jQuery
팀 용어:    TB_ 로 시작하는 테이블명, camelCase 메서드명
분석 스타일: 상세하고 꼼꼼하게
```

### 2단계: 좋은 분석 기억시키기

분석 실행 → 결과가 마음에 들면 → **"이 분석 기억하기"** 클릭

### 3단계: 쌓이면 자동으로 맞춰짐

```
5번 기억  → "우리 팀 분석서 스타일"로 수렴
10번 기억 → "이게 우리 팀 분석서다" 느낌
```

---

## 화면 구성

| 화면 | 주소 | 기능 |
|------|------|------|
| 메인 | `/` | 파일 업로드, 분석 실행, 결과 확인 |
| 관리자 | `/admin` | 이력, 통계, 로그, 프로필 설정, 학습 예시 |

---

## 시스템 요구사항

| 항목 | 권장 |
|------|------|
| RAM | 8GB 이상 (Ollama 모델용) |
| 디스크 | 20GB 이상 (Docker 이미지 + 모델) |
| OS | macOS, Linux, Windows (Docker 필수) |
| Docker | 4.0 이상 |

---

## 디렉토리 구조

```
ai-agent/
├── app.py                  # FastAPI 웹서버
├── orchestrator.py         # 에이전트 파이프라인 조율
├── database.py             # SQLite (분석이력, 프로필, 학습예시)
├── config.py               # 환경변수 및 설정
├── agents/                 # 6개 전문 에이전트
│   ├── planner.py          # 기획자
│   ├── developer.py        # 개발자
│   ├── impact_analyzer.py  # 영향도 분석
│   ├── reviewer.py         # 검토자
│   ├── quality_checker.py  # 품질 검사
│   └── documenter.py       # 문서화
├── utils/
│   ├── llm_client.py       # Ollama/로컬 LLM 클라이언트
│   ├── claude_client.py    # Claude API 클라이언트
│   ├── context_builder.py  # 프로필/히스토리 프롬프트 빌더
│   ├── queue_manager.py    # 분석 작업 큐 (순차 실행)
│   └── file_processor.py   # 파일 텍스트 추출
├── static/
│   ├── index.html          # 메인 UI
│   └── admin.html          # 관리자 대시보드
├── docker-compose.yml
└── Dockerfile
```

---

## 트러블슈팅

**분석이 중국어로 나옴**
```bash
docker-compose restart app
```

**Ollama 모델 오류**
```bash
docker-compose exec ollama ollama pull qwen2.5:7b
```

**포트 충돌**
```bash
# .env 파일에서 변경
PORT=8080
```

**CSS 안 보임**
```bash
docker-compose down && docker-compose up -d --build
```

더 자세한 내용은 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참고하세요.

---

## 변경 이력

### 최근 업데이트

- **순차 실행**: 에이전트를 한 번에 하나씩 실행해 CPU 과부하 방지 (`MAX_CONCURRENT_ANALYSES=1`)
- **검토자 한국어 수정**: 리뷰어 에이전트 응답 한국어 강제 적용
- **성능 개선**
  - DB 인스턴스 재사용 (매 분석마다 재생성 제거)
  - 통계 쿼리 5개 → 1개 통합
  - 분석 완료 처리 쿼리 3개 → 1개 통합
  - SQLite WAL 모드 활성화
  - 파일 스캔 대신 컨텍스트에서 직접 경로 참조
