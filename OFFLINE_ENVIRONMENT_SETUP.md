# 오프라인 환경 완전 셋팅 가이드

**인터넷이 없는 폐쇄망 환경에서 AI 분석 프로그램을 실행하기 위한 완벽한 가이드**

---

## 📋 개요

```
온라인 환경 (1회 준비)          오프라인 환경 (언제든지 사용)
┌─────────────────────┐       ┌──────────────────────┐
│ 1. Python 다운로드   │       │ 1. Python 설치       │
│ 2. Docker 다운로드   │  →→→  │ 2. Docker 설치       │
│ 3. 패키지 준비       │  USB  │ 3. exe 실행          │
│ 4. ZIP 패키징        │       │ (자동으로 작동)      │
└─────────────────────┘       └──────────────────────┘
```

---

## 🖥️ 온라인 환경에서의 준비 (1회만 필요)

### 준비물
- Windows PC (온라인 연결)
- USB 드라이브 (최소 16GB)
- 인터넷 연결

### Step 1: 필요한 파일 다운로드

#### 1-1. Python 공식 설치 파일 다운로드

```
1. https://www.python.org/downloads/ 접속
2. "Download Python 3.9" (또는 3.10, 3.11) 클릭
3. Windows installer (64-bit) 다운로드
   → 예: python-3.9.x-amd64.exe (약 25MB)
4. USB에 저장: USB:\installers\python-3.9.x-amd64.exe
```

#### 1-2. Docker Desktop 설치 파일 다운로드

```
1. https://www.docker.com/products/docker-desktop 접속
2. "Download for Windows" 클릭
3. Docker Desktop for Windows 다운로드
   → 예: Docker Desktop Installer.exe (약 500MB)
4. USB에 저장: USB:\installers\Docker Desktop Installer.exe
```

#### 1-3. Git 설치 파일 다운로드 (선택사항)

```
1. https://git-scm.com/download/win 접속
2. 64-bit Git for Windows Setup 다운로드
   → 예: Git-2.x.x-64-bit.exe (약 50MB)
3. USB에 저장: USB:\installers\Git-2.x.x-64-bit.exe
```

---

### Step 2: 프로젝트 파일 준비

#### 2-1. 배포 패키지 다운로드

```powershell
# Windows PC의 cmd 또는 PowerShell에서:

# 1. 프로젝트 클론
cd C:\temp
git clone https://github.com/css9596/ai-agent.git
cd ai-agent

# 2. exe 빌드 (이미 완료했다면 생략)
powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
# → dist\AIAnalyzer.exe 생성

# 3. 배포 패키지 준비
mkdir dist\deployment
Copy-Item .\dist\AIAnalyzer.exe .\dist\deployment\
Copy-Item . .\dist\deployment\ -Recurse -Exclude .git, .venv, __pycache__, build, dist

# 4. ZIP 압축
Compress-Archive -Path .\dist\deployment -DestinationPath .\dist\ai-agent-deployment.zip

# 5. USB에 저장
Copy-Item .\dist\ai-agent-deployment.zip E:\  # E:는 USB 드라이브
```

#### 2-2. 오프라인 패키지 준비 (선택사항, 더 빠른 설치)

```powershell
# Python pip 패키지 미리 다운로드 (인터넷에서)
cd C:\temp\ai-agent

# 방법: requirements.txt에서 패키지 다운로드
pip download -r requirements.txt -d .\packages

# USB에 저장
Copy-Item .\packages E:\

# 이렇게 하면 오프라인 PC에서 인터넷 없이 pip install 가능
```

---

### Step 3: USB 준비 완료

#### USB 최종 구조

```
E:\ (USB)
├── installers\
│   ├── python-3.9.x-amd64.exe          (약 25MB)
│   ├── Docker Desktop Installer.exe    (약 500MB)
│   └── Git-2.x.x-64-bit.exe           (약 50MB) [선택]
│
├── ai-agent-deployment.zip             (약 500MB)
│
└── packages\                           [선택]
    ├── anthropic-0.x.x-py3-none-any.whl
    ├── fastapi-0.x.x-py3-none-any.whl
    └── ... (requirements.txt의 모든 패키지)
```

**USB 용량**: 약 1-2GB (최소 16GB USB 권장)

---

## 🔧 오프라인 환경에서의 설치

### 준비물
- USB (온라인 PC에서 준비한 파일들)
- Windows PC (오프라인)
- 관리자 권한

### Step 1: Python 설치

```powershell
# 1. USB의 Python 설치 파일 실행
E:\installers\python-3.9.x-amd64.exe

# 2. 설치 옵션 (매우 중요!)
   - [v] Add Python 3.9 to PATH           (반드시 체크!)
   - [v] Install launcher for all users
   - Installation type: "Install for all users" 권장

# 3. "Install Now" 클릭 후 완료 대기 (약 5분)

# 4. 설치 확인 (새 PowerShell 창에서)
python --version
# 예상: Python 3.9.x
```

### Step 2: Docker Desktop 설치

```powershell
# 1. USB의 Docker 설치 파일 실행
E:\installers\Docker Desktop Installer.exe

# 2. 설치 과정
   - 모든 기본 옵션 그대로 진행
   - Windows Subsystem for Linux (WSL 2) 자동 설치

# 3. 설치 완료 후 컴퓨터 재부팅 (매우 중요!)
Restart-Computer

# 4. 재부팅 후 Docker 확인
docker --version
# 예상: Docker version 24.0.0 이상
```

**⚠️ 주의**: Docker Desktop 설치 후 반드시 재부팅해야 합니다!

### Step 3: Git 설치 (선택사항)

```powershell
# USB에서 프로젝트를 직접 복사했다면 생략 가능
E:\installers\Git-2.x.x-64-bit.exe

# 설치: 모든 기본 옵션 그대로 진행
```

---

## 📦 배포 패키지 설치

### Step 1: USB에서 압축 해제

```powershell
# 1. 배포 폴더 생성
mkdir C:\AIAnalyzer

# 2. USB의 ZIP 파일 압축 해제
Expand-Archive -Path E:\ai-agent-deployment.zip -DestinationPath C:\AIAnalyzer

# 3. 폴더 구조 확인
cd C:\AIAnalyzer
ls -Name
# 예상: AIAnalyzer.exe, docker-compose.yml, app.py, agents, scripts, static, utils, ...
```

### Step 2: pip 패키지 설치 (오프라인 패키지가 있는 경우)

```powershell
# USB에 packages\ 폴더가 있으면:
cd C:\AIAnalyzer

# requirements.txt 설치
pip install --no-index --find-links E:\packages -r requirements.txt

# 이 방법이 없으면:
pip install -r requirements.txt
# (온라인이 필요하므로 불가)
```

---

## 🚀 exe 실행

### 첫 실행

```powershell
# 1. 현재 위치 확인
cd C:\AIAnalyzer

# 2. exe 실행 (3가지 방법)

# 방법 A: 더블클릭 (가장 간단)
# C:\AIAnalyzer\AIAnalyzer.exe를 더블클릭

# 방법 B: PowerShell에서 실행
.\AIAnalyzer.exe

# 방법 C: 명령 프롬프트에서 실행
AIAnalyzer.exe
```

### 자동 실행 과정

```
[1/5] Docker 설치 확인...
  ✓ Docker version 24.0.0 확인

[2/5] Docker Compose 확인...
  ✓ Docker Compose version 2.20.0 확인

[3/5] 설정 파일 확인...
  ✓ docker-compose.yml 확인: C:\AIAnalyzer\docker-compose.yml

[4/5] 서비스 시작...
  기존 컨테이너 정리 완료
  Docker Compose 시작 중...
  ✓ Docker Compose 시작 완료
  서버 시작 대기 중... 완료!
  웹 브라우저 오픈 중...
  ✓ 브라우저 오픈: http://localhost:8000

[5/5] 실시간 로그 모니터링...

2026-04-05 12:35:00 INFO: 시스템 시작 (llm_mode="local")
2026-04-05 12:35:02 INFO: Uvicorn running on http://0.0.0.0:8000
```

### ⏱️ 첫 실행 시간

- **docker-compose 시작**: 약 30-60초
- **Ollama 모델 다운로드**: 약 5-20분 (첫 분석 시)
- **이후 분석**: 약 30초 이내

---

## ❓ 문제 해결

### 문제 1: "Docker가 설치되지 않았거나 실행 중이 아닙니다"

**증상:**
```
✗ Docker Desktop이 설치되지 않았거나 실행 중이 아닙니다.
```

**해결:**
1. Docker Desktop 재부팅 확인 (시스템 트레이 아이콘 확인)
2. Docker Desktop 애플리케이션 수동 실행
3. exe 다시 실행

### 문제 2: "docker-compose.yml을 찾을 수 없습니다"

**증상:**
```
✗ docker-compose.yml을 찾을 수 없습니다
```

**해결:**
1. 폴더 구조 확인:
   ```powershell
   C:\AIAnalyzer\
   ├── AIAnalyzer.exe
   ├── docker-compose.yml        ← 필수
   └── multi-agent\              ← 또는 여기에
   ```
2. ZIP을 제대로 압축 해제했는지 확인
3. exe를 C:\AIAnalyzer\ 폴더에서 실행

### 문제 3: "Python이 설치되지 않았습니다"

**증상:**
```
Python이 설치되지 않았습니다. Add Python to PATH를 확인하세요.
```

**해결:**
1. Python이 PATH에 있는지 확인:
   ```powershell
   python --version
   ```
2. 설치 안 됐으면 USB에서 다시 설치 (Add Python to PATH 체크)
3. PowerShell 재시작 후 다시 확인

### 문제 4: "포트 8000이 이미 사용 중입니다"

**증상:**
```
Error response from daemon: Ports are not available
```

**해결:**
1. 포트 사용 프로세스 확인:
   ```powershell
   netstat -ano | findstr :8000
   ```
2. 프로세스 종료:
   ```powershell
   taskkill /PID <PID> /F
   ```
3. 또는 다른 포트 사용 (.env 파일 수정)

### 문제 5: "첫 분석이 매우 느림"

**증상:**
```
첫 실행 후 분석이 5분 이상 걸림
```

**원인:**
- Ollama가 qwen2.5:7b 모델 처음 로드 (5-20분)
- 이후 분석부터는 빠름

**해결:**
- 첫 분석은 기다리기
- 또는 .env 파일에서 더 작은 모델 선택

---

## 📊 시스템 요구사항

| 항목 | 최소 | 권장 |
|-----|------|------|
| OS | Windows 10 Build 1903+ | Windows 11 |
| CPU | 2코어 | 4코어+ |
| RAM | 8GB | 16GB+ |
| 디스크 | 20GB | 50GB+ |
| Docker | 24.0.0+ | 최신 버전 |
| Python | 3.9+ | 3.9~3.11 |

---

## 🔄 여러 PC에서 재사용

준비된 USB를 다른 오프라인 PC에서도 재사용 가능:

```powershell
# 각 PC에서 반복:
# 1. Python 설치 (Step 1)
# 2. Docker 설치 (Step 2)
# 3. 배포 패키지 설치 (Step 3)
# 4. exe 실행 (Step 4)

# 각 PC는 독립적으로 작동합니다
```

---

## ✅ 완성 체크리스트

### 온라인 PC 준비
- [ ] Python 설치 파일 다운로드 (USB에 저장)
- [ ] Docker Desktop 설치 파일 다운로드 (USB에 저장)
- [ ] exe 빌드 완료 (AIAnalyzer.exe)
- [ ] 배포 패키지 ZIP 생성
- [ ] ZIP을 USB에 저장
- [ ] (선택) pip 패키지를 USB\packages\에 다운로드

### 오프라인 PC 설치
- [ ] Python 설치 완료
- [ ] Docker Desktop 설치 & 재부팅 완료
- [ ] 배포 패키지 압축 해제 (C:\AIAnalyzer\)
- [ ] exe 첫 실행 테스트
- [ ] Docker Compose 자동 시작 확인
- [ ] 브라우저에서 http://localhost:8000 접속 확인
- [ ] 첫 분석 실행 (5-20분 대기)
- [ ] 이후 분석 속도 확인 (약 30초 이내)

---

## 🎯 최종 결과

오프라인 PC에서:
```
✅ exe 더블클릭 → 자동으로 모든 것이 시작됨
✅ 브라우저 자동 열림
✅ 분석 준비 완료
✅ 인터넷 연결 불필요
```

**이제 폐쇄망 환경에서도 완전히 독립적으로 작동합니다!** 🎉
