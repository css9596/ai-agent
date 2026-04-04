# 📖 사용자 가이드

## 목차
1. [설치 및 설정](#설치-및-설정)
2. [CLI 사용 방법](#cli-사용-방법)
3. [웹 인터페이스 사용](#웹-인터페이스-사용)
4. [파일 업로드 및 형식](#파일-업로드-및-형식)
5. [결과 확인 및 다운로드](#결과-확인-및-다운로드)
6. [설정 및 커스터마이징](#설정-및-커스터마이징)
7. [자주 묻는 질문](#자주-묻는-질문)
8. [문제 해결](#문제-해결)

---

## 설치 및 설정

### 사전 요구사항

- **Python**: 3.9 이상
- **OS**: macOS, Linux, Windows
- **Anthropic API 키** (옵션: 모의 모드 또는 Ollama 사용 시 불필요)

### Step 1: 환경 준비

```bash
# 프로젝트 디렉토리로 이동
cd multi-agent

# 가상 환경 생성
python3 -m venv .venv

# 가상 환경 활성화
source .venv/bin/activate          # macOS/Linux
# 또는
.venv\Scripts\activate              # Windows
```

### Step 2: 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 패키지**:
- `anthropic` - Claude API 클라이언트
- `fastapi` - 웹 서버 프레임워크
- `uvicorn` - ASGI 서버
- `python-dotenv` - 환경 변수 관리
- `pydantic` - 데이터 검증
- `weasyprint` - PDF 생성
- `markdown` - 마크다운 처리
- `openpyxl` - Excel 파일 처리
- `PyPDF2` - PDF 텍스트 추출
- `python-pptx` - PowerPoint 파일 처리

### Step 3: API 키 설정

#### 방법 A: .env 파일 (권장)

```bash
# .env 파일 생성
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
EOF
```

[Anthropic Console](https://console.anthropic.com)에서 API 키 발급받기:
1. 계정 로그인
2. "API Keys" 메뉴로 이동
3. "Create Key" 클릭
4. 발급받은 키를 .env에 복사

#### 방법 B: 환경 변수 설정

```bash
# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Windows (CMD)
set ANTHROPIC_API_KEY=sk-ant-...
```

---

## CLI 사용 방법

### 기본 실행

#### 1️⃣ 텍스트 직접 입력

```bash
python main.py --input "게시판에 파일 첨부 기능을 추가해주세요"
```

**출력 예**:
```
[기획자] 분석 중...
요구사항 추출 완료: 4개 기능 요구사항, 2개 비기능 요구사항

[개발자] 분석 중...
기술 설계 완료: 3개 새로운 클래스, 2개 DB 테이블 수정

[검토자] 분석 중...
리스크 분석 완료: 1개 보안 리스크, 2개 성능 고려사항

[문서화 담당자] 분석 중...
마크다운 문서 생성 완료

결과: output/analysis_20260404_102530.md
```

#### 2️⃣ 파일 입력

```bash
# 텍스트 파일
python main.py --input "./requirements.txt"

# 마크다운 파일
python main.py --input "./specification.md"

# 절대 경로
python main.py --input "/Users/sungsik/Documents/request.txt"
```

#### 3️⃣ 모의 모드 (API 없이 테스트)

```bash
python main.py --mock --input "테스트 요구사항"
```

**장점**:
- API 키 없어도 실행
- 빠른 응답 (1-3초)
- UI/워크플로우 테스트에 유용

### 고급 옵션

#### 📝 긴 문서 처리

```bash
# 여러 줄 텍스트
python main.py --input "
게시판 시스템 개선 요청:

1. 파일 첨부 기능
   - jpg, png, pdf, xlsx 지원
   - 최대 파일 크기: 10MB
   - 최대 5개 첨부 가능

2. 성능 최적화
   - 조회 응답 시간 < 1초
   - 동시 접속자 10000명 지원

3. 보안 강화
   - CSRF 방지
   - XSS 필터링
"
```

#### 🔄 여러 요구사항 순차 처리

```bash
# 스크립트 작성
cat > batch_analyze.sh << 'EOF'
#!/bin/bash
for file in requirements_*.txt; do
  echo "Processing $file..."
  python main.py --input "./$file"
done
EOF

chmod +x batch_analyze.sh
./batch_analyze.sh
```

---

## 웹 인터페이스 사용

### 웹 서버 시작

```bash
# 터미널 1: 웹 서버 실행
python app.py
```

**예상 출력**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 브라우저에서 접속

```
http://localhost:8000
```

### 메인 페이지 (사용자)

#### 1. 파일 업로드

**방법 A: 파일 선택**
```
1. "파일 선택" 버튼 클릭
2. 원하는 파일 선택 (.txt, .pdf, .xlsx, .pptx, .md)
3. 파일이 미리보기에 표시됨
```

**방법 B: 드래그&드롭**
```
1. 업로드 영역에 파일 드래그
2. 파일을 드롭
3. 자동으로 미리보기 표시
```

#### 2. 텍스트 직접 입력

```
1. "또는 직접 입력" 텍스트 박스에 클릭
2. 요구사항 작성
3. 파일과 함께 사용 가능
```

#### 3. 분석 시작

```
1. "분석 시작" 버튼 클릭
2. 진행률 바가 표시됨 (실시간)
3. 각 에이전트 진행 상황 표시
   - 기획자: 30%
   - 개발자: 50%
   - 검토자: 70%
   - 문서화: 100%
```

#### 4. 결과 다운로드

분석 완료 후 5가지 형식으로 다운로드:
- 📄 **Markdown**: 원본 마크다운 (.md)
- 📋 **HTML**: 웹 페이지 형식 (.html)
- 📑 **PDF**: 인쇄 가능한 형식 (.pdf)
- 📝 **Word**: Office 형식 (.docx)
- 📦 **JSON**: 구조화된 데이터 (.json)

```
각 버튼에 마우스 호버 → 파일명 표시
클릭 → 다운로드 시작
```

### 관리자 대시보드 (`/admin`)

#### 접속 방법

```
http://localhost:8000/admin
```

#### 1. 통계 카드

```
┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐
│ 총 분석수   │ │ 완료된 수   │ │ 진행중   │ │ 실패한수 │
│    45       │ │    42       │ │   1      │ │   2      │
└─────────────┘ └─────────────┘ └──────────┘ └──────────┘
```

#### 2. 분석 이력 테이블

**컬럼 설명**:

| 컬럼 | 설명 |
|------|------|
| **입력** | 업로드된 파일명 또는 입력 텍스트 (50자 말줄임) |
| **크기** | 파일 크기 (KB/MB) |
| **상태** | 상태 배지 (완료/진행중/실패) |
| **생성일시** | 분석 요청 시간 |
| **소요시간** | 처리 소요 시간 (초) |
| **다운로드** | 결과 다운로드 아이콘 |

**페이지네이션**:
```
[이전] ◄  Page 1 / 3  ► [다음]
```

#### 3. 필터링 및 검색

```
상태 필터:
  [ ] 모든 상태
  [●] 완료
  [ ] 진행중
  [ ] 실패
```

#### 4. 성능 메트릭

```
├─ 성공률: 95.5% (42/44)
├─ 평균 소요 시간: 45초
└─ 동시 실행 중: 1/3
```

---

## 파일 업로드 및 형식

### 지원하는 파일 형식

#### 📄 텍스트 (.txt, .md)

```
파일 크기 제한: 50MB
지원 인코딩: UTF-8, EUC-KR
처리 속도: 빠름 (< 1초)

예제:
-- requirements.txt --
게시판에 파일 첨부 기능을 추가해야 합니다.
첨부 가능한 파일: 이미지(jpg, png), 문서(pdf, xlsx)
파일 크기 제한: 최대 10MB
```

#### 📊 Excel (.xlsx)

```
파일 크기 제한: 50MB
처리 방식: 모든 시트 읽기
출력: 텍스트로 변환 후 분석

예제:
+---------+------------------+
| 번호    | 요구사항         |
+---------+------------------+
| 1       | 파일 첨부 기능   |
| 2       | 성능 최적화      |
+---------+------------------+
```

#### 📄 PDF (.pdf)

```
파일 크기 제한: 50MB
처리 속도: 보통 (1-3초)
텍스트 추출 방식: PyPDF2 라이브러리
지원: 텍스트 기반 PDF (스캔 이미지 불가)

예제: 프로젝트 제안서.pdf (10MB)
  → 텍스트 추출
  → 분석 실행
```

#### 🎯 PowerPoint (.pptx)

```
파일 크기 제한: 50MB
처리 방식: 모든 슬라이드 텍스트 추출
주의: 이미지 내 텍스트는 인식 불가

슬라이드 구성:
  1. 제목 슬라이드
  2. 현황 분석
  3. 요구사항 (3 슬라이드)
  4. 예상 효과
```

### 파일 검증 규칙

**클라이언트 사이드 검증**:

```javascript
// 확장자 확인
const ALLOWED_EXTENSIONS = ['txt', 'md', 'pdf', 'xlsx', 'pptx'];

// 파일 크기 확인 (50MB)
const MAX_SIZE = 50 * 1024 * 1024;

// 파일 선택 시 실시간 검증
if (!isValidFile(file)) {
  alert('지원하지 않는 형식입니다.');
  // 업로드 차단
}
```

**에러 메시지 예**:

```
❌ 파일 형식 오류
지원하는 형식: txt, md, pdf, xlsx, pptx
업로드한 파일: unknown.doc

❌ 파일 크기 오류
파일 크기: 120MB
최대 크기: 50MB
```

---

## 결과 확인 및 다운로드

### 생성된 문서 구조

마크다운 문서는 항상 다음 8개 섹션으로 구성됩니다:

```markdown
# 개발 분석서

## 1. 개요 (Executive Summary)
- 프로젝트 목표
- 주요 기능
- 예상 효과

## 2. 요구사항 분석
- 핵심 요구사항
- 기능 요구사항
- 비기능 요구사항
- 명확화 필요 사항

## 3. 기술 설계
- 기술 스택
- 아키텍처 설계
- 새로운 컴포넌트
- 데이터 흐름

## 4. 데이터베이스 변경
- 신규 테이블
- 수정 테이블
- 마이그레이션 스크립트

## 5. 기술적 리스크 및 대응 방안
- 보안 리스크
- 성능 리스크
- 일정 리스크
- 대응 방안

## 6. 개발 계획
- 개발 일정
- 리소스 배치
- 마일스톤

## 7. 테스트 전략
- 테스트 항목
- 테스트 시나리오
- 테스트 일정

## 8. 부록
- 용어 정의
- 참고 자료
```

### 다운로드 형식 비교

| 형식 | 용도 | 파일명 | 크기 |
|------|------|--------|------|
| **Markdown** | 버전 관리, 편집 | `analysis_*.md` | 최소 |
| **HTML** | 웹 브라우징 | `analysis_*.html` | 작음 |
| **PDF** | 인쇄, 배포 | `analysis_*.pdf` | 중간 |
| **Word** | Office 편집 | `analysis_*.docx` | 중간 |
| **JSON** | 프로그래밍 | `analysis_*.json` | 최대 |

### 결과 활용 예시

#### 📋 Markdown 다운로드
```
용도: Git 저장소에 커밋, 팀 위키에 업로드
편집: VS Code, Obsidian, Notion 등에서 수정 가능
```

#### 📑 PDF 다운로드
```
용도: 경영진 보고, 고객 배포, 인쇄
특징: 포맷 고정, 어느 환경에서나 동일하게 표시
```

#### 📝 Word 다운로드
```
용도: 팀 내 협업 편집, 최종 보고서 작성
특징: Office에서 추가 포매팅 가능
```

---

## 설정 및 커스터마이징

### config.py 설정

```python
# 웹 서버
HOST = "0.0.0.0"
PORT = 8000

# 파일 처리
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = ['txt', 'md', 'pdf', 'xlsx', 'pptx']

# 분석
MAX_CONCURRENT_ANALYSES = 3
ANALYSIS_TIMEOUT_MINUTES = 30

# 저장소 정책
RETENTION_DAYS = 30  # 30일 후 자동 삭제
OUTPUT_DIR = "output"
```

### 환경 변수 (.env)

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (로컬 LLM)
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=mistral
LLM_API_KEY=ollama

# 개발 모드
DEBUG=true
LOG_LEVEL=INFO
```

### 프롬프트 커스터마이징

각 에이전트의 프롬프트는 agents/*.py에서 수정 가능합니다:

```python
# agents/planner.py
class PlannerAgent:
    def __init__(self, client):
        self.system_prompt = """
        당신은 경험 많은 기획자입니다.
        사용자가 제시한 요구사항을 다음과 같이 분석해주세요:
        1. 핵심 요구사항
        2. 기능 요구사항
        3. 비기능 요구사항
        4. 모호한 부분
        ...
        """
```

**주의**: 프롬프트 변경 후 모의 모드로 먼저 테스트하세요.

---

## 자주 묻는 질문

### Q1: API 키가 없는데 사용할 수 있나요?

**A**: 네, 2가지 방법이 있습니다:

**방법 1: 모의 모드 (추천)**
```bash
python main.py --mock --input "요구사항"
```
- API 호출 없음
- 빠른 응답 (1-3초)
- UI 테스트에 최적

**방법 2: Ollama (오프라인)**
```bash
# Ollama 설치 후
ollama pull mistral

# 로컬 LLM 사용
export LLM_BASE_URL=http://localhost:11434/v1
python main.py --input "요구사항"
```

---

### Q2: 얼마나 빠른가요?

**A**: 입력 크기에 따라 다릅니다:

| 입력 크기 | 모의 모드 | Claude API | Ollama |
|---------|---------|-----------|--------|
| < 500자 | 1초 | 30초 | 15초 |
| 500-2000자 | 2초 | 60초 | 30초 |
| > 2000자 | 3초 | 120초 | 60초 |

---

### Q3: 생성된 분석을 수정할 수 있나요?

**A**: 현재는 다음과 같이 가능합니다:

1. **마크다운 다운로드 후 수정**
   - VS Code, Notion 등에서 편집
   - Git으로 버전 관리

2. **Word 다운로드 후 편집**
   - Office에서 추가 포매팅
   - 팀과 협업

3. **향후 계획**
   - 웹 UI에서 직접 편집 기능
   - 버전 관리 시스템 통합

---

### Q4: 분석 이력은 얼마나 보관되나요?

**A**: 기본 설정:

```python
RETENTION_DAYS = 30  # 30일 보관
```

30일 후 자동 삭제됩니다. 영구 보관이 필요하면:

```python
# config.py 수정
RETENTION_DAYS = 365  # 1년 보관
```

---

### Q5: 보안은 어떻게 되나요?

**A**: 다음과 같이 보호됩니다:

✅ **데이터 보안**
- 모든 데이터는 로컬에 저장 (클라우드 미사용)
- 사용자 입력은 샌드박스 처리
- 생성된 파일은 output/ 디렉토리에만 저장

✅ **API 보안**
- API 키는 .env에 저장
- .env는 .gitignore에 포함
- 환경 변수로도 설정 가능

✅ **웹 서버 보안**
- CORS 설정
- 파일 크기 제한 (50MB)
- 입력 검증

---

## 문제 해결

### 🔴 "API 키를 찾을 수 없습니다" 오류

**원인**: ANTHROPIC_API_KEY 설정 미흡

**해결 방법**:

```bash
# 방법 1: .env 파일 확인
cat .env

# .env 없으면 생성
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 방법 2: 환경 변수로 설정
export ANTHROPIC_API_KEY=sk-ant-...

# 방법 3: 모의 모드 사용
python main.py --mock --input "요구사항"
```

---

### 🔴 "포트 8000이 이미 사용 중입니다" 오류

**원인**: 다른 프로세스가 포트 8000을 사용 중

**해결 방법**:

```bash
# 방법 1: 기존 프로세스 확인
lsof -i :8000

# 방법 2: 프로세스 종료
kill -9 $(lsof -i :8000 -t)

# 방법 3: 다른 포트 사용
# config.py 수정
PORT = 8001

# 방법 4: 기존 프로세스 목록 확인 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### 🔴 "PDF 생성 실패" 오류

**원인**: WeasyPrint 의존성 누락

**해결 방법**:

```bash
# pip 재설치
pip install --upgrade weasyprint

# macOS의 경우
brew install weasyprint

# Linux (Ubuntu)
sudo apt-get install python3-dev python3-pip \
  libcairo2-dev libpango-1.0-0 libpango-cairo-1.0-0

pip install weasyprint
```

---

### 🔴 "파일을 열 수 없습니다" 오류

**원인**: 파일 경로 오류

**해결 방법**:

```bash
# 절대 경로 사용
python main.py --input "/absolute/path/to/file.txt"

# Windows 경로
python main.py --input "C:\\Users\\username\\Documents\\file.txt"

# 상대 경로는 현재 작업 디렉토리 기준
cd multi-agent
python main.py --input "./requirements.txt"
```

---

### 🔴 "분석이 멈췄습니다" (타임아웃)

**원인**: 네트워크 지연 또는 API 오류

**해결 방법**:

```bash
# 1. 네트워크 확인
ping api.anthropic.com

# 2. API 상태 확인
curl https://status.anthropic.com

# 3. 타임아웃 시간 증가
# config.py 수정
ANALYSIS_TIMEOUT_MINUTES = 60

# 4. 모의 모드로 시스템 확인
python main.py --mock --input "테스트"
```

---

### 🔴 "데이터베이스 오류"

**원인**: SQLite 파일 손상

**해결 방법**:

```bash
# 1. 데이터베이스 파일 확인
ls -la *.db

# 2. 백업 후 초기화
cp analysis.db analysis.db.backup
rm analysis.db

# 3. 다시 실행 (자동 생성)
python app.py
```

---

### 🔴 "메모리 부족" 오류

**원인**: 큰 파일 처리

**해결 방법**:

```bash
# 1. 동시 실행 개수 줄이기
# config.py 수정
MAX_CONCURRENT_ANALYSES = 1

# 2. 파일 크기 제한 줄이기
MAX_FILE_SIZE_MB = 30

# 3. 시스템 리소스 확인
# macOS/Linux
top

# Windows
tasklist | findstr python
```

---

### 📞 추가 지원

문제가 해결되지 않으면:

1. **GitHub Issues**: [이슈 보고](https://github.com/sungsik-lee/ai-agent/issues)
2. **로그 파일 수집**:
   ```bash
   # 로그 파일 확인
   tail -f logs/analysis.log
   ```
3. **디버그 모드 실행**:
   ```bash
   DEBUG=true python main.py --input "..."
   ```

---

<div align="center">

**📚 다음 단계**:  
[API 문서](API_REFERENCE.md) · [아키텍처](ARCHITECTURE.md)

</div>
