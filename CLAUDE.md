# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

비즈니스 요구사항을 입력하면 8개 AI 에이전트가 협력하여 Java/JSP/MyBatis 기반 개발 분석서를 자동 생성하는 시스템. FastAPI 웹서버 + CLI 모드 지원.

---

## 빠른 명령어

```bash
# 초기 설정
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# LLM 모드 선택 (3가지)
LLM_MODE=mock python app.py                                          # 개발/테스트 (API 불필요)
LLM_MODE=local LLM_MODEL=qwen2.5:7b python app.py                   # 로컬 Ollama
LLM_MODE=claude ANTHROPIC_API_KEY=sk-ant-... python app.py           # Claude API

# Docker 배포 (권장)
docker-compose up -d --build
docker-compose exec ollama ollama pull qwen2.5:7b  # 최초 1회

# CLI 실행
python main.py --input "게시판에 파일 첨부 기능 추가"

# 테스트
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

---

## 아키텍처: Multi-Agent Pipeline

### 에이전트 실행 순서

```
입력 (텍스트/파일)
    ↓
Orchestrator.run()
    ├─ 1. PlannerAgent        → context["planner"]
    ├─ 2. DeveloperAgent      → context["developer"]
    ├─ 3. ImpactAnalyzerAgent → context["impact_analyzer"]
    ├─ 4. ReviewerAgent       → context["reviewer"]
    ├─ 5. QualityCheckerAgent → context["quality_checker"]  (95점 미만 에이전트 최대 2회 재실행)
    └─ 6. DocumenterAgent     → context["documenter"]["markdown"]
    ↓
output/analysis_YYYYMMDD_HHMMSS.md 저장
```

### Context Dictionary

모든 에이전트가 공유하는 누적 딕셔너리:

```python
context = {
    "input_document": str,
    "profile_context": Dict,      # user_profile DB → 팀 프로필 자동 주입
    "history_context": List[Dict],# 최근 3개 분석 요약 → 일관성 유지용
    "planner": {...},
    "developer": {...},
    "impact_analyzer": {...},
    "reviewer": {...},
    "quality_checker": {...},
    "documenter": {"markdown": "..."},
    "output_file": str
}
```

`profile_context`와 `history_context`는 `orchestrator.py`에서 분석 시작 시 DB에서 자동 로드되어 모든 에이전트 프롬프트에 주입됨.

### 나만의 AI 비서 (3-Layer 학습)

```
Layer 1 - 팀 프로필: /admin → AI 비서 설정 탭 → 팀명/기술스택/스타일 저장
                     → user_profile 테이블 → build_profile_section() → 모든 에이전트 프롬프트에 주입

Layer 2 - 원클릭 학습: 분석 결과 → "이 분석 기억하기" 버튼
                       → POST /api/analyses/{job_id}/save-example
                       → training_examples 테이블 → 다음 분석부터 Few-shot으로 주입

Layer 3 - 이전 분석 참조: 분석 시작 시 get_recent_context_analyses(limit=3) 자동 호출
                          → 최근 3개 분석 요약을 history_context로 주입
```

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `orchestrator.py` | 에이전트 파이프라인 조율, 품질 검사 루프, profile/history 주입 |
| `app.py` | FastAPI 웹서버, SSE 스트림, job_contexts 메모리 저장 |
| `database.py` | SQLite (`data/analysis_history.db`), 4개 테이블 |
| `utils/context_builder.py` | `KOREAN_INSTRUCTION`, `build_profile_section()`, `build_history_section()` |
| `utils/llm_client.py` | Ollama용 클라이언트, `_korean_system_prompt()` 자동 주입 |
| `utils/claude_client.py` | Claude API 클라이언트, JSON 파싱, mock 모드 |
| `agents/source_comparator.py` | 실제 소스코드 ZIP vs 분석 결과 비교 |
| `agents/chat_agent.py` | 분석 후 채팅 정제, 변경 요청 시 ImpactAnalyzer 재실행 |

### DB 테이블 (database.py)

| 테이블 | 역할 |
|--------|------|
| `analyses` | 분석 이력 (job_id, status, output_file 등) |
| `user_profile` | 팀 프로필 (key-value, 예: company_name, tech_stack) |
| `training_examples` | Few-shot 학습 예시 (input_text, output_markdown, quality_score) |
| `projects` | 업로드된 소스코드 프로젝트 저장 |

---

## 중요 규칙

### 한국어 강제 — 모든 에이전트 + Orchestrator에 반드시 적용

Ollama(qwen2.5:7b) 기본 언어가 중국어이므로 이중 보호가 필수:

```python
# 1. user_prompt 맨 앞에 KOREAN_INSTRUCTION 추가
from utils.context_builder import KOREAN_INSTRUCTION

prompt = f"{KOREAN_INSTRUCTION}\n\n... 실제 프롬프트 ..."

# 2. system_prompt에 한국어 명시
system_prompt="You are a ... agent. Always respond in Korean only."
```

`LLMClient`는 `_korean_system_prompt()`로 system_prompt에 자동 추가하지만, `ClaudeClient`는 자동 추가 없음 → user_prompt의 `KOREAN_INSTRUCTION`이 유일한 보호막.

**주의**: `orchestrator.py`의 `select_agents()` 프롬프트에도 반드시 `KOREAN_INSTRUCTION` 포함 필요. 에이전트뿐 아니라 Orchestrator 자체도 LLM을 호출하므로 동일 규칙 적용.

새 에이전트 추가 시 두 가지 모두 빠뜨리면 중국어 출력 발생.

### 피드백 기반 재실행

```python
# QualityChecker가 낮은 점수 에이전트 지정 → orchestrator가 feedback과 함께 재실행
context = agent.run(context, feedback=feedback)  # feedback 파라미터 필수
```

### JSON 파싱 안정성

`claude_client.py`의 `_parse_json_safely()`가 마크다운 fence, 내장 JSON 등을 자동 처리. Claude가 예상치 못한 형식으로 반환하면 이 메서드에 폴백 패턴 추가.

### qwen2.5:7b LLM 응답 형태 방어 처리

qwen2.5:7b는 스키마를 무시하고 예상치 못한 형태로 반환할 수 있음. 특히 `quality_checker`의 `agent_scores`:

```python
# LLM이 아래처럼 list로 반환할 수 있음 (예상: dict)
# "agent_scores": {"planner": [90, "피드백"]}  ← list
# "agent_scores": {"planner": {"score": 90, "feedback": "피드백"}}  ← 정상 dict

# 방어 처리 패턴
agent_scores = qc.get("agent_scores", {})
if not isinstance(agent_scores, dict):
    agent_scores = {}

score_data = agent_scores.get(agent_name, {})
if not isinstance(score_data, dict):
    score_data = {}
agent_score = score_data.get("score", 0)
```

`orchestrator.py`의 `_emit_agent_scores()`, `_emit_retry_feedback()`, retry 루프 feedback 추출 모두 이 방어 처리 적용되어 있음.

### DocumenterAgent 템플릿

`agents/documenter.py`의 템플릿(14~55줄)은 고정 8섹션 구조. 섹션 수정 시 템플릿 상수와 프롬프트 모두 업데이트.

---

## 새 에이전트 추가 패턴

```python
# agents/new_agent.py
from utils.context_builder import KOREAN_INSTRUCTION

class NewAgent:
    name = "new_agent"

    def run(self, context, feedback="", examples=None):
        examples_section = ""
        if examples:
            examples_section = "\n\n[참고 예시]\n" + ...

        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "... 프롬프트 ..."
            f"{examples_section}"
            + (f"\n\n[피드백]\n{feedback}" if feedback else "")
        )
        result = self.client.request_json(
            system_prompt="You are a ... agent. Always respond in Korean only.",
            user_prompt=prompt,
        )
        context[self.name] = result
        return context
```

그 다음 `orchestrator.py`에 에이전트 등록, `utils/claude_client.py` mock 응답에 케이스 추가.

---

## Docker 배포

```bash
# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f app

# 컨테이너 상태
docker-compose ps
```

**주요 설정** (`.env.offline` → docker-compose에서 사용):
- `LLM_MODE=local`, `LLM_BASE_URL=http://ollama:11434/v1`, `LLM_MODEL=qwen2.5:7b`
- `DATABASE_PATH=data/analysis_history.db` (볼륨: `./data:/app/data`)

**Ollama 헬스 체크**: 첫 실행 시 모델 다운로드(5-20분)로 unhealthy 표시됨. `start_period: 300s`로 설정되어 있어 정상 — 기다리면 됨.

**Windows 배포**: `scripts/build-exe.ps1`로 `AIAnalyzer.exe` 빌드. exe 실행 시 Docker 확인 → `docker-compose up -d --build` → 브라우저 자동 오픈.

---

## API 엔드포인트 (주요)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/analyze` | 분석 시작 (파일/텍스트) |
| GET | `/api/stream/{job_id}` | SSE 실시간 진행상황 |
| POST | `/api/chat/{job_id}` | 분석 후 채팅 정제 |
| POST | `/api/analyses/{job_id}/save-example` | 분석 결과 학습 예시로 저장 |
| GET/POST | `/api/profile` | 팀 프로필 조회/저장 |
| GET/POST/DELETE/PUT | `/api/training/examples` | 학습 예시 CRUD |
| GET | `/api/download/{filename}/{format}` | 결과 내보내기 (md/html/pdf/docx/json) |
