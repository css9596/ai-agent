# 프로젝트 폴더 구조 완벽 가이드

이 문서에서는 multi-agent 프로젝트의 모든 폴더와 파일이 무엇인지 설명합니다.

---

## 📁 전체 폴더 구조

```
multi-agent/
│
├─ 🎯 핵심 소스 코드 (프로그램 로직)
│  ├─ agents/                      ← AI 분석 에이전트들
│  ├─ utils/                       ← 공통 유틸리티 함수
│  ├─ static/                      ← 웹 UI (HTML, CSS, JS)
│  ├─ scripts/                     ← 실행/배포 스크립트
│  ├─ main.py                      ← CLI 모드 진입점
│  ├─ app.py                       ← 웹 서버 (FastAPI)
│  ├─ orchestrator.py              ← 에이전트 조율
│  ├─ config.py                    ← 설정 관리
│  └─ database.py                  ← 데이터베이스 관리
│
├─ 🐳 배포 관련 (Docker, 환경설정)
│  ├─ docker-compose.yml           ← Docker 서비스 구성
│  ├─ Dockerfile                   ← Docker 이미지 정의
│  ├─ .env                         ← 환경 변수 (로컬)
│  ├─ .env.offline                 ← 환경 변수 (오프라인)
│  └─ requirements.txt             ← Python 패키지 목록
│
├─ 📚 문서 (가이드, 설명서)
│  ├─ README.md                    ← 프로젝트 소개
│  ├─ CLAUDE.md                    ← 개발 가이드 (주요!)
│  ├─ OFFLINE_DEPLOYMENT.md        ← 오프라인 배포 가이드
│  ├─ WINDOWS_EXE_GUIDE.md         ← Windows exe 가이드
│  ├─ EXE_BUILD_EXPLAINED.md       ← exe 빌드 상세 설명
│  ├─ SIMULATION_GUIDE.md          ← 시뮬레이션 가이드
│  ├─ PROJECT_STRUCTURE.md         ← 이 파일 (구조 설명)
│  ├─ API_REFERENCE.md             ← API 엔드포인트 명세
│  ├─ ARCHITECTURE.md              ← 기술 아키텍처
│  ├─ PHASE2_IMPLEMENTATION.md     ← Phase 2 계획
│  ├─ PHASE3_IMPLEMENTATION.md     ← Phase 3 계획
│  └─ IMPROVEMENT_ROADMAP.md       ← 개선 계획
│
├─ 🏗️ 빌드 및 배포 산출물
│  ├─ dist/                        ← 빌드 결과물 (exe + 패키지)
│  │  └─ AI분석서배포/             ← 배포 패키지
│  │     ├─ AI분석서생성           ← 실행 파일
│  │     └─ multi-agent/           ← 프로그램 폴더
│  ├─ build/                       ← PyInstaller 빌드 임시 폴더
│  └─ htmlcov/                     ← 테스트 커버리지 리포트
│
├─ 📊 실행 결과 (프로그램이 만드는 것)
│  ├─ output/                      ← 분석 결과 (MD 파일들)
│  ├─ logs/                        ← 실행 로그
│  ├─ projects/                    ← 업로드된 프로젝트 (Phase 6)
│  ├─ analysis_history.db          ← 분석 이력 데이터베이스
│  └─ temp_uploads/                ← 임시 업로드 파일
│
├─ 🔧 개발 환경
│  ├─ .venv/                       ← Python 가상 환경
│  ├─ .git/                        ← Git 버전 관리
│  ├─ .pytest_cache/               ← pytest 캐시
│  ├─ .gitignore                   ← Git 제외 파일 목록
│  └─ pytest.ini                   ← pytest 설정
│
└─ 📋 테스트 및 샘플
   ├─ sample_requirements.txt       ← 샘플 입력 파일
   ├─ sample_requirements.xlsx      ← 샘플 Excel
   └─ sample_requirements.pptx      ← 샘플 PowerPoint

════════════════════════════════════════════════════════════════════
```

---

## 🎯 핵심 소스 코드 (프로그램 로직)

### `agents/` 폴더
**목적**: 각 단계별 AI 분석 에이전트들

```
agents/
├─ planner.py              ← 요구사항 추출
├─ developer.py            ← 기술 설계
├─ reviewer.py             ← 리스크 검토
├─ documenter.py           ← 마크다운 생성
├─ impact_analyzer.py      ← 파일 영향도 분석 (Phase 4)
├─ quality_checker.py      ← 품질 검사 (Phase 4)
├─ chat_agent.py           ← 대화형 정제 (Phase 5A)
├─ source_comparator.py    ← 소스 비교 (Phase 6)
└─ __init__.py
```

**언제 수정하나?**
- 분석 로직을 개선할 때
- 새로운 에이전트를 추가할 때

---

### `utils/` 폴더
**목적**: 공통으로 사용하는 유틸리티 함수들

```
utils/
├─ claude_client.py        ← Claude API 연동
├─ llm_client.py          ← Ollama/로컬 LLM 연동
├─ file_processor.py      ← 파일 형식 처리
├─ logger.py              ← 로깅 기능
├─ export_formats.py      ← 결과 내보내기 (HTML, PDF 등)
├─ comparison.py          ← 분석 결과 비교
├─ queue_manager.py       ← 작업 큐 관리
├─ project_extractor.py   ← 프로젝트 소스 파싱 (Phase 6)
└─ __init__.py
```

**언제 수정하나?**
- API 연동 방식 변경
- 파일 형식 지원 추가
- 로깅 방식 개선

---

### `static/` 폴더
**목적**: 웹 UI (사용자가 보는 화면)

```
static/
├─ index.html             ← 메인 웹 페이지
├─ admin.html             ← 관리자 대시보드
└─ vendor/                ← 로컬화된 라이브러리
   ├─ tailwind.min.css
   ├─ marked.min.js
   └─ fontawesome/
      ├─ css/
      └─ webfonts/
```

**언제 수정하나?**
- UI 디자인 변경
- 새로운 기능 탭 추가
- 스타일 개선

---

### `scripts/` 폴더
**목적**: 설치, 빌드, 배포 스크립트

```
scripts/
├─ setup-offline.sh       ← CDN + pip 패키지 준비 (Linux/macOS)
├─ setup-offline.bat      ← CDN + pip 패키지 준비 (Windows)
├─ build-exe.sh           ← exe 빌드 (Linux/macOS)
├─ build-exe.ps1          ← exe 빌드 (Windows PowerShell)
├─ download-packages.sh   ← pip 패키지 캐시
└─ run-app.py             ← exe 실행 시 메인 스크립트
```

**언제 사용하나?**
- `setup-offline.sh/.bat`: 온라인 환경에서 1회만
- `build-exe.sh/.ps1`: exe 빌드할 때
- `run-app.py`: exe로 변환되어 실행됨

---

### 핵심 파일들

| 파일 | 목적 | 언제 수정? |
|------|------|----------|
| `main.py` | CLI 모드 진입점 | CLI 기능 추가 시 |
| `app.py` | 웹 서버 (FastAPI) | API 엔드포인트 추가 시 |
| `orchestrator.py` | 에이전트 조율 | 에이전트 순서 변경 시 |
| `config.py` | 설정값 관리 | 설정 항목 추가 시 |
| `database.py` | SQLite 관리 | 데이터 저장 방식 변경 시 |
| `requirements.txt` | Python 패키지 목록 | 라이브러리 추가/제거 시 |

---

## 🐳 배포 관련 (Docker, 환경설정)

### Docker 파일들

| 파일 | 목적 | 수정 빈도 |
|------|-----|---------|
| `docker-compose.yml` | 서비스 구성 (app + ollama) | 거의 안 함 |
| `Dockerfile` | Docker 이미지 정의 | 거의 안 함 |
| `.env` | 로컬 환경 변수 (개인용) | 자주 |
| `.env.offline` | 오프라인 환경 변수 (배포용) | 드물게 |
| `requirements.txt` | Python 패키지 목록 | 가끔 |

**역할**:
- `docker-compose.yml`: app과 Ollama 서비스가 어떻게 연동될지 정의
- `Dockerfile`: Python 3.9 + 패키지를 Docker 이미지로 변환
- `.env.offline`: 배포할 때 고객이 사용하는 기본 설정
- `requirements.txt`: Python 패키지 관리 (pip install할 목록)

---

## 📚 문서 (가이드, 설명서)

### 사용자별 추천 문서

| 대상 | 읽어야 할 문서 | 목적 |
|------|--------------|------|
| 개발자 | `CLAUDE.md` + `ARCHITECTURE.md` | 코드 이해, 개발 방법 |
| 운영자 | `OFFLINE_DEPLOYMENT.md` | 시스템 배포 및 관리 |
| 최종 사용자 | `WINDOWS_EXE_GUIDE.md` | exe 사용 방법 |
| 신규 기여자 | `README.md` + `CLAUDE.md` | 프로젝트 이해 |

### 각 문서의 역할

| 문서 | 내용 | 길이 |
|------|------|------|
| `README.md` | 프로젝트 소개, 빠른 시작 | 200줄 |
| `CLAUDE.md` | 개발 가이드, 아키텍처, 주의사항 | 300줄 |
| `OFFLINE_DEPLOYMENT.md` | Docker 기반 배포 | 400줄 |
| `WINDOWS_EXE_GUIDE.md` | exe 파일 사용 방법 | 400줄 |
| `EXE_BUILD_EXPLAINED.md` | exe 빌드 상세 설명 | 500줄 |
| `SIMULATION_GUIDE.md` | 시뮬레이션 체크리스트 | 430줄 |
| `API_REFERENCE.md` | API 엔드포인트 명세 | 200줄 |
| `ARCHITECTURE.md` | 기술 아키텍처 상세 | 300줄 |
| `PHASE2_IMPLEMENTATION.md` | Phase 2 계획서 | 150줄 |
| `PHASE3_IMPLEMENTATION.md` | Phase 3 계획서 | 150줄 |
| `IMPROVEMENT_ROADMAP.md` | 향후 개선 계획 | 200줄 |

---

## 🏗️ 빌드 및 배포 산출물

### `dist/` 폴더
**목적**: PyInstaller 빌드 결과물

```
dist/
├─ AI분석서생성              ← 실행 파일 (macOS/Linux)
└─ AI분석서배포/            ← 배포 패키지
   ├─ AI분석서생성           ← 실행 파일
   └─ multi-agent/           ← 프로그램 전체 폴더
```

**언제 생성?**
- `./scripts/build-exe.sh` 또는 `build-exe.ps1` 실행 시

**용도**:
- 배포용 패키지 준비
- USB 또는 클라우드에 업로드
- 고객에게 전달

---

### `build/` 폴더
**목적**: PyInstaller 빌드 임시 파일

```
build/
├─ AI분석서생성/            ← 빌드 과정의 중간 산출물
└─ AI분석서생성.spec       ← 빌드 설정 파일
```

**필요?**
- 빌드 완료 후 삭제 가능
- 재빌드할 때만 필요

---

### `htmlcov/` 폴더
**목적**: 테스트 커버리지 리포트

```
htmlcov/
├─ index.html              ← 테스트 커버리지 시각화
├─ *.html                  ← 파일별 커버리지
└─ ...
```

**언제 생성?**
- `pytest --cov=.` 명령 실행 시

**용도**:
- 어떤 코드가 테스트되었는지 확인

---

## 📊 실행 결과 (프로그램이 만드는 것)

### `output/` 폴더
**목적**: 분석 결과 저장

```
output/
├─ analysis_20260405_123456.md    ← 분석 결과 (Markdown)
├─ analysis_20260405_123457.md
└─ ...
```

**생성 시기**: 사용자가 분석을 실행할 때마다

---

### `logs/` 폴더
**목적**: 실행 로그 저장

```
logs/
├─ analysis_20260405.log          ← 일자별 로그 파일
└─ ...
```

**생성 시기**: 프로그램이 실행될 때

---

### `projects/` 폴더
**목적**: 업로드된 프로젝트 저장 (Phase 6)

```
projects/
├─ project_uuid_1/                ← 프로젝트 1
│  ├─ project.zip                 ← 업로드된 ZIP
│  └─ snapshot.json               ← 소스 구조 메타데이터
├─ project_uuid_2/                ← 프로젝트 2
└─ ...
```

**생성 시기**: 사용자가 프로젝트를 업로드할 때

---

### `analysis_history.db`
**목적**: 분석 이력 저장

```
SQLite 데이터베이스
├─ analyses 테이블          ← 분석 이력
└─ ...
```

**용도**: 관리자 대시보드에서 분석 이력 조회

---

### `temp_uploads/` 폴더
**목적**: 임시 업로드 파일 저장

```
temp_uploads/
├─ sample_xxx.pdf
├─ sample_xxx.xlsx
└─ ...
```

**정리**: 분석 완료 후 자동 삭제

---

## 🔧 개발 환경

### `.venv/` 폴더
**목적**: Python 가상 환경

```
.venv/
├─ bin/                    ← 실행 파일 (python, pip 등)
├─ lib/                    ← 설치된 라이브러리
└─ ...
```

**생성**: `python3 -m venv .venv`

**사용**: `source .venv/bin/activate`

---

### `.git/` 폴더
**목적**: Git 버전 관리

```
.git/
├─ objects/               ← 커밋 데이터
├─ refs/                  ← 브랜치 정보
├─ HEAD                   ← 현재 브랜치
└─ ...
```

**역할**: 코드 변경 이력 추적

---

### 기타 설정 파일

| 파일 | 목적 |
|------|------|
| `.gitignore` | Git에서 제외할 파일 목록 |
| `pytest.ini` | pytest 테스트 설정 |
| `.pytest_cache/` | pytest 캐시 (자동 생성) |

---

## 📋 테스트 및 샘플

### 샘플 파일들

```
sample_requirements.txt    ← 텍스트 요구사항 샘플
sample_requirements.xlsx   ← Excel 요구사항 샘플  
sample_requirements.pptx   ← PowerPoint 요구사항 샘플
```

**용도**:
- 프로그램 테스트
- 데모용
- 지원 형식 확인

---

## 🎯 빠른 참조

### "이 파일은 뭔가요?" - 빠른 답변

| 질문 | 답변 |
|------|------|
| 프로그램 코드는 어디? | `agents/`, `utils/`, `app.py`, `main.py` |
| 웹 화면은 어디? | `static/index.html` |
| Docker 설정은? | `docker-compose.yml`, `Dockerfile` |
| 배포 가이드는? | `OFFLINE_DEPLOYMENT.md`, `WINDOWS_EXE_GUIDE.md` |
| 개발 가이드는? | `CLAUDE.md` |
| 분석 결과는? | `output/` 폴더 |
| 실행 로그는? | `logs/` 폴더 |
| exe 파일은? | `dist/AI분석서배포/` |
| 환경 설정은? | `.env.offline` |
| 패키지 목록은? | `requirements.txt` |

---

## 📁 이해하기 쉬운 분류

### 수정이 필요한 파일들
```
개발/개선 할 때만 수정:
  ├─ agents/*.py           (분석 로직 개선)
  ├─ utils/*.py            (공통 기능 개선)
  ├─ app.py                (API 엔드포인트 추가)
  ├─ static/index.html     (UI 디자인 변경)
  └─ config.py             (설정 추가)

배포할 때만 수정:
  ├─ .env.offline          (고객 환경 설정)
  └─ requirements.txt      (패키지 추가)
```

### 자동 생성되는 파일들 (수정 금지)
```
프로그램 실행 중에 생성:
  ├─ output/               (분석 결과)
  ├─ logs/                 (실행 로그)
  ├─ analysis_history.db   (분석 이력)
  └─ temp_uploads/         (임시 파일)

빌드할 때 생성:
  ├─ build/                (PyInstaller 중간 파일)
  ├─ dist/                 (exe + 패키지)
  └─ htmlcov/              (테스트 리포트)

개발 환경:
  ├─ .venv/                (Python 가상 환경)
  ├─ .pytest_cache/        (pytest 캐시)
  └─ .git/                 (Git 데이터)
```

---

## 🚀 각 작업별 필요한 파일/폴더

### 프로그램 실행
```
필요한 것:
  ✅ app.py / main.py      (실행 진입점)
  ✅ agents/               (분석 로직)
  ✅ utils/                (공통 기능)
  ✅ config.py             (설정)
  ✅ static/               (웹 UI)
  ✅ docker-compose.yml    (Docker 설정)
  ✅ .env.offline          (환경 변수)
```

### 배포 패키지 생성
```
필요한 것:
  ✅ scripts/build-exe.sh  (빌드 스크립트)
  ✅ requirements.txt      (패키지 목록)
  ✅ 위의 모든 파일들      (프로그램 전체)

결과물:
  ✅ dist/AI분석서배포/    (배포 패키지)
```

### 고객에게 전달
```
고객이 받아야 할 것:
  ✅ dist/AI분석서배포/    (배포 패키지)
  ✅ WINDOWS_EXE_GUIDE.md  (사용 가이드)
```

---

## 💡 최종 정리

```
프로젝트 = 프로그램 코드 + 배포 방식 + 문서

┌─ agents/, utils/, app.py          프로그램 (실제 동작)
├─ docker-compose.yml, Dockerfile   배포 방식 (어떻게 실행)
├─ .env.offline                     환경 설정 (어디에서)
├─ static/                          사용자 인터페이스
├─ scripts/                         설치/빌드 도구
│
└─ README.md, CLAUDE.md, 기타 문서  설명서 (이해하기)
   ├─ 개발자용 (CLAUDE.md)
   ├─ 운영자용 (OFFLINE_DEPLOYMENT.md)
   └─ 사용자용 (WINDOWS_EXE_GUIDE.md)
```

이 구조가 이해되시나요? 더 궁금한 부분이 있으면 알려주세요! 😊
