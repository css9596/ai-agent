# Windows exe 설치 및 사용 가이드

**간단하게 exe 파일을 더블클릭해서 AI 분석 프로그램을 실행할 수 있습니다!**

---

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [사전 준비](#사전-준비)
3. [exe 파일 생성 (개발자용)](#exe-파일-생성-개발자용)
4. [exe 파일 사용 (일반 사용자)](#exe-파일-사용-일반-사용자)
5. [문제 해결](#문제-해결)

---

## 시스템 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| OS | Windows 10 (Build 1903+) | Windows 11 |
| CPU | 2코어 | 4코어+ |
| RAM | 8GB | 16GB+ |
| 디스크 | 20GB | 50GB+ |
| Docker Desktop | 4.0+ | 최신 버전 |

---

## 사전 준비

### 필수 소프트웨어

1. **Docker Desktop 설치** (exe 파일 필수!)
   - 다운로드: https://www.docker.com/products/docker-desktop
   - 설치 후 실행 (시스템 트레이에서 Docker 아이콘 확인)

2. **Git (선택사항, exe 빌드 시에만)**
   - 다운로드: https://git-scm.com/download/win

### 폴더 구조

exe를 사용하려면 다음과 같이 배치해야 합니다:

```
C:\Program Files\AI분석서\  (또는 원하는 위치)
├── AI분석서생성.exe            ← 이 파일을 실행
└── multi-agent\               ← 반드시 같은 폴더에 있어야 함
    ├── docker-compose.yml
    ├── .env.offline
    ├── Dockerfile
    ├── static\
    ├── agents\
    ├── utils\
    ├── scripts\
    └── ...
```

---

## exe 파일 생성 (개발자용)

### 방법 1: Windows PowerShell (권장)

**1단계: PowerShell 실행 정책 허용**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2단계: 빌드 스크립트 실행**
```powershell
cd C:\path\to\multi-agent
powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
```

**3단계: exe 파일 확인**
```
dist\AI분석서생성.exe (약 10-15MB)
```

### 방법 2: 명령 프롬프트 (cmd)

```batch
cd C:\path\to\multi-agent

REM PyInstaller 설치
python -m pip install pyinstaller

REM exe 빌드
python -m PyInstaller ^
    --onefile ^
    --name "AI분석서생성" ^
    --distpath ".\dist" ^
    --specpath ".\build" ^
    --workpath ".\build" ^
    --console ^
    scripts\run-app.py
```

### 방법 3: WSL (Linux) 또는 macOS

```bash
cd multi-agent
chmod +x scripts/build-exe.sh
./scripts/build-exe.sh
```

### 빌드 결과

성공하면:
```
✓ 빌드 성공!

생성된 파일:
  dist\AI분석서생성.exe (10-15 MB)
```

---

## exe 파일 사용 (일반 사용자)

### 설정 방법

**1. 필요한 것 다운로드**

온라인 환경에서 준비한 사람으로부터 받은 파일:
- `AI분석서생성.exe` (exe 파일)
- `multi-agent.zip` (프로젝트 폴더)

**2. 파일 배치**

```bash
# C:\ 또는 D:\ 드라이브에 폴더 생성
mkdir "C:\AI분석서"

# 받은 파일들을 폴더에 배치
C:\AI분석서\
├── AI분석서생성.exe
└── multi-agent\
```

**3. ZIP 압축 해제**

`multi-agent.zip` → 압축 해제 → `multi-agent` 폴더 생성

### 실행 방법

**방법 1: 더블클릭 (가장 간단)**
```
C:\AI분석서\AI분석서생성.exe를 더블클릭
```

**방법 2: 명령 프롬프트**
```cmd
cd C:\AI분석서
AI분석서생성.exe
```

**방법 3: PowerShell**
```powershell
cd C:\AI분석서
& .\AI분석서생성.exe
```

### 실행 화면

exe를 실행하면 다음 과정이 자동으로 실행됩니다:

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║      AI 개발 분석서 생성 - 오프라인 환경                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

[1/5] Docker 설치 확인...
✓ Docker 설치 확인: Docker version 24.0.0, build abcdef

[2/5] Docker Compose 확인...
✓ Docker Compose 확인: Docker Compose version 2.20.0

[3/5] 구성 파일 확인...
✓ docker-compose.yml 확인: C:\AI분석서\multi-agent\docker-compose.yml

[4/5] 서비스 시작...
  기존 컨테이너 정리 완료
  Docker Compose 시작 중...
  (첫 실행: 이미지 빌드 + Ollama 다운로드로 10-30분 소요)
  ........ (진행 상황 표시)
✓ Docker Compose 시작 완료
  서버 시작 대기 중...
  ........ (앱 시작 대기)
  ✓ 완료!
  웹 브라우저 오픈 중...
✓ 브라우저 오픈: http://localhost:8000

[5/5] 실시간 로그 모니터링...

Ctrl+C를 눌러 로그 보기를 종료할 수 있습니다.
(서비스는 백그라운드에서 계속 실행됩니다)

--------

2026-04-05 12:35:00 INFO: 시스템 시작 (llm_mode="local")
2026-04-05 12:35:02 INFO: Uvicorn running on http://0.0.0.0:8000
...
```

### 사용 중

1. **웹 브라우저 자동 오픈**
   - http://localhost:8000으로 자동 이동
   - 아이콘과 스타일 확인

2. **분석 시작**
   - 텍스트 입력 또는 파일 업로드
   - "분석 시작" 버튼 클릭
   - 실시간 진행 상황 표시
   - 결과 확인

3. **로그 보기**
   - exe 콘솔 창에서 실시간 로그 표시
   - `Ctrl+C`로 로그 보기 종료 (서비스는 계속 실행)

4. **완료 후**
   - exe 창을 닫아도 서비스는 백그라운드에서 실행
   - 언제든지 http://localhost:8000 접속 가능

---

## 종료 및 재시작

### 종료 방법

**방법 1: exe에서 종료**
```
exe 콘솔 창에서 Ctrl+C 누르기
→ 로그 보기만 종료 (서비스는 계속 실행)
```

**방법 2: Docker 정지**
```cmd
cd C:\AI분석서\multi-agent
docker-compose down
```

**방법 3: 작업 관리자**
```
Windows Task Manager에서 Docker Desktop 종료
```

### 재시작

exe를 다시 실행하면:
- 기존 컨테이너 자동 정리
- 새로운 서비스 시작
- 데이터는 유지됨 (output/, logs/, projects/ 폴더)

---

## 문제 해결

### 문제 1: "[ERROR] Docker Desktop이 설치되지 않았습니다"

**증상:**
```
[ERROR] Docker Desktop이 설치되지 않았습니다.

설치 방법:
1) Docker Desktop 다운로드 (무료):
   https://www.docker.com/products/docker-desktop
   
2) 설치 파일 실행:
   - 다운로드 완료 후 설치 파일 더블클릭
   - 설치 마법사 따라가기 (기본 설정으로 OK)
   - 설치 완료 후 컴퓨터 재시작 (권장)
   
3) Docker Desktop 시작:
   - 설치 후 시작 메뉴에서 'Docker Desktop' 검색
   - Docker Desktop 아이콘이 초록색으로 변할 때까지 대기 (약 30초)
   - 시스템 트레이(화면 우측 아래)에 Docker 아이콘 표시 확인
   
4) 이 프로그램 다시 실행
```

**해결 단계:**
1. 위의 링크에서 Docker Desktop 다운로드
2. 설치 파일을 더블클릭하고 설치 진행
3. 컴퓨터 재시작
4. 시작 메뉴에서 "Docker Desktop" 검색해 실행
5. 시스템 트레이에 Docker 아이콘이 초록색으로 표시될 때까지 대기 (약 30초)
6. exe 파일 다시 실행

**팁**: Docker Desktop을 항상 실행해두면 exe 시작 시간이 단축됩니다.

### 문제 1-2: "[ERROR] Docker Desktop이 응답하지 않습니다"

**증상:**
```
[ERROR] Docker Desktop이 응답하지 않습니다 (실행 중이 아닐 수 있음).

해결 방법:
1) Docker Desktop 시작:
   - 시스템 트레이(화면 우측 아래)에서 Docker 아이콘 찾기
   - 없으면 시작 메뉴에서 'Docker Desktop' 검색해 실행
   - Docker 아이콘이 초록색으로 변할 때까지 대기 (약 30초)
   
2) 이 프로그램 다시 실행

[팁] Docker Desktop을 항상 실행해두면 다음부터 더 빠릅니다.
```

**해결 단계:**
1. 시스템 트레이(화면 우측 아래)에서 Docker 아이콘 확인
2. 아이콘이 없으면 시작 메뉴에서 "Docker Desktop" 검색
3. Docker Desktop 실행 (첫 실행은 30초 정도 소요)
4. 아이콘이 초록색으로 변할 때까지 대기
5. exe 파일 다시 실행

### 문제 2: "docker-compose.yml을 찾을 수 없습니다"

**증상:**
```
✗ docker-compose.yml을 찾을 수 없습니다
```

**해결:**
- 폴더 구조 확인:
  ```
  C:\AI분석서\
  ├── AI분석서생성.exe
  └── multi-agent\
      ├── docker-compose.yml    ← 이 파일 필수
      └── ...
  ```

### 문제 3: "서버 응답 확인 실패"

**증상:**
```
⚠ 서버 응답 확인 실패. 브라우저를 수동으로 열어주세요.
```

**해결:**
1. 브라우저를 직접 열기
2. http://localhost:8000 입력
3. 페이지 로드 대기 (10-20초)
4. Ollama 첫 실행 시 모델 로드 (5-20분)

### 문제 4: "포트 8000이 이미 사용 중"

**증상:**
```
✗ Docker Compose 시작 실패:
Error response from daemon: Ports are not available
```

**해결:**
```cmd
REM 포트 8000을 사용하는 프로세스 종료
netstat -ano | findstr :8000
taskkill /PID <PID> /F

REM 또는 다른 포트 사용 (C:\AI분석서\multi-agent\.env 수정)
PORT=8080
```

### 문제 5: 웹페이지 스타일이 깨짐

**증상:**
```
아이콘이 안 보이거나, 배경색이 없음
```

**해결:**
1. 브라우저 캐시 삭제
2. `Ctrl+F5` 강력 새로고침
3. 다른 브라우저에서 확인

### 문제 6: 첫 분석이 매우 느림

**증상:**
```
첫 실행 후 분석이 5분 이상 걸림
```

**원인:**
- Ollama 모델이 처음 로드되면 느림 (5-20분)
- 이후 분석부터는 빠름

**해결:**
기다리거나 `.env` 파일에서 더 작은 모델 선택:
```ini
LLM_MODEL=llama3.2:3b  # 더 빠름, 정확도 낮음
```

---

## 고급 설정

### 포트 변경

1. `C:\AI분석서\multi-agent\.env` 파일 열기
2. `PORT=8000` 변경 (예: `PORT=8080`)
3. exe 다시 실행

### 모델 변경

1. `C:\AI분석서\multi-agent\.env` 파일 열기
2. `LLM_MODEL=qwen2.5:7b` 변경

옵션:
- `llama3.2:3b` - 가장 빠름 (2.5GB), 정확도 낮음
- `qwen2.5:7b` - 균형 (5GB), 권장
- `llama3.3:70b` - 가장 정확 (40GB), 느림

3. exe 다시 실행 (처음 모델은 다운로드, 5-20분)

### 로그 파일 확인

```
C:\AI분석서\multi-agent\logs\
├── analysis_YYYYMMDD.log
└── ...
```

### 분석 결과 확인

```
C:\AI분석서\multi-agent\output\
├── analysis_YYYYMMDD_HHMMSS.md
└── ...
```

---

## 자주 묻는 질문

### Q: 여러 사용자가 동시에 사용할 수 있나요?
**A:** 한 대의 컴퓨터에서 여러 사용자가 같은 exe를 사용하면 포트 충돌이 발생합니다. 각 사용자가 다른 포트를 사용하도록 `.env` 파일에서 `PORT=8000/8001/8002...` 로 설정하세요.

### Q: 인터넷이 필요한가요?
**A:** 아니요. 완전 오프라인 환경에서 동작합니다. Docker만 필요합니다.

### Q: 데이터는 안전한가요?
**A:** 네. 모든 분석이 로컬 컴퓨터에서 처리되고, 클라우드로 전송되지 않습니다.

### Q: Claude API 비용이 드나요?
**A:** 아니요. 무료 Ollama 오픈소스 LLM을 사용하므로 비용이 없습니다.

### Q: exe 파일이 안전한가요?
**A:** 네. GitHub에서 오픈소스 코드로부터 빌드되었으므로 악성 코드가 없습니다.

### Q: exe의 크기가 큰 이유는?
**A:** Python 런타임 + 모든 라이브러리를 exe에 포함했기 때문입니다 (10-15MB). Docker 이미지는 별도입니다.

---

## 추가 지원

- 프로젝트 GitHub: (링크)
- 문제 보고: (링크)
- 설정 파일: `.env.offline`
- 배포 가이드: `OFFLINE_DEPLOYMENT.md`

---

**설치 완료! exe를 더블클릭해서 AI 분석을 시작하세요! 🎉**
