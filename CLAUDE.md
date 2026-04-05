# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**Multi-Agent Development Analyzer** - Claude AI 에이전트들이 협력하여 비즈니스 요구사항을 전문적인 개발 분석서로 자동 변환하는 시스템.

### 핵심 특징
- **멀티에이전트 아키텍처**: 7개 specialized agents가 pipeline으로 동작
- **자동 품질 검사**: 분석 결과가 95점 미만이면 자동으로 재분석 (최대 2회)
- **채팅형 정제**: 분석 후 "S3로 바꾸면?"같은 후속 질문으로 요구사항 정제 ⭐ Phase 5A
- **소스 비교 & 수정 가이드**: 분석 결과와 실제 소스코드 비교 → 파일별 수정 위치/사유 자동 도출 ⭐ Phase 6
- **다중 포맷 지원**: 입력(텍스트/PDF/Excel/PowerPoint) → 출력(MD/HTML/PDF/Word/JSON)
- **3가지 LLM 모드**: Mock(개발), Local(Ollama), Claude(API) 자유 선택 ⭐ Phase 6
- **프로젝트 로컬 저장**: 프로젝트 ZIP 업로드 후 자동 저장 (재분석 불필요) ⭐ Phase 6
- **웹 + CLI 모드**: FastAPI 웹서버 또는 CLI로 실행

---

## 🚀 빠른 명령어

```bash
# 초기 설정
cd multi-agent
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# ⭐ LLM 모드 선택 (3가지)

# 1️⃣ Mock 모드 (기본, API 불필요, 개발/테스트용)
LLM_MODE=mock python app.py

# 2️⃣ Local 모드 (무료 Ollama LLM, Ollama 설치 필수)
# ollama pull llama3.3:70b
LLM_MODE=local LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=llama3.3:70b python app.py

# 3️⃣ Claude 모드 (Claude API, 최고 정확도)
LLM_MODE=claude ANTHROPIC_API_KEY=sk-ant-... python app.py

# CLI 실행
python main.py --input "게시판에 파일 첨부 기능 추가"
python main.py --input "./sample_requirements.txt"

# 테스트 실행
pytest tests/ -v                          # 전체 테스트
pytest tests/ --cov=. --cov-report=html  # 커버리지 리포트

# 분석 결과 확인
ls -ltr output/ | tail -1
cat output/analysis_*.md | head -100

# 프로젝트 목록 확인 (Phase 6)
ls -ltr projects/ | tail -5
```

---

## 🏗️ 아키텍처: Multi-Agent Pipeline

### 요청 흐름

```
사용자 입력 (텍스트/파일)
    ↓
Orchestrator.run() - 에이전트 파이프라인 조율
    ├─ 1️⃣ Planner Agent
    │  └─ 핵심/기능/비기능 요구사항 추출
    │     output: context["planner"] = {core_requirements, functional_requirements, ...}
    │
    ├─ 2️⃣ Developer Agent
    │  └─ Java/JSP/MyBatis 기술설계 작성
    │     output: context["developer"] = {technical_spec, db_changes, impacted_modules, effort}
    │
    ├─ 3️⃣ Impact Analyzer Agent ⭐ (Phase 4)
    │  └─ 레이어별(Controller/Service/DAO/JSP/JS) 파일 영향도 분석
    │     output: context["impact_analyzer"] = {file_impacts, db_changes, dependency_chain}
    │
    ├─ 4️⃣ Reviewer Agent
    │  └─ 보안/성능/일정 리스크 도출
    │     output: context["reviewer"] = {security_risks, performance_risks, ...}
    │
    ├─ 5️⃣ Quality Checker Agent ⭐ (Phase 4)
    │  └─ 4개 에이전트 분석 결과 품질 검사 (95점 기준)
    │  └─ 낮은 점수 에이전트는 feedback과 함께 재실행 (최대 2회)
    │     output: context["quality_checker"] = {total_score, agent_scores, retry_agents}
    │
    ├─ 6️⃣ Documenter Agent
    │  └─ 모든 context 데이터를 8섹션 마크다운으로 종합
    │     output: context["documenter"] = {markdown: "# 개발 분석서\n..."}
    │
    └─ output/*.md 저장 및 반환
```

### 분석 후 대화형 정제

```
분석 완료 후 웹 UI의 채팅 패널에서:
사용자: "S3로 저장소 바꾸면?"
    ↓
POST /api/chat/{job_id}
    ↓
Chat Agent (agents/chat_agent.py)
    ├─ 기존 context 기반 질문 분류
    ├─ "변경 요청" 감지 → requires_reanalysis: true 신호
    ├─ 파일/DB 변경 목록 + 영향도 설명
    └─ 추천 질문 3개 생성
    ↓
응답: {type: "reanalysis", answer: "...", requires_reanalysis: true, follow_up_suggestions: [...]}
```

### Context Dictionary Pattern

모든 에이전트는 **context 딕셔너리**를 통해 데이터를 누적 전달:

```python
# 기본 구조 (orchestrator.py:60-119)
context: Dict[str, Any] = {
    "input_document": str,          # 원본 입력
    "orchestrator": {...},          # 선택된 에이전트 정보
    "planner": {...},               # Planner 결과
    "developer": {...},             # Developer 결과
    "impact_analyzer": {...},       # ImpactAnalyzer 결과
    "reviewer": {...},              # Reviewer 결과
    "quality_checker": {...},       # QualityChecker 결과 + 재시도 신호
    "documenter": {markdown: "..."},# 최종 마크다운
    "output_file": str              # 저장된 파일 경로
}

# 각 에이전트는 동일한 패턴 사용:
def run(self, context: Dict[str, Any], feedback: str = "") -> Dict[str, Any]:
    input_data = context.get("upstream_agent", {})
    result = self.client.request_json(...)  # Claude API 호출
    context[self.agent_name] = result       # context에 누적
    return context
```

### Feedback 기반 재실행

품질 검사에서 낮은 점수가 나면:

```python
# quality_checker.py에서 feedback 생성
agent_scores = {
    "developer": {
        "score": 80,
        "feedback": "DB 인덱스 전략과 파일 경로 관리 방식이 미명시되었습니다."
    }
}

# orchestrator.py에서 피드백과 함께 재실행
context = agent.run(context, feedback=feedback)  # feedback 파라미터 추가
```

---

## 📁 핵심 파일 및 역할

| 파일 | 역할 | 주요 클래스/함수 |
|------|------|-----------------|
| `main.py` | CLI 진입점 | `if __name__ == "__main__"` |
| `app.py` | FastAPI 웹서버 | `@app.post("/api/analyze")`, `run_analysis()` |
| `orchestrator.py` | 에이전트 조율 | `Orchestrator.run()`, `_run_agent()`, 품질 검사 루프 |
| `agents/planner.py` | 요구사항 추출 | `PlannerAgent` |
| `agents/developer.py` | 기술 설계 | `DeveloperAgent` |
| `agents/impact_analyzer.py` | 파일/DB 영향도 ⭐ | `ImpactAnalyzerAgent` |
| `agents/reviewer.py` | 리스크 검토 | `ReviewerAgent` |
| `agents/quality_checker.py` | 품질 검사 ⭐ | `QualityCheckerAgent`, `QUALITY_THRESHOLD=95` |
| `agents/chat_agent.py` | 대화형 정제 ⭐ | `ChatAgent` |
| `agents/documenter.py` | 마크다운 생성 | `DocumenterAgent`, 고정 템플릿 구조 |
| `utils/claude_client.py` | Claude API 래퍼 | `ClaudeClient.request_json()`, `_parse_json_safely()` |
| `database.py` | SQLite 이력관리 | `Database`, `save_chat_history()` |
| `config.py` | 설정 | `Settings` (Pydantic), 환경변수 로드 |
| `static/index.html` | 웹 UI | 채팅 패널, marked.js 렌더링 |

---

## 🔑 핵심 설계 결정

### 1. **Feedback 기반 재분석 (Phase 4 추가)**
- **이유**: QualityChecker가 낮은 점수 에이전트를 감지하면, 구체적 피드백을 주입해서 재실행
- **이점**: 전체 파이프라인을 다시 도는 것보다 효율적, 컨텍스트 유지
- **제한**: 최대 2회 재시도 (무한 루프 방지)
- **구현**: `agents/*.py`의 `run(context, feedback="")` 파라미터

### 2. **Context Dictionary 누적 (전역 상태 없음)**
- **패턴**: 각 에이전트는 read-only로 필요 데이터 추출, context에 결과 추가
- **이점**: 테스트 용이, 디버깅 시 context 전체 추적 가능, 병렬화 가능

### 3. **고정 템플릿 + 동적 채움**
- **원칙**: DocumenterAgent는 템플릿 구조를 재구성하지 않고 채움 (agents/documenter.py:14-55)
- **이유**: 모든 출력이 동일한 8섹션 형식 보증

### 4. **Mock Mode로 API 호출 없이 테스트**
- `ClaudeClient(api_key=None, mock=True)` 사용 시 hardcoded 응답 반환
- `_mock_json_response()`, `_mock_text_response()` 에서 시나리오별 응답 제공
- 성능 테스트 & CI/CD에 필수

### 5. **SSE (Server-Sent Events) 실시간 모니터링**
- 분석 중 백그라운드 태스크가 진행상황을 `emit()` 콜백으로 전송
- 클라이언트가 EventSource로 수신 (static/index.html 489-575줄)

### 6. **Job Context 메모리 저장**
- app.py에서 `job_contexts[job_id] = context` 로 분석 완료 후 저장
- Chat API가 기존 context 기반으로 질문 처리 가능
- 재시작 시 손실되므로 추후 DB 영구 저장 필요

---

## 🧪 테스트 구조

### 테스트 파일 위치: `tests/`

| 파일 | 목적 | 주의점 |
|------|------|--------|
| `test_claude_client.py` | Claude API 래퍼 + JSON 파싱 | Mock 응답 검증 |
| `test_agents.py` | 각 에이전트 isolated 테스트 | `mock_client` fixture 필요 |
| `test_orchestrator.py` | 파이프라인 통합 테스트 | 모의 모드로 전체 흐름 검증 |
| `test_database.py` | SQLite 쿼리/마이그레이션 | 임시 DB 사용 |
| `test_file_processor.py` | 파일 형식 지원 | 다양한 encoding 테스트 |
| `test_performance.py` | 벤치마크 (처리량, DB CRUD 등) | 목표 성능 threshold 검증 |

### 커버리지 확인

```bash
# HTML 리포트 생성
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# 터미널 출력
pytest tests/ --cov=. --cov-report=term-missing
```

**현재 상태**: 134개 테스트, 100% 통과, 70%+ 커버리지

---

## 🛠️ 일반적인 개발 작업

### 새 기능 추가 (예: 새 에이전트)

1. `agents/new_agent.py` 생성:
```python
class NewAgent:
    name = "NewAgent"
    
    def __init__(self, client: ClaudeClient) -> None:
        self.client = client
    
    def run(self, context: Dict[str, Any], feedback: str = "") -> Dict[str, Any]:
        input_data = context.get("upstream_agent", {})
        prompt = "..."
        result = self.client.request_json(...)
        context[self.agent_name] = result
        return context
```

2. `orchestrator.py`에 추가:
```python
self.agent_map["new_agent"] = NewAgent(client)
ANALYSIS_ORDER = [..., "new_agent", ...]  # 순서 정의
```

3. `utils/claude_client.py`의 mock 응답에 케이스 추가:
```python
if "new_agent" in lower or "new_agent_keyword" in lower:
    return {"key": "value"}
```

4. 테스트 파일 생성: `tests/test_new_agent.py`

### Claude API 호출 디버깅

```python
# _parse_json_safely()에 print 추가 (77-92줄)
print(f"Raw response: {text}")  # Claude 원본 응답 확인

# 또는 모의 모드에서 검증
client = ClaudeClient(api_key=None, mock=True)
result = agent.run(context)
```

### 웹 UI 수정 (Tailwind CSS)

- `static/index.html` 수정 후 브라우저 새로고침 (핫 리로드 없음)
- Tailwind 클래스: `flex justify-center items-center p-4 rounded-lg ...`
- marked.js로 마크다운 렌더링 (11줄): `marked.parse(text)`

### 데이터베이스 마이그레이션

새 컬럼 추가 시 `database.py`의 `init_db()`에 마이그레이션 로직 추가:

```python
# 기존 테이블에 컬럼 없으면 추가
try:
    cursor.execute("PRAGMA table_info(analyses)")
    columns = [col[1] for col in cursor.fetchall()]
    if "new_column" not in columns:
        cursor.execute("ALTER TABLE analyses ADD COLUMN new_column TEXT")
except sqlite3.OperationalError:
    pass
```

---

## ⚠️ 주의사항

### 프롬프트 수정 시
- 모든 프롬프트는 **한국어**로 작성 (일관성)
- JSON 응답 형식을 명시적으로 지정: `반드시 JSON으로만 답변하세요`
- 스키마 정의를 프롬프트에 포함: `{"key": "value", ...}`

### Mock 응답 업데이트
Claude 응답 형식이 바뀌면 `_mock_json_response()`, `_mock_text_response()` 동시 수정 필요

### 에이전트 재실행 시 피드백 주입
```python
# ❌ 잘못된 방식 (feedback 무시)
context = agent.run(context)

# ✅ 올바른 방식 (피드백 포함)
feedback = quality_checker.get_feedback_for("developer")
context = developer_agent.run(context, feedback=feedback)
```

### Context 접근
- `context.get("agent_name", {})` 사용 (KeyError 방지)
- Upstream 에이전트 결과 존재 확인 후 접근

---

## 📚 참고 문서

- `README.md` - 프로젝트 소개, 빠른 시작, 기능
- `ARCHITECTURE.md` - 상세 아키텍처 설명
- `API_REFERENCE.md` - API 엔드포인트 명세
- `.github/workflows/tests.yml` - CI/CD 파이프라인
- `pytest.ini` - pytest 설정

---

## 🚀 다음 Phase 제안

**Phase 5: 채팅 기능 완성**
- ImpactAnalyzer 재실행 통합 (S3 변경 시 자동 영향도 재분석)
- 채팅 히스토리 DB 영구 저장
- 멀티턴 대화 컨텍스트 유지

**Phase 6: 기술 스택 유연화**
- Spring Boot + React, Node.js + Vue 등 지원
- 에이전트 프롬프트 동적화

**Phase 7: 팀 협업**
- 공유 링크 + 코멘트
- 버전 관리 (delta 분석)
- Jira 티켓 자동 생성
