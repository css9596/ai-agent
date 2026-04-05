# 완전 배포 가이드 (Mac/Windows/오프라인)

**마지막 업데이트**: 2026-04-06

---

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [Mac 환경 배포](#mac-환경-배포)
3. [Windows 환경 배포](#windows-환경-배포)
4. [오프라인 환경 배포](#오프라인-환경-배포)
5. [첫 실행 체크리스트](#첫-실행-체크리스트)
6. [배포 후 검증](#배포-후-검증)

---

## 시스템 요구사항

### 모든 환경

| 항목 | 요구사항 | 비고 |
|------|---------|------|
| Docker Desktop | 4.0+ | 필수 (포함: Docker, Docker Compose) |
| Python | 3.9+ | Mac/Windows exe 빌드 시 필요 |
| 디스크 공간 | 최소 20GB | Docker 이미지 + Ollama 모델 |
| RAM | 최소 8GB | Ollama 모델 로드용 |
| 인터넷 | 첫 실행 시만 필요 | 이미지/모델 다운로드 |

### Mac 추가 요구사항

- macOS 10.14+ (또는 Apple Silicon M1/M2/M3)
- Docker Desktop for Mac (Intel 또는 Apple Silicon 버전)

### Windows 추가 요구사항

- Windows 10 (Build 1903+) 이상 또는 Windows 11
- Docker Desktop for Windows
- PowerShell 7.0+ (또는 cmd.exe)

---

## Mac 환경 배포

### 1단계: Docker Desktop 설치

```bash
# Apple Silicon (M1/M2/M3)
# https://desktop.docker.com/mac/main/arm64/Docker.dmg 다운로드
# 또는 Intel Mac: Intel 버전 다운로드

# 설치 확인
docker --version  # Docker version 24.0.0 이상
docker run hello-world  # "Hello from Docker!" 메시지 확인
```

### 2단계: 코드 준비

```bash
# GitHub 클론 또는 pull
cd /Users/sungsik/workspace/ai-agent/multi-agent
git pull

# 필수 디렉토리 확인
ls -la data/
ls -la static/vendor/
```

### 3단계: Docker Compose 실행

```bash
# 기존 컨테이너 정리 (필요시)
docker-compose down -v

# 첫 실행: 이미지 빌드 + 컨테이너 시작 (10-30분)
docker-compose up -d --build

# 상태 확인
docker-compose ps

# 로그 모니터링
docker-compose logs -f app
```

**예상 로그**:
```
multi-agent-app | 2026-04-06 12:00:00 INFO: 시스템 시작
multi-agent-app | 2026-04-06 12:00:02 INFO: Uvicorn running on http://0.0.0.0:8000
```

### 4단계: Ollama 모델 다운로드

첫 실행 시 모델을 수동으로 다운로드해야 합니다:

```bash
# 모델 다운로드 (5-20분 소요)
docker-compose exec ollama ollama pull qwen2.5:7b

# 진행 상황 확인
docker-compose logs -f ollama

# 다운로드 완료 확인
docker-compose exec ollama ollama list
```

### 5단계: 웹 UI 접속

```
브라우저: http://localhost:8000

✓ 메인 UI (파일 업로드, 분석)
✓ 관리자 대시보드: http://localhost:8000/admin
```

### 6단계: 분석 테스트

```
1. 메인 화면에서 텍스트 입력: "게시판에 파일 첨부 기능 추가"
2. "분석 시작" 클릭
3. 15-60초 후 결과 확인
4. 다양한 형식으로 내보내기 (Markdown, PDF, Word, HTML, JSON)
```

---

## Windows 환경 배포

### 1단계: Docker Desktop 설치

```powershell
# https://www.docker.com/products/docker-desktop 다운로드
# Docker.msi 더블클릭 → 설치 마법사 따라가기

# 설치 확인
docker --version  # Docker version 24.0.0 이상
docker run hello-world
```

### 2단계: 코드 준비

```powershell
# 폴더로 이동
cd C:\경로\multi-agent

# 최신 코드 pull
git pull

# 필수 폴더 확인
dir data
dir static\vendor
```

### 3단계: Docker Compose 실행

```powershell
# 기존 컨테이너 정리 (필요시)
docker-compose down -v

# 첫 실행: 이미지 빌드 + 컨테이너 시작 (10-30분)
docker-compose up -d --build

# 상태 확인
docker-compose ps

# 로그 모니터링
docker-compose logs -f app
```

### 4단계: Ollama 모델 다운로드

```powershell
# 모델 다운로드
docker-compose exec ollama ollama pull qwen2.5:7b

# 진행 상황 확인
docker-compose logs -f ollama

# 완료 확인
docker-compose exec ollama ollama list
```

### 5단계: 웹 UI 접속

```
브라우저: http://localhost:8000

✓ 메인 UI (파일 업로드, 분석)
✓ 관리자 대시보드: http://localhost:8000/admin
```

### 6단계: exe 빌드 (선택사항, 최종 사용자 배포용)

```powershell
# PowerShell 실행 정책 설정 (1회만)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# exe 빌드
powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
# → dist\AI분석서생성.exe 생성 (15-20MB)

# 배포 패키지 준비
mkdir dist\AI분석서배포
cp dist\AI분석서생성.exe dist\AI분석서배포\
cp -r . dist\AI분석서배포\multi-agent\ -Exclude .git,build,dist,__pycache__

# ZIP 압축
Compress-Archive -Path .\dist\AI분석서배포 -DestinationPath .\dist\AI분석서배포.zip
# → USB, 이메일, 클라우드로 전달
```

---

## 오프라인 환경 배포

### 특징

- 인터넷 연결 없이 완전히 독립적으로 실행 가능
- 모든 CSS/JS, Ollama 모델을 로컬에 보유
- 폐쇄망 환경 지원

### 준비 (온라인 환경, 1회만)

```bash
# static/vendor/ 확인
ls -la static/vendor/

# 파일 목록:
# - tailwind.min.css (2.8MB)
# - marked.min.js (39KB)
# - fontawesome/css/all.min.css (100KB)
# - fontawesome/webfonts/*.woff2 (280KB)

# Docker 이미지 빌드 & 모델 다운로드
docker-compose up -d --build
docker-compose exec ollama ollama pull qwen2.5:7b

# 배포 패키지 생성
mkdir -p dist/AI분석서배포
cp -r . dist/AI분석서배포/multi-agent/

# ZIP 압축
zip -r dist/AI분석서배포.zip dist/AI분석서배포/
```

### 배포 (오프라인 환경)

```bash
# 1. 패키지 전달 (USB, 외장드라이브)
C:\AI분석서\
├── AI분석서생성.exe (또는 바이너리)
└── multi-agent\
    ├── docker-compose.yml
    ├── Dockerfile
    ├── static/vendor/  # 로컬 CSS/JS
    ├── .env (LLM_MODE=local)
    └── ... (모든 소스코드)

# 2. Docker Desktop 설치 (온라인에서 미리 준비 또는 설치 미디어)

# 3. exe 또는 스크립트 실행
./AI분석서생성.exe  # 또는 docker-compose up -d

# 4. 브라우저 접속
http://localhost:8000
```

---

## 첫 실행 체크리스트

### ⏱️ 시간 계획

| 단계 | 소요 시간 | 작업 |
|------|----------|------|
| Docker 설치 | 10-20분 | 다운로드 + 설치 + 확인 |
| 코드 pull | 1분 | git pull |
| Docker 이미지 빌드 | 5-10분 | docker-compose up -d --build |
| Ollama 모델 다운로드 | 5-20분 | ollama pull qwen2.5:7b |
| **총 첫 실행** | **20-50분** | - |
| 이후 실행 | 30-120초 | docker-compose up -d |

### 체크리스트

```
☐ Docker Desktop 설치 및 실행 확인
  docker --version 출력 확인

☐ git pull 완료
  git log --oneline -1 확인

☐ Docker 컨테이너 상태 확인
  docker-compose ps → "healthy" 또는 "starting"

☐ Ollama 모델 다운로드
  docker-compose exec ollama ollama list → qwen2.5:7b 표시

☐ 웹 UI 접속
  http://localhost:8000 → CSS/JS 정상 로드

☐ 분석 테스트
  텍스트 입력 → "분석 시작" → 결과 확인

☐ 관리자 대시보드
  http://localhost:8000/admin → 통계/로그 표시
```

---

## 배포 후 검증

### 1. Docker 상태 확인

```bash
# Mac/Linux
docker-compose ps
docker-compose logs -f app

# Windows PowerShell
docker-compose ps
docker-compose logs -f app
```

**정상 상태**:
```
NAME                 STATUS
multi-agent-app      Up (health: healthy)
multi-agent-ollama   Up (health: healthy)
```

### 2. 웹 UI 동작 검증

| 기능 | 확인 방법 | 예상 결과 |
|------|----------|----------|
| CSS 로드 | http://localhost:8000 | 색상, 스타일 정상 |
| Font Awesome | 헤더 아이콘 | 아이콘 표시 정상 |
| 파일 업로드 | 파일 선택 | 파일 미리보기 표시 |
| 분석 실행 | "분석 시작" 클릭 | 15-60초 후 결과 |
| 내보내기 | "다운로드" 클릭 | PDF/Word/HTML 생성 |
| 관리자 | /admin 접속 | 통계/로그 표시 |

### 3. 오프라인 검증 (선택사항)

```bash
# 인터넷 끊기 (또는 네트워크 차단)

# 1. Docker 이미지 재빌드 불가능 확인
docker-compose down
docker-compose build  # 실패 예상

# 2. 하지만 기존 컨테이너는 시작 가능
docker-compose up -d  # 성공

# 3. 분석 실행
http://localhost:8000 → 텍스트 입력 → 분석 시작
# → Ollama 로컬 모델로 정상 처리

# 4. 인터넷 복구
# (필요시 이미지 재빌드 가능)
```

---

## 자주 묻는 질문

### Q1: 첫 실행이 20-50분 걸리는 이유는?

**A**: Docker 이미지 빌드(5-10분) + Ollama 모델 다운로드(5-20분) 때문입니다.
- 이 과정은 **첫 실행 1회만** 필요합니다.
- 이후 실행은 30-120초로 빠릅니다.
- 인터넷 속도에 따라 변동됩니다.

### Q2: 오프라인에서도 분석이 가능한가?

**A**: 네! 모든 CSS/JS와 Ollama 모델이 로컬에 있으므로 인터넷 불필요합니다.
- Docker만 있으면 됩니다.
- 폐쇄망 환경도 지원합니다.

### Q3: Windows exe는 필수인가?

**A**: 아니요. 선택사항입니다.
- **일반 사용자**: exe 권장 (더블클릭으로 실행)
- **개발팀**: Docker Compose 권장 (명령어 기반)

### Q4: Ollama 모델 크기가 크면?

**A**: 더 작은 모델을 선택할 수 있습니다:
- `llama3.2:3b` (2.5GB, 빠름)
- `qwen2.5:7b` (5GB, 균형) ← 기본
- `llama3.3:70b` (40GB, 정확)

### Q5: 포트 충돌이 있으면?

**A**: `.env` 파일에서 포트 변경:
```
PORT=8080  # 또는 8001, 8002 등
```

---

## 트러블슈팅은 다른 문서 참조

- **OLLAMA_HEALTH_CHECK_GUIDE.md** - 헬스 체크 문제
- **TROUBLESHOOTING.md** - 일반적인 문제 해결
- **README.md** - 기본 사용법

---

## 배포 완료!

**이제 완전히 배포 가능한 상태입니다!** ✅

모든 환경(Mac/Windows/오프라인)에서 독립적으로 실행 가능합니다. 🚀
