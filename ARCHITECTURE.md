# 🏗️ 아키텍처 상세 설명서

## 목차
1. [시스템 개요](#시스템-개요)
2. [오케스트레이터 패턴](#오케스트레이터-패턴)
3. [에이전트 설계](#에이전트-설계)
4. [데이터 흐름](#데이터-흐름)
5. [핵심 모듈](#핵심-모듈)
6. [웹 서버 아키텍처](#웹-서버-아키텍처)
7. [데이터베이스 설계](#데이터베이스-설계)
8. [확장성 및 성능](#확장성-및-성능)

---

## 시스템 개요

**AI 개발 분석서 자동 생성 시스템**은 비즈니스 요구사항을 입력받아 전문적인 개발 분석 문서를 생성하는 멀티-에이전트 AI 시스템입니다.

### 주요 특징
- **멀티-에이전트 협업**: 4개의 특화된 AI 에이전트가 순차적으로 협력
- **구조화된 출력**: 고정된 8섹션 템플릿으로 일관성 있는 문서 생성
- **다양한 입력 형식**: 텍스트, PDF, Excel, PowerPoint 모두 지원
- **실시간 모니터링**: SSE(Server-Sent Events)로 분석 진행 상황 실시간 표시
- **여러 내보내기 형식**: Markdown, HTML, PDF, Word, JSON

---

## 오케스트레이터 패턴

### 설계 철학

```
입력 분석 → 에이전트 선택 → 순차 실행 (context 누적) → 최종 문서 생성
```

**Orchestrator** (`orchestrator.py`)는 중앙 조율자로서:

1. **입력 분석 및 라우팅**
   - 입력 문서의 유형 파악 (텍스트 / 파일 경로)
   - 필요한 에이전트 자동 선택 (Claude 사용)
   ```python
   selected_agents = self.select_agents(input_document)
   # 반환값: {selected_agents: [...], reason: "..."}
   ```

2. **순차적 에이전트 실행**
   ```python
   context = {
       "input_document": input_text,
       "selected_agents": [...]
   }
   
   for agent_class in [PlannerAgent, DeveloperAgent, ReviewerAgent, DocumenterAgent]:
       if agent should run:
           context = agent.run(context)
   ```

3. **DocumenterAgent는 항상 마지막에 실행**
   - 앞의 3개 에이전트 결과를 모두 받아 최종 마크다운 생성
   - 고정된 8섹션 템플릿 사용으로 일관성 보장

### 컨텍스트 누적 패턴

모든 에이전트는 동일한 계약을 따릅니다:

```python
def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # 1. 필요한 데이터 추출
    upstream_data = context.get("upstream_agent_name", {})
    
    # 2. Claude API 호출하여 처리
    result = self.client.request_json(
        system_prompt=self.system_prompt,
        user_prompt=f"{upstream_data}\n{processing_instructions}"
    )
    
    # 3. 결과를 context에 누적
    context[self.agent_name] = result
    
    # 4. 다음 에이전트를 위해 context 반환
    return context
```

**장점**:
- ✅ 전역 상태 제거 → 테스트 용이
- ✅ 에이전트 간 느슨한 결합 → 독립적 수정 가능
- ✅ 디버깅 시 특정 단계의 입력/출력 명확
- ✅ 병렬 실행 가능성 열려 있음

---

## 에이전트 설계

### 1. PlannerAgent (기획자)

**목적**: 원본 요구사항에서 핵심 정보 추출 및 분류

**입력**:
```
context["input_document"] = "사용자가 제시한 요구사항 문서"
```

**처리 과정**:
1. 핵심 요구사항 (core_requirements) 추출
2. 기능 요구사항 (functional_requirements) 나열
3. 비기능 요구사항 (non_functional_requirements) 식별
4. 모호한 부분 (ambiguities) 지적
5. 명확화가 필요한 질문 (clarification_questions) 작성

**출력**:
```json
{
  "core_requirements": "...",
  "functional_requirements": ["요구사항1", "요구사항2", ...],
  "non_functional_requirements": ["성능", "보안", ...],
  "ambiguities": ["부분1", "부분2"],
  "clarification_questions": ["질문1", "질문2"]
}
```

**저장 위치**: `context["planner"]`

---

### 2. DeveloperAgent (개발자)

**목적**: PlannerAgent의 결과를 기반으로 기술 사양서 작성

**입력**:
```
context["planner"] = PlannerAgent의 분석 결과
```

**처리 과정**:
1. 기술 스택 확인 (Java/JSP/jQuery/MyBatis)
2. 기술 설계 (technical_spec) 작성
   - 새로운 클래스/메서드 목록
   - DB 스키마 변경사항
   - 영향을 받는 모듈
3. DB 변경사항 (db_changes) 상세 기술
4. 영향도 분석 (impacted_modules) 
5. 개발 노력도 (effort) 산정

**출력**:
```json
{
  "technical_spec": "...",
  "db_changes": "ALTER TABLE ...",
  "impacted_modules": ["Module A", "Module B"],
  "effort": "일 5명, 2주"
}
```

**저장 위치**: `context["developer"]`

---

### 3. ReviewerAgent (검토자)

**목적**: 기획과 개발 사항을 교차 검토하여 리스크 도출

**입력**:
```
context["planner"] + context["developer"]
```

**처리 과정**:
1. 기획과 개발의 일관성 검토 (cross_review)
2. 누락된 예외사항 (missing_exceptions) 식별
3. 보안 리스크 (security_risks) 분석
4. 성능 리스크 (performance_risks) 분석
5. 일정 리스크 (schedule_risks) 검토

**출력**:
```json
{
  "cross_review": "...",
  "missing_exceptions": ["예외1", "예외2"],
  "security_risks": ["SQL Injection 가능성", "..."],
  "performance_risks": ["쿼리 최적화 필요", "..."],
  "schedule_risks": ["일정 단축 불가", "..."]
}
```

**저장 위치**: `context["reviewer"]`

---

### 4. DocumenterAgent (문서화 담당자)

**목적**: 모든 분석 결과를 마크다운 문서로 통합

**입력**:
```
전체 context 딕셔너리
= input_document + planner + developer + reviewer
```

**처리 과정**:
1. **고정 템플릿** (14-55줄, documenter.py)에 값 채우기
   ```
   # 1. 개요 (Executive Summary)
   # 2. 요구사항 분석
   # 3. 기술 설계
   # 4. 데이터베이스 변경
   # 5. 기술적 리스크 및 대응 방안
   # 6. 개발 계획
   # 7. 테스트 전략
   # 8. 부록
   ```

2. 각 섹션을 context의 관련 데이터로 채우기
3. 마크다운 포매팅 적용

**출력**:
```
context["documenter"] = {
  "markdown": "# 개발 분석서\n\n## 1. 개요\n...",
  "output_file": "output/analysis_YYYYMMDD_HHMMSS.md"
}
```

**저장 위치**: `context["documenter"]`

**핵심 원칙**:
- 템플릿은 고정 → 모든 문서가 동일한 8섹션 구조
- 각 섹션의 제목과 순서는 변경되지 않음
- 에이전트는 템플릿을 재구성하지 않고, 값만 채움

---

## 데이터 흐름

### CLI 모드 (main.py)

```
사용자 입력
    ↓
main.py:
  - 입력 유형 판단 (텍스트 or 파일)
  - 파일일 경우 읽기
    ↓
Orchestrator.__init__:
  - output/ 디렉토리 생성
  - ClaudeClient 초기화 (API 키 / mock 모드 설정)
    ↓
Orchestrator.select_agents():
  - Claude에 입력 문서 분석 요청
  - 필요한 에이전트 목록 반환
    ↓
Orchestrator.run():
  - context = {"input_document": "..."}
  - for each selected agent:
      context = agent.run(context)
  - DocumenterAgent는 항상 마지막에 실행
    ↓
최종 결과:
  - output/analysis_YYYYMMDD_HHMMSS.md 저장
  - 터미널에 출력
```

### 웹 서버 모드 (app.py)

```
클라이언트
    ↓
POST /api/analyze (파일 or 텍스트)
    ↓
app.py:
  - 요청 검증
  - 파일 처리 (PDF/Excel/PowerPoint → 텍스트 추출)
  - job_id 생성 (UUID)
  - 분석 작업을 큐에 추가
  - job_id 반환
    ↓
클라이언트: GET /api/stream/{job_id} (SSE)
    ↓
백그라운드 작업:
  - Orchestrator.run() 실행
  - 각 에이전트 완료 시마다 SSE 메시지 전송
  - 최종 결과를 DB에 저장
    ↓
클라이언트:
  - SSE 스트림에서 진행 상황 수신
  - 분석 완료 시 결과 다운로드 버튼 활성화
  - GET /api/download/{filename} 또는 GET /api/download/{filename}/pdf
```

---

## 핵심 모듈

### utils/claude_client.py

**역할**: Claude API와의 모든 상호작용을 담당

**주요 메서드**:

#### 1. `request_json(system_prompt, user_prompt, max_retries=3)`

구조화된 JSON 응답을 요청하며, 파싱 실패 시 자동으로 재시도합니다.

```python
result = client.request_json(
    system_prompt="JSON 형식으로 응답해주세요: {...}",
    user_prompt="사용자 요청",
    max_retries=3
)
```

**파싱 전략** (`_parse_json_safely()`):
1. 직접 JSON 파싱 시도
2. ``````` ``` ````` 마크다운 펜스 제거 후 파싱
3. 첫 번째 `{...}` 부분문자열 추출
4. 아무것도 작동하지 않으면 Claude가 JSON 수정

**재시도 전략**:
- 지수 백오프: `1.5 * attempt_number` 초 대기
- 최대 3회 재시도
- 최종 실패 시 오류 발생

#### 2. `request_text(system_prompt, user_prompt, max_retries=3)`

구조화되지 않은 텍스트 응답을 요청합니다 (DocumenterAgent에서 사용).

```python
markdown = client.request_text(
    system_prompt="마크다운으로 작성...",
    user_prompt="컨텍스트: {...}"
)
```

#### 3. 모의 모드 (`mock=True`)

API 없이 테스트하기 위해 하드코딩된 응답을 반환합니다.

```python
client = ClaudeClient(api_key="dummy", mock=True)
# 모의 응답은 실제 응답과 동일한 스키마 구조
```

**모의 모드 동작**:
- API 호출하지 않음
- 각 에이전트별 하드코딩된 응답 반환
- 응답 시간: 1-3초 (네트워크 지연 없음)
- 오케스트레이션 로직과 UI 테스트에 유용

---

### agents/

각 에이전트는 동일한 기본 구조를 따릅니다:

```python
class AgentName:
    def __init__(self, client: ClaudeClient):
        self.client = client
        self.agent_name = "agent_name"
        self.system_prompt = """..."""
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # 처리 로직
        result = self.client.request_json(...)
        context[self.agent_name] = result
        return context
```

**각 에이전트의 역할**:

| 파일 | 클래스 | 목적 |
|------|--------|------|
| `planner.py` | `PlannerAgent` | 요구사항 분석 |
| `developer.py` | `DeveloperAgent` | 기술 설계 |
| `reviewer.py` | `ReviewerAgent` | 리스크 검토 |
| `documenter.py` | `DocumenterAgent` | 최종 문서 생성 |

---

## 웹 서버 아키텍처

### FastAPI 애플리케이션 (app.py)

```
FastAPI App
├── 정적 파일 제공 (index.html, admin.html)
├── REST API 엔드포인트
├── SSE 스트림 핸들러
└── 백그라운드 작업 관리
```

### 핵심 엔드포인트

#### 1. `POST /api/analyze`

**용도**: 새로운 분석 작업 시작

**요청**:
```
Content-Type: multipart/form-data

text: "텍스트 입력" 또는
file: <파일>
```

**응답**:
```json
{
  "job_id": "uuid-4",
  "analysis_id": "analysis_12345",
  "status": "running",
  "queue": {
    "position": 1,
    "total_in_queue": 2
  }
}
```

**처리 흐름**:
1. 요청 검증 (텍스트 또는 파일 중 하나)
2. 파일일 경우 텍스트 추출 (PDF/Excel/PowerPoint)
3. 작업 큐에 추가
4. 백그라운드 작업 시작

#### 2. `GET /api/stream/{job_id}`

**용도**: 분석 진행 상황을 실시간으로 수신 (SSE)

**응답** (스트림):
```
data: {"event": "analyzing", "agent": "planner", "message": "요구사항 분석 중..."}
data: {"event": "agent_complete", "agent": "planner"}
data: {"event": "analyzing", "agent": "developer", "message": "기술 설계 중..."}
data: {"event": "complete", "output_file": "analysis_20260404_102530.md"}
```

**클라이언트 측 JavaScript** (index.html):
```javascript
const eventSource = new EventSource(`/api/stream/${job_id}`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data);
};
```

#### 3. `GET /api/download/{filename}`

**용도**: 마크다운 다운로드

**응답**: 마크다운 파일 (text/markdown)

#### 4. `GET /api/download/{filename}/pdf`

**용도**: PDF 형식 다운로드

**변환 파이프라인**:
```
Markdown → HTML → PDF (WeasyPrint)
```

#### 5. `GET /api/history`

**용도**: 분석 이력 조회 (페이지네이션)

**쿼리 파라미터**:
```
?limit=20&offset=0
```

**응답**:
```json
{
  "analyses": [
    {
      "id": "analysis_12345",
      "input_text": "게시판에 파일...",
      "created_at": "2026-04-04T10:25:30",
      "status": "completed",
      "output_file": "analysis_20260404_102530.md",
      "file_size": 12345
    }
  ],
  "total_count": 45,
  "limit": 20,
  "offset": 0
}
```

#### 6. `GET /api/health`

**용도**: 헬스 체크

**응답**:
```json
{
  "status": "healthy",
  "queue_size": 2,
  "db_status": "connected"
}
```

---

### 백그라운드 작업 관리

**라우팅 및 큐잉**:
1. `/api/analyze` 요청 → job_id 생성 및 작업 큐에 추가
2. 별도 스레드에서 큐 모니터링
3. 동시 실행 제한: `MAX_CONCURRENT_ANALYSES = 3`
4. 각 작업 완료 시 DB 저장 및 SSE 브로드캐스트

**작업 상태 추적**:
```python
job = {
  "id": "uuid",
  "status": "running" | "completed" | "failed",
  "agent": "현재 진행 중인 에이전트",
  "progress": 25,  # 0-100%
  "created_at": datetime,
  "completed_at": datetime,
  "output_file": "파일명"
}
```

---

## 데이터베이스 설계

### SQLite (database.py)

**테이블: analyses**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER (PK) | 자동 증가 ID |
| `analysis_id` | TEXT | UUID 기반 분석 ID |
| `input_text` | TEXT | 사용자 입력 텍스트 (처음 500자) |
| `input_file_name` | TEXT | 업로드된 파일명 |
| `file_size` | INTEGER | 파일 크기 (bytes) |
| `output_file` | TEXT | 생성된 마크다운 파일명 |
| `status` | TEXT | 'running' / 'completed' / 'failed' |
| `agents_used` | TEXT | JSON 배열: ["planner", "developer", ...] |
| `created_at` | TIMESTAMP | 생성 시간 |
| `completed_at` | TIMESTAMP | 완료 시간 |
| `duration_seconds` | INTEGER | 처리 소요 시간 |

**쿼리 예제**:

```python
# 이력 조회 (페이지네이션)
analyses = db.get_analyses(limit=20, offset=0)

# 완료된 분석만
completed = db.get_analyses(status="completed")

# 통계
stats = {
  "total": db.count_analyses(),
  "completed": db.count_analyses(status="completed"),
  "failed": db.count_analyses(status="failed")
}
```

---

## 확장성 및 성능

### 성능 고려 사항

**1. 동시 실행 제한**
```python
MAX_CONCURRENT_ANALYSES = 3
```
- 동시에 최대 3개 분석만 실행
- API 레이트 제한 고려
- 메모리 효율성

**2. 타임아웃 설정**
```python
ANALYSIS_TIMEOUT_MINUTES = 30
```
- 30분 이상 응답 없으면 실패 처리
- 좀비 작업 방지

**3. 파일 크기 제한**
```python
MAX_FILE_SIZE_MB = 50
```
- 50MB 이상 파일 거부
- 텍스트 추출 시간 최소화

### 확장 가능성

**1. 새로운 에이전트 추가**
```python
class NewAgent:
    def run(self, context):
        result = self.client.request_json(...)
        context["new_agent"] = result
        return context

# orchestrator.py에 추가
if "new_agent" in selected_agents:
    context = NewAgent(self.client).run(context)
```

**2. 새로운 내보내기 형식**
```python
# utils/exporters.py
class ExportFormat:
    @staticmethod
    def to_format(markdown):
        # 변환 로직
        return result
```

**3. 새로운 입력 형식**
```python
# utils/file_processor.py에 추가
@staticmethod
def process_new_format(file_path):
    # 추출 로직
    return text
```

---

## 보안 고려 사항

### 1. API 키 관리
- `.env` 파일에 저장
- 환경 변수로 로드
- .gitignore에 .env 포함

### 2. 입력 검증
- 파일 크기 제한
- 파일 형식 검증
- 텍스트 길이 제한

### 3. 출력 보안
- 생성된 파일은 output/ 디렉토리에만 저장
- 파일명 sanitization
- CORS 설정

### 4. 데이터 보관 정책
```python
RETENTION_DAYS = 30  # 30일 후 자동 삭제
```

---

## 디버깅 및 로깅

### 로깅 전략 (utils/logger.py)

```python
import logging

logger = logging.getLogger("analysis")
logger.info(f"에이전트 시작: {agent_name}")
logger.error(f"에러 발생: {error_message}")
```

### 모니터링 포인트

1. **API 호출 전/후**
   - 요청 매개변수 로깅
   - 응답 시간 기록
   - 재시도 횟수 추적

2. **에이전트 진행 상황**
   - 각 에이전트 시작/완료 시간
   - 중간 결과 (context 상태)

3. **웹 서버 요청**
   - HTTP 상태 코드
   - 응답 시간
   - 에러 스택 트레이스

---

<div align="center">

**📚 다음 단계**:  
[API 문서](API_REFERENCE.md) · [사용자 가이드](USER_GUIDE.md)

</div>
