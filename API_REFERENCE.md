# 📚 API 참고 문서

## 목차
1. [개요](#개요)
2. [인증](#인증)
3. [엔드포인트](#엔드포인트)
4. [요청 형식](#요청-형식)
5. [응답 형식](#응답-형식)
6. [에러 처리](#에러-처리)
7. [코드 예제](#코드-예제)
8. [레이트 제한](#레이트-제한)

---

## 개요

### 기본 정보

```
Base URL: http://localhost:8000
Version: 1.0
Protocol: REST + SSE (Server-Sent Events)
```

### 지원 형식

```
요청: application/json, multipart/form-data
응답: application/json, text/event-stream, text/markdown
```

---

## 인증

현재 버전에서는 인증이 필요하지 않습니다.

향후 업데이트에서 API 토큰 기반 인증이 추가될 예정입니다:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

---

## 엔드포인트

### 1. 분석 요청

#### `POST /api/analyze`

새로운 분석 작업을 시작합니다.

**요청 방식 A: 텍스트 입력**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=게시판에 파일 첨부 기능을 추가해야 합니다"
```

**요청 방식 B: 파일 업로드**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@requirements.txt"
```

**요청 방식 C: 혼합 (파일 + 추가 텍스트)**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@requirements.txt" \
  -F "text=추가 요청사항"
```

**요청 매개변수**:

| 매개변수 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `text` | string | 선택 | 텍스트 입력 (최대 10,000자) |
| `file` | file | 선택 | 파일 업로드 (txt, md, pdf, xlsx, pptx) |

**요청 제약**:
- `text` 또는 `file` 중 최소 하나는 필수
- 파일 크기: 최대 50MB
- 동시 요청: 최대 3개

**응답**:

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "analysis_id": "analysis_20260404_102530",
  "status": "running",
  "queue": {
    "position": 1,
    "total_in_queue": 2
  }
}
```

**응답 설명**:

| 필드 | 타입 | 설명 |
|------|------|------|
| `job_id` | string (UUID) | 작업 고유 ID (스트림 수신 시 필요) |
| `analysis_id` | string | 분석 결과 ID (결과 조회 시 필요) |
| `status` | string | 작업 상태: `running`, `completed`, `failed` |
| `queue.position` | integer | 현재 큐 위치 (1부터 시작) |
| `queue.total_in_queue` | integer | 큐에 있는 총 작업 수 |

**상태 코드**:

| 상태 | 설명 |
|------|------|
| `200` | 요청 성공, 작업 생성됨 |
| `400` | 잘못된 요청 (text와 file 모두 없음, 파일 형식 오류 등) |
| `413` | 파일 크기 초과 (50MB 이상) |
| `503` | 서버 과부하 (동시 작업 초과) |

---

### 2. 실시간 진행 상황 스트림

#### `GET /api/stream/{job_id}`

분석 진행 상황을 실시간으로 수신합니다 (Server-Sent Events).

**요청**:

```bash
curl -N http://localhost:8000/api/stream/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**응답** (스트림):

```
data: {"event": "analyzing", "agent": "planner", "message": "요구사항 분석 중..."}

data: {"event": "agent_complete", "agent": "planner", "progress": 25}

data: {"event": "analyzing", "agent": "developer", "message": "기술 설계 중..."}

data: {"event": "agent_complete", "agent": "developer", "progress": 50}

data: {"event": "analyzing", "agent": "reviewer", "message": "리스크 검토 중..."}

data: {"event": "agent_complete", "agent": "reviewer", "progress": 75}

data: {"event": "analyzing", "agent": "documenter", "message": "마크다운 문서 생성 중..."}

data: {"event": "complete", "analysis_id": "analysis_20260404_102530", "output_file": "analysis_20260404_102530.md", "progress": 100}
```

**이벤트 타입**:

| 이벤트 | 필드 | 설명 |
|--------|------|------|
| `analyzing` | `agent`, `message` | 에이전트 실행 중 |
| `agent_complete` | `agent`, `progress` | 에이전트 완료 |
| `complete` | `analysis_id`, `output_file`, `progress` | 전체 분석 완료 |
| `error` | `message`, `error_code` | 오류 발생 |

**JavaScript 클라이언트 예제**:

```javascript
const eventSource = new EventSource(`/api/stream/${jobId}`);

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.event) {
    case 'analyzing':
      console.log(`${data.agent}: ${data.message}`);
      break;
    case 'agent_complete':
      updateProgressBar(data.progress);
      break;
    case 'complete':
      console.log('분석 완료:', data.output_file);
      eventSource.close();
      break;
    case 'error':
      console.error('오류:', data.message);
      eventSource.close();
      break;
  }
});

eventSource.addEventListener('error', (event) => {
  console.error('연결 오류:', event);
  eventSource.close();
});
```

**타임아웃**:
- 연결 유지: 30분 (ANALYSIS_TIMEOUT_MINUTES)
- 초과 시: 연결 종료, `error` 이벤트 발생

---

### 3. 분석 결과 다운로드

#### `GET /api/download/{filename}`

마크다운 형식으로 다운로드합니다.

**요청**:

```bash
curl -O http://localhost:8000/api/download/analysis_20260404_102530.md
```

**응답**:
- Content-Type: `text/markdown`
- 파일명: `analysis_20260404_102530.md`

**상태 코드**:

| 상태 | 설명 |
|------|------|
| `200` | 다운로드 성공 |
| `404` | 파일 없음 |

---

#### `GET /api/download/{filename}/pdf`

PDF 형식으로 다운로드합니다.

**요청**:

```bash
curl -O http://localhost:8000/api/download/analysis_20260404_102530/pdf
```

**응답**:
- Content-Type: `application/pdf`
- 파일명: `analysis_20260404_102530.pdf`

**변환 과정**:
```
Markdown → HTML (마크다운 렌더러) → PDF (WeasyPrint)
```

**변환 시간**: 5-10초

---

#### `GET /api/download/{filename}/docx`

Word 형식으로 다운로드합니다.

**요청**:

```bash
curl -O http://localhost:8000/api/download/analysis_20260404_102530/docx
```

**응답**:
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- 파일명: `analysis_20260404_102530.docx`

**변환 과정**:
```
Markdown → Word (python-docx)
```

---

#### `GET /api/download/{filename}/json`

JSON 형식으로 다운로드합니다.

**요청**:

```bash
curl -O http://localhost:8000/api/download/analysis_20260404_102530/json
```

**응답**:
```json
{
  "analysis_id": "analysis_20260404_102530",
  "created_at": "2026-04-04T10:25:30",
  "input": {
    "text": "게시판에 파일 첨부 기능 추가",
    "file_name": null
  },
  "planner": {
    "core_requirements": "...",
    "functional_requirements": [...],
    "non_functional_requirements": [...]
  },
  "developer": {
    "technical_spec": "...",
    "db_changes": "...",
    "impacted_modules": [...]
  },
  "reviewer": {
    "security_risks": [...],
    "performance_risks": [...]
  },
  "documenter": {
    "markdown": "..."
  }
}
```

---

### 4. 분석 이력 조회

#### `GET /api/history`

분석 이력을 페이지네이션으로 조회합니다.

**요청**:

```bash
# 기본 (첫 20개)
curl http://localhost:8000/api/history

# 페이지네이션
curl http://localhost:8000/api/history?limit=20&offset=40

# 상태 필터
curl http://localhost:8000/api/history?status=completed
```

**쿼리 매개변수**:

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | integer | 20 | 한 페이지 결과 수 (최대 100) |
| `offset` | integer | 0 | 스킵할 항목 수 |
| `status` | string | (없음) | 필터: `completed`, `running`, `failed` |

**응답**:

```json
{
  "analyses": [
    {
      "id": 1,
      "analysis_id": "analysis_20260404_102530",
      "input_file_name": "requirements.txt",
      "input_text": "게시판에 파일 첨부 기능을 추가해야 합니다...",
      "file_size": 2048,
      "output_file": "analysis_20260404_102530.md",
      "status": "completed",
      "agents_used": ["planner", "developer", "reviewer", "documenter"],
      "created_at": "2026-04-04T10:25:30",
      "completed_at": "2026-04-04T10:26:15",
      "duration_seconds": 45
    },
    ...
  ],
  "total_count": 142,
  "limit": 20,
  "offset": 0,
  "page": 1,
  "total_pages": 8
}
```

**응답 필드**:

| 필드 | 타입 | 설명 |
|------|------|------|
| `analyses` | array | 분석 결과 배열 |
| `total_count` | integer | 전체 분석 수 |
| `page` | integer | 현재 페이지 번호 |
| `total_pages` | integer | 전체 페이지 수 |

---

### 5. 헬스 체크

#### `GET /api/health`

서버 상태를 확인합니다.

**요청**:

```bash
curl http://localhost:8000/api/health
```

**응답**:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-04T10:30:00",
  "version": "1.0.0",
  "queue": {
    "size": 2,
    "running": 1,
    "max_concurrent": 3
  },
  "database": {
    "status": "connected",
    "analyses_count": 142,
    "storage_mb": 45.3
  },
  "api": {
    "model": "claude-sonnet-4-5",
    "status": "connected"
  }
}
```

**상태 코드**:

| 상태 | 의미 |
|------|------|
| `200` | 정상 작동 중 |
| `503` | 서비스 일시 중단 (DB 연결 실패 등) |

---

## 요청 형식

### Content-Type별 요청

#### 1. JSON 요청

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "게시판 시스템 개선",
    "mock": false
  }'
```

#### 2. Form Data 요청

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=게시판 시스템 개선"
```

#### 3. Multipart 요청 (파일)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/file.txt"
```

---

## 응답 형식

### 성공 응답

```json
{
  "job_id": "uuid",
  "status": "running",
  "message": "분석이 시작되었습니다"
}
```

### 에러 응답

```json
{
  "error": true,
  "code": "INVALID_REQUEST",
  "message": "text 또는 file이 필요합니다",
  "details": {
    "provided": [],
    "required": ["text", "file"]
  }
}
```

---

## 에러 처리

### 에러 코드

| 코드 | HTTP | 설명 | 해결 방법 |
|------|------|------|---------|
| `INVALID_REQUEST` | 400 | 요청 형식 오류 | 요청 매개변수 확인 |
| `FILE_TOO_LARGE` | 413 | 파일 크기 초과 | 50MB 이하 파일 사용 |
| `UNSUPPORTED_FORMAT` | 400 | 지원하지 않는 파일 형식 | txt, md, pdf, xlsx, pptx만 허용 |
| `QUEUE_FULL` | 503 | 작업 큐 초과 | 나중에 재시도 |
| `ANALYSIS_TIMEOUT` | 504 | 분석 시간 초과 | 더 작은 입력으로 재시도 |
| `DATABASE_ERROR` | 500 | 데이터베이스 오류 | 관리자 연락 |
| `API_ERROR` | 502 | Claude API 오류 | API 상태 확인 후 재시도 |

### 에러 응답 예제

```json
{
  "error": true,
  "code": "FILE_TOO_LARGE",
  "message": "파일 크기가 50MB를 초과했습니다",
  "details": {
    "max_size_mb": 50,
    "provided_size_mb": 120,
    "file_name": "large_document.pdf"
  }
}
```

### 재시도 전략

```python
import time
import requests

def call_api_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # 서버 과부하, 재시도
                wait_time = 2 ** attempt  # 2초, 4초, 8초
                print(f"재시도 대기 중... ({wait_time}초)")
                time.sleep(wait_time)
            else:
                # 다른 에러, 즉시 실패
                raise Exception(response.json()["message"])
        except requests.RequestException as e:
            print(f"네트워크 오류: {e}")
            time.sleep(2 ** attempt)
    
    raise Exception("재시도 실패")
```

---

## 코드 예제

### Python

#### 기본 분석 요청

```python
import requests

url = "http://localhost:8000/api/analyze"

# 방법 1: 텍스트 입력
response = requests.post(
    url,
    data={"text": "게시판에 파일 첨부 기능 추가"}
)
data = response.json()
job_id = data["job_id"]
print(f"작업 ID: {job_id}")

# 방법 2: 파일 업로드
with open("requirements.txt", "rb") as f:
    response = requests.post(
        url,
        files={"file": f}
    )
    data = response.json()
    job_id = data["job_id"]
```

#### SSE 스트림 수신

```python
import sseclient
import json

job_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
url = f"http://localhost:8000/api/stream/{job_id}"

response = requests.get(url, stream=True)
client = sseclient.SSEClient(response)

for event in client:
    if event.data:
        data = json.loads(event.data)
        print(f"[{data.get('agent', 'system')}] {data.get('message', '')}")
        
        if data.get('event') == 'complete':
            print(f"완료: {data['output_file']}")
            break
```

#### 결과 다운로드

```python
import requests

# 마크다운 다운로드
response = requests.get(
    "http://localhost:8000/api/download/analysis_20260404_102530.md"
)
with open("result.md", "wb") as f:
    f.write(response.content)

# PDF 다운로드
response = requests.get(
    "http://localhost:8000/api/download/analysis_20260404_102530/pdf"
)
with open("result.pdf", "wb") as f:
    f.write(response.content)
```

---

### JavaScript

#### 기본 분석 요청

```javascript
const analyzeButton = document.getElementById('analyze-btn');

analyzeButton.addEventListener('click', async () => {
  const formData = new FormData();
  const fileInput = document.getElementById('file-input');
  
  if (fileInput.files.length > 0) {
    formData.append('file', fileInput.files[0]);
  } else {
    const text = document.getElementById('text-input').value;
    formData.append('text', text);
  }
  
  const response = await fetch('http://localhost:8000/api/analyze', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  const jobId = data.job_id;
  console.log('작업 ID:', jobId);
  
  // SSE 스트림 시작
  streamAnalysis(jobId);
});
```

#### SSE 스트림 수신

```javascript
function streamAnalysis(jobId) {
  const eventSource = new EventSource(`/api/stream/${jobId}`);
  
  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.event) {
      case 'analyzing':
        updateUI(`분석 중: ${data.agent}`);
        break;
      case 'agent_complete':
        updateProgress(data.progress);
        break;
      case 'complete':
        console.log('분석 완료:', data.output_file);
        showDownloadButtons(data.analysis_id);
        eventSource.close();
        break;
      case 'error':
        showError(data.message);
        eventSource.close();
        break;
    }
  });
  
  eventSource.addEventListener('error', (event) => {
    console.error('연결 오류:', event);
    eventSource.close();
  });
}
```

#### 다운로드

```javascript
function downloadResult(filename, format) {
  const url = `/api/download/${filename}/${format || ''}`;
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
}

// 사용
downloadResult('analysis_20260404_102530.md', 'md');    // Markdown
downloadResult('analysis_20260404_102530', 'pdf');      // PDF
downloadResult('analysis_20260404_102530', 'docx');     // Word
downloadResult('analysis_20260404_102530', 'json');     // JSON
```

---

### cURL

#### 전체 워크플로우

```bash
#!/bin/bash

# 1. 분석 요청
echo "분석 요청 중..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/analyze \
  -F "file=@requirements.txt")

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "작업 ID: $JOB_ID"

# 2. SSE 스트림 모니터링
echo "분석 진행 중..."
curl -N http://localhost:8000/api/stream/$JOB_ID | while IFS= read -r line; do
  echo $line | sed 's/^data: //'
done

# 3. 결과 다운로드
echo "결과 다운로드..."
curl -O http://localhost:8000/api/download/analysis_latest.md
curl -O http://localhost:8000/api/download/analysis_latest/pdf

echo "완료!"
```

---

## 레이트 제한

### 제한 정책

| 항목 | 제한 |
|------|------|
| 동시 분석 | 3개 |
| 요청당 파일 크기 | 50MB |
| 분석 타임아웃 | 30분 |
| 이력 조회 페이지 크기 | 최대 100 |

### 초과 시 동작

```json
{
  "error": true,
  "code": "QUEUE_FULL",
  "message": "대기열이 가득 찼습니다. 나중에 다시 시도해주세요.",
  "queue": {
    "position": 10,
    "total_in_queue": 3,
    "wait_time_estimate": 180
  }
}
```

---

## 버전 관리

### 현재 버전: 1.0

### 향후 변경 예정

**1.1 버전 (예정)**
- API 토큰 인증 추가
- 웹훅 지원
- 분석 취소 기능
- 배치 분석 지원

**1.2 버전 (예정)**
- 실시간 협업 편집
- 버전 관리
- 분석 비교

### 하위 호환성

- `v1.0`의 모든 엔드포인트는 이후 버전에서도 유지됩니다.
- 새로운 필드는 항상 선택사항입니다 (기존 코드 호환성 보장).

---

<div align="center">

**📞 지원**:  
[GitHub Issues](https://github.com/sungsik-lee/ai-agent/issues) · [사용자 가이드](USER_GUIDE.md)

Made with ❤️ for developers

</div>
