# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 빠른 명령어

```bash
# 로컬 개발 (mock 모드 — API 불필요)
LLM_MODE=mock python app.py
# → http://localhost:8000

# Docker 배포 (권장, Ollama 자동 포함)
docker-compose up -d --build
docker-compose logs -f app

# Ollama 모델 최초 1회 다운로드
docker-compose exec ollama ollama pull qwen2.5:7b

# CLI 모드
python main.py --input "게시판에 파일 첨부 기능 추가"

# 테스트
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

### LLM_MODE 3가지

| 모드 | 명령 | 용도 |
|------|------|------|
| `mock` | `LLM_MODE=mock python app.py` | 개발/테스트, API 불필요 |
| `local` | `LLM_MODE=local LLM_MODEL=qwen2.5:7b python app.py` | Ollama 로컬 LLM |
| `claude` | `LLM_MODE=claude ANTHROPIC_API_KEY=sk-ant-... python app.py` | Claude API |

Docker에서는 `.env.offline`이 자동 사용됨 (`LLM_MODE=local`, `LLM_BASE_URL=http://ollama:11434/v1`).

---

## 아키텍처

### Multi-Agent Pipeline

```
POST /api/analyze
    ↓
run_analysis() [asyncio background task]
    ↓
Orchestrator.run()
    ├─ select_agents()         LLM이 입력 분석 → 실행할 에이전트 목록 결정
    ├─ PlannerAgent            → context["planner"]
    ├─ DeveloperAgent          → context["developer"]
    ├─ ImpactAnalyzerAgent     → context["impact_analyzer"]
    ├─ ReviewerAgent           → context["reviewer"]
    ├─ QualityCheckerAgent     → 90점 미만이면 낮은 점수 에이전트 최대 2회 재실행
    └─ DocumenterAgent         → context["documenter"]["markdown"]
    ↓
output/analysis_YYYYMMDD_HHMMSS.md 저장
```

각 에이전트는 `context` dict를 받아 자신의 결과를 `context[agent_name]`에 추가하고 반환.  
`Orchestrator._run_agent()`가 실행 전 `client._stream_cb`을 설정 → LLM 토큰 스트리밍 → SSE `agent_thinking` 이벤트.

### SSE 실시간 스트리밍

```
Orchestrator.emit(event_type, data)
    → create_event_callback() [app.py]
    → asyncio.run_coroutine_threadsafe(event_queues[job_id].put(...), loop)
    → GET /api/stream/{job_id} SSE 스트림
    → 브라우저 handleEvent()
```

**SSE 이벤트 타입**: `status`, `agent_start`, `agent_done`, `agent_thinking`, `agent_result`, `selection`, `complete`, `error`, `heartbeat`(30초 keepalive)

### 큐 시스템 (`utils/queue_manager.py`)

`MAX_CONCURRENT_ANALYSES=1`로 순차 실행. 중요: `event_queues`(SSE 큐)와 `started_analysis_jobs`(실행 추적 set)는 별도 관리 — `stream()` 엔드포인트가 SSE 큐를 먼저 생성하므로 `event_queues` 존재 여부로 run_analysis 실행 여부를 판단하면 안 됨.

### 3-Layer 학습 (AI 비서)

- **Layer 1 팀 프로필**: `/admin` → DB `user_profile` 테이블 → `build_profile_section()` → 모든 에이전트 프롬프트에 주입
- **Layer 2 Few-shot**: 결과 화면 "이 분석 저장하기" → `training_examples` 테이블 → 다음 분석 시 프롬프트에 예시 삽입
- **Layer 3 이전 이력**: 분석 시작 시 최근 3개 분석 요약 자동 로드 → `history_context`로 주입

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `orchestrator.py` | 에이전트 파이프라인 조율, 품질 검사 루프, 스트리밍 콜백 설정 |
| `app.py` | FastAPI, SSE 큐, `started_analysis_jobs` set, 큐 이어달리기 |
| `database.py` | SQLite WAL 모드, 싱글턴 `db` 인스턴스 (`data/analysis_history.db`) |
| `config.py` | Pydantic Settings, `.env` 자동 로드 |
| `utils/llm_client.py` | Ollama/OpenAI 호환 클라이언트, `_stream_cb` 속성, 스트리밍 처리 |
| `utils/claude_client.py` | Claude API 클라이언트, `_parse_json_safely()`, mock 모드 |
| `utils/context_builder.py` | `KOREAN_INSTRUCTION`, `KOREAN_SUFFIX`, `strip_forbidden_text()` |
| `utils/queue_manager.py` | `AnalysisQueueManager`, `JobStatus` enum |
| `utils/export_formats.py` | HTML/PDF(WeasyPrint)/DOCX/JSON 내보내기, Noto Sans KR 폰트 |
| `agents/quality_checker.py` | `QUALITY_THRESHOLD=90`, `MAX_RETRIES=2` |
| `agents/documenter.py` | 고정 8섹션 마크다운 템플릿 (14~55줄) |

---

## 중요 규칙

### 한국어 강제

Ollama(qwen2.5:7b)는 기본적으로 중국어를 출력할 수 있어 이중 보호 필수:

```python
# 모든 에이전트 프롬프트 구조
prompt = (
    f"{KOREAN_INSTRUCTION}"        # 프롬프트 맨 앞
    "\n\n실제 작업 지시..."
    f"{KOREAN_SUFFIX}"             # 프롬프트 맨 끝
)
result = client.request_json(
    system_prompt="You are a ... agent. Always respond in Korean only.",
    ...
)
```

- `LLMClient`는 `_korean_system_prompt()`로 system_prompt에 한국어 규칙 자동 추가
- `ClaudeClient`는 자동 추가 없음 → `KOREAN_INSTRUCTION`이 유일한 보호막
- `select_agents()` 등 Orchestrator 직접 LLM 호출에도 동일하게 적용
- 응답 후 `strip_forbidden_text()`로 사후 필터링

### LLM 응답 방어 처리

qwen2.5:7b가 스키마를 벗어난 형태로 반환할 수 있음. 특히 `quality_checker.agent_scores`:

```python
# "agent_scores": {"planner": [90, "피드백"]}  ← list로 올 수 있음
agent_scores = qc.get("agent_scores", {})
if not isinstance(agent_scores, dict):
    agent_scores = {}
score_data = agent_scores.get(agent_name, {})
if not isinstance(score_data, dict):
    score_data = {}
```

`_to_list()` (orchestrator.py)도 동일 패턴 — LLM이 list/dict/str 무엇을 반환해도 list로 정규화.

### 스트리밍 콜백

`LLMClient._stream_cb`은 `__init__`에서 `None`으로 초기화됨. `_run_agent()`가 `hasattr()` 체크 없이 직접 설정:

```python
# orchestrator.py _run_agent()
self.client._stream_cb = lambda text: self.emit("agent_thinking", {"agent": agent_name, "text": text})
# finally:
self.client._stream_cb = None
```

`ClaudeClient`는 `_stream_cb` 미지원 — mock/claude 모드에서는 thinking 스트리밍 없음.

---

## 새 에이전트 추가

1. `agents/new_agent.py` 작성 (아래 패턴 준수)
2. `orchestrator.py`의 `ANALYSIS_ORDER`와 `agent_map`에 등록
3. `utils/claude_client.py` mock 응답에 케이스 추가

```python
from utils.context_builder import KOREAN_INSTRUCTION, KOREAN_SUFFIX

class NewAgent:
    name = "new_agent"

    def run(self, context, feedback="", examples=None):
        prompt = (
            f"{KOREAN_INSTRUCTION}"
            + (f"\n\n[피드백]\n{feedback}" if feedback else "")
            + "\n\n실제 작업 지시..."
            + f"{KOREAN_SUFFIX}"
        )
        result = self.client.request_json(
            system_prompt="You are a ... agent. Always respond in Korean only.",
            user_prompt=prompt,
        )
        context[self.name] = result
        return context
```

---

## Docker / 배포

```bash
# 컨테이너 내 파일 즉시 반영 (재빌드 불필요, 정적 파일/Python 코드)
docker cp ./static/index.html multi-agent-app:/app/static/index.html
docker-compose restart app

# 전체 재빌드 (Dockerfile 변경 시)
docker-compose up -d --build
```

**볼륨**: `./data:/app/data` (SQLite DB 영속), `./output:/app/output` (분석 결과), `./logs:/app/logs`

**Ollama 헬스 체크**: 첫 실행 시 모델 다운로드(5-20분)로 unhealthy 표시 — `start_period: 300s` 설정되어 있어 정상.

**PDF 한국어**: Dockerfile에 `fonts-noto-cjk` 설치됨. `export_formats.py` CSS에 `Noto Sans KR` 지정.
