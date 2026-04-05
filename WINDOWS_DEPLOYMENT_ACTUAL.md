# Windows PC에서 실제 배포하기 (단계별 가이드)

**현재 상황**: macOS에서 준비했고, Windows PC에서 실제로 exe를 빌드하고 배포하려고 합니다.

---

## 🎯 전체 과정 개요

```
Step 1: Windows PC 준비 (5-10분)
  ├─ Python 설치 확인
  ├─ Docker Desktop 설치
  └─ 프로젝트 복사

Step 2: exe 빌드 (10-15분)
  ├─ PyInstaller 설치
  ├─ build-exe.ps1 실행
  └─ exe 파일 생성 확인

Step 3: 배포 패키지 준비 (5분)
  ├─ 배포 폴더 만들기
  ├─ exe + multi-agent 폴더 배치
  └─ ZIP 압축

Step 4: exe 실행 테스트 (5분)
  ├─ 배포 폴더 준비
  ├─ exe 더블클릭
  └─ 정상 작동 확인
```

---

## 📋 Step 1: Windows PC 준비 (5-10분)

### 1-1. Python 설치 확인

**명령 프롬프트 또는 PowerShell에서 실행:**

```powershell
python --version
```

**예상 결과:**
```
Python 3.9.0 이상 필요 (3.9, 3.10, 3.11 모두 가능)
```

**만약 설치 안 되어있으면:**
1. https://www.python.org/downloads/ 에서 Windows 설치 파일 다운로드
2. 설치 시 **"Add Python to PATH"** 체크박스 반드시 클릭
3. 다시 `python --version` 확인

### 1-2. Docker Desktop 설치 확인

**명령 프롬프트에서 실행:**

```powershell
docker --version
```

**예상 결과:**
```
Docker version 24.0.0 이상
```

**만약 설치 안 되어있으면:**
1. https://www.docker.com/products/docker-desktop 에서 다운로드
2. 설치 후 컴퓨터 재부팅
3. Docker Desktop 애플리케이션 실행 (시스템 트레이에서 아이콘 확인)
4. 다시 `docker --version` 확인

### 1-3. 프로젝트 복사

**2가지 방법:**

**방법 A: 배포 패키지 ZIP으로 받기 (권장) ⭐**
```powershell
# 1. AI분석서배포.zip 파일 받기 (USB, 이메일, 클라우드)
# 2. 원하는 폴더에 압축 해제 (예: C:\AI분석서)
# 3. 폴더 구조:
#    C:\AI분석서\
#    ├── AI분석서생성.exe (이미 macOS 형식이지만, 아래서 다시 빌드)
#    └── multi-agent\
#        ├── docker-compose.yml
#        ├── scripts\
#        └── ...

# PowerShell에서:
cd C:\AI분석서\multi-agent
```

**방법 B: Git으로 클론하기 (Git 설치 필수)**
```powershell
# 원하는 폴더로 이동 (예: C:\Projects)
cd C:\Projects

# 프로젝트 복제
git clone https://github.com/css9596/ai-agent.git

cd ai-agent\multi-agent
```

### 확인: 필수 파일이 있는지 체크

**PowerShell에서 실행:**
```powershell
# 1. 현재 위치 확인
pwd
# 예상: C:\AI분석서\multi-agent (또는 git clone한 경로)

# 2. 필수 파일 확인 (Windows PowerShell 호환 명령어)
ls -Name | Select-String -Pattern "docker-compose|build-exe|requirements"
```

**예상 결과:**
```
build-exe.ps1
docker-compose.yml
requirements.txt
```

**또는 전체 폴더 구조 보기:**
```powershell
# 주요 폴더/파일 확인
ls -Directory
# 예상: agents  config  scripts  static  utils  ...

ls -Name | Select-String "\.yml|\.txt|\.py" | head -10
# 예상: app.py, config.py, docker-compose.yml, requirements.txt, ...
```

---

## 🔨 Step 2: exe 빌드 (10-15분)

### 2-1. PowerShell 실행 정책 허용

**PowerShell (관리자 권한)에서 실행:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**질문이 나오면:** `Y` (Yes) 입력 후 Enter

### 2-2. 빌드 스크립트 실행

**PowerShell에서 실행:**

```powershell
# 1. multi-agent 폴더로 이동 (현재 위치 확인 후)
pwd
# 결과가 C:\AI분석서\multi-agent 또는 C:\Projects\multi-agent 여야 함

# 2. 빌드 스크립트 실행
powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
```

**또는 한 줄로 실행:**
```powershell
cd C:\AI분석서\multi-agent; powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
```

**실행 과정:**
```
[1/4] Python 확인...
  ✓ Python 3.9.6

[2/4] PyInstaller 설치...
  → PyInstaller 설치 중... (1-2분)
  ✓ PyInstaller 6.19.0

[3/4] 이전 빌드 정리...
  ✓ 정리 완료

[4/4] exe 파일 생성 중... (5-10분 소요)
  [진행률 표시...]
  ✓ 빌드 성공!

생성된 파일:
  dist\AI분석서생성.exe (약 15-20MB, Windows 환경이므로 macOS보다 큼)

사용 방법:
  1. dist\AI분석서생성.exe를 원하는 폴더로 복사
  2. multi-agent\ 폴더와 같은 위치에 배치
  3. exe를 더블클릭해서 실행
```

### 2-3. 빌드 결과 확인

**PowerShell에서 실행:**

```powershell
# 1. 생성된 exe 파일 확인
ls -lh dist\AI분석서생성.exe

# 2. 파일 크기 확인 (MB 단위)
$size = (Get-Item .\dist\AI분석서생성.exe).Length / 1MB
Write-Host "exe 파일 크기: $([math]::Round($size, 2)) MB"

# 3. 파일이 제대로 생성되었는지 확인
Test-Path .\dist\AI분석서생성.exe
```

**예상 결과:**
```
ls 결과:
    Directory: C:\AI분석서\multi-agent\dist
Mode                 LastWriteTime         Length Name
----                 ---------------         ------ ----
-a---         2026-04-05    12:51       20000000 AI분석서생성.exe

파일 크기: 약 15-20 MB
Test-Path 결과: True
```

---

## 📦 Step 3: 배포 패키지 준비 (5분)

### 3-1. 배포 폴더 생성

**PowerShell에서 실행:**

```powershell
# 배포용 폴더 생성
mkdir dist\AI분석서배포
```

### 3-2. 파일 복사

**방법 A: 간편한 폴더 복사 (권장)**
```powershell
# 1. exe 파일 복사
Copy-Item .\dist\AI분석서생성.exe .\dist\AI분석서배포\

# 2. 전체 multi-agent 폴더 복사 (필요없는 폴더는 나중에 삭제 가능)
Copy-Item . .\dist\AI분석서배포\multi-agent\ -Recurse -Exclude .git, .venv, __pycache__, .pytest_cache, *.pyc, build, htmlcov

Write-Host "✓ 복사 완료"
```

**방법 B: 필수 파일만 선택해서 복사 (상세)**
```powershell
# 1. exe 파일 복사
Copy-Item .\dist\AI분석서생성.exe .\dist\AI분석서배포\

# 2. 필수 파일 복사
$files = @('docker-compose.yml', '.env.offline', 'Dockerfile', 'requirements.txt', 
           'config.py', 'database.py', 'orchestrator.py', 'app.py', 'main.py')
foreach ($file in $files) {
    Copy-Item $file .\dist\AI분석서배포\multi-agent\ -ErrorAction SilentlyContinue
}

# 3. 필수 폴더 복사
$folders = @('scripts', 'agents', 'utils', 'static')
foreach ($folder in $folders) {
    Copy-Item $folder .\dist\AI분석서배포\multi-agent\ -Recurse -ErrorAction SilentlyContinue
}

Write-Host "✓ 복사 완료"
```

### 3-3. 폴더 확인

```powershell
# 1. 배포 폴더 구조 확인
ls -lh dist\AI분석서배포\

# 2. 폴더 내용 확인
ls -lh dist\AI분석서배포\multi-agent\ | head -10

# 3. 전체 폴더 크기 확인 (GB 단위)
$size = (Get-ChildItem .\dist\AI분석서배포\ -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "전체 크기: $([math]::Round($size, 2)) GB"
```

**예상 결과:**
```
ls 결과:
Mode                 LastWriteTime         Length Name
----                 ---------------         ------ ----
-a---         2026-04-05    12:51       20000000 AI분석서생성.exe
d----         2026-04-05    12:52              . multi-agent

multi-agent 폴더 내용:
Mode                 LastWriteTime         Length Name
----                 ---------------         ------ ----
d----         2026-04-05    12:52              agents
d----         2026-04-05    12:52              scripts
d----         2026-04-05    12:52              static
d----         2026-04-05    12:52              utils
-a---         2026-04-05    12:51           2000 app.py
-a---         2026-04-05    12:51           1000 config.py

전체 크기: 약 3-4 GB
```

### 3-4. ZIP 압축 (선택사항)

```powershell
# 배포 패키지 ZIP으로 압축
Compress-Archive -Path .\dist\AI분석서배포 -DestinationPath .\dist\AI분석서배포.zip -Force

# 압축 파일 확인
ls -lh .\dist\AI분석서배포.zip
```

---

## 🧪 Step 4: exe 실행 테스트 (5분)

### 4-1. 테스트 폴더 준비

```powershell
# 1. 테스트 폴더 생성 (오프라인 환경 시뮬레이션)
mkdir C:\Test-AI분석서
cd C:\Test-AI분석서

# 2. 배포 파일 복사 (본인의 실제 경로로 변경)
# 예시: C:\AI분석서\multi-agent\dist\AI분석서배포\ 또는
#       C:\Projects\multi-agent\dist\AI분석서배포\

# PowerShell에서 (경로를 실제 경로로 변경하세요):
Copy-Item "C:\AI분석서\multi-agent\dist\AI분석서배포\*" .\ -Recurse

# 또는
Copy-Item "C:\Projects\multi-agent\dist\AI분석서배포\*" .\ -Recurse

# 3. 파일 확인
ls -Name
# 예상: AI분석서생성.exe, multi-agent
```

### 4-2. exe 파일 실행

**3가지 방법:**

**방법 A: 더블클릭 (가장 간단)**
```
C:\Test-AI분석서\AI분석서생성.exe 를 더블클릭
```

**방법 B: PowerShell에서 실행**
```powershell
.\AI분석서생성.exe
```

**방법 C: 명령 프롬프트에서 실행**
```cmd
AI분석서생성.exe
```

### 4-3. 자동 실행 과정 확인

**exe를 실행하면 자동으로:**

```
╔════════════════════════════════════════════╗
║  AI 개발 분석서 생성 - 오프라인 환경      ║
╚════════════════════════════════════════════╝

[1/5] Docker 설치 확인...
  ✓ Docker version 24.0.0

[2/5] Docker Compose 확인...
  ✓ Docker Compose version 2.20.0

[3/5] 구성 파일 확인...
  ✓ docker-compose.yml 확인

[4/5] 서비스 시작...
  → 기존 컨테이너 정리 완료
  → Docker Compose 시작 중...
  ✓ Docker Compose 시작 완료
  → 서버 시작 대기 중... 완료!
  ✓ 브라우저 오픈: http://localhost:8000

[5/5] 실시간 로그 모니터링...
  
  (이후 콘솔 창에 실시간 로그 표시)
```

### 4-4. 웹 브라우저 확인

**자동으로 브라우저가 열리지 않으면:**

1. 웹 브라우저 수동 오픈 (Chrome, Edge 등)
2. 주소 입력: `http://localhost:8000`
3. 다음 화면이 보여야 함:

```
┌─────────────────────────────────────────┐
│  AI 개발 분석서 생성 - 오프라인 환경    │
├─────────────────────────────────────────┤
│                                         │
│  📄 분석   🗂️ 프로젝트   🔍 소스 비교  │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 텍스트 입력 또는 파일 업로드      │ │
│  │                                   │ │
│  │ [분석 시작] 버튼                  │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### 4-5. 분석 테스트

**텍스트 입력:**
```
"기존 게시판에 파일 첨부 기능을 추가하려고 합니다"
```

**분석 시작 버튼 클릭 후:**
- 실시간 진행 상황 표시
- 약 30-60초 후 분석 완료
- 마크다운 결과 표시

---

## ✅ 배포 성공 체크리스트

### 빌드 성공 확인
- [ ] `dist\AI분석서생성.exe` 파일 존재
- [ ] 파일 크기: 15-20MB
- [ ] 파일이 실행 가능 (.exe 확장자)

### 배포 패키지 확인
- [ ] `dist\AI분석서배포\` 폴더 생성
- [ ] `AI분석서생성.exe` 포함
- [ ] `multi-agent\` 폴더 포함
- [ ] `docker-compose.yml` 포함
- [ ] `.env.offline` 포함
- [ ] 전체 크기: 2-3GB

### exe 실행 테스트
- [ ] exe 더블클릭 시 콘솔 창 오픈
- [ ] Docker 설치 확인 메시지
- [ ] "Docker Compose 시작 완료" 메시지
- [ ] 브라우저 자동 오픈 또는 수동으로 http://localhost:8000 접속
- [ ] 웹 페이지 정상 표시
- [ ] 분석 기능 정상 작동

---

## 🚀 배포 완료 후

### 고객에게 전달할 것

**방법 1: ZIP 파일**
```
dist\AI분석서배포.zip (약 2-3GB)
├─ 설명: "이 파일을 압축 해제하고 exe를 더블클릭하면 됩니다"
└─ 설치 가이드: WINDOWS_EXE_GUIDE.md 함께 제공
```

**방법 2: 폴더**
```
dist\AI분석서배포\ (약 2-3GB)
├─ USB, 클라우드, 웹사이트에서 다운로드 가능하게
└─ 설치 가이드: WINDOWS_EXE_GUIDE.md 함께 제공
```

### 고객이 할 일
1. ZIP 압축 해제 (또는 폴더 복사)
2. `AI분석서생성.exe` 더블클릭
3. 자동으로 모든 게 시작!

---

## ❓ 문제 해결

### 문제 1: "docker: 찾을 수 없습니다" 오류

**증상:**
```
docker: command not found
또는
'docker' is not recognized as an internal or external command
```

**해결:**
1. Docker Desktop 설치 확인
2. Docker Desktop 애플리케이션 실행
3. 잠깐 대기 (시작 시간 필요)
4. PowerShell 새로 열기
5. 다시 시도

### 문제 2: "Python: 찾을 수 없습니다" 오류

**증상:**
```
python: command not found
'python' is not recognized
```

**해결:**
1. Python 재설치 (PATH 확인)
2. PowerShell 재시작
3. `python --version` 다시 확인

### 문제 3: exe 빌드 실패

**증상:**
```
✗ exe 파일 생성 실패
또는 PyInstaller 오류
```

**해결:**
1. PyInstaller 재설치:
   ```powershell
   pip install --upgrade pyinstaller
   ```
2. 빌드 폴더 정리:
   ```powershell
   rm -Force -Recurse build, dist
   ```
3. 다시 빌드 시도

### 문제 4: "포트 8000이 이미 사용 중" 오류

**증상:**
```
Ports are not available
Error response from daemon
```

**해결:**
1. 기존 컨테이너 중지:
   ```powershell
   docker-compose down
   ```
2. 또는 포트 변경 (`.env` 파일에서 `PORT=8080` 로 변경)

---

## 📊 예상 시간

| 단계 | 시간 | 누적 |
|------|------|------|
| Python/Docker 확인 | 2-3분 | 2-3분 |
| 프로젝트 복사 | 3-5분 | 5-8분 |
| PyInstaller 설치 | 1-2분 | 6-10분 |
| exe 빌드 | 5-10분 | 11-20분 |
| 배포 패키지 준비 | 5분 | 16-25분 |
| exe 실행 테스트 | 5-10분 | 21-35분 |

**총 소요 시간: 약 30-40분**

---

## 🎉 완료!

이제 `dist\AI분석서배포\` 폴더가 배포 준비된 상태입니다.

다음 선택지:
1. **ZIP으로 압축해서 배포** (권장)
2. **USB에 복사해서 배포**
3. **클라우드에 업로드해서 공유**
4. **웹사이트에서 다운로드 가능하게 설정**

---

## 💡 다음 단계

1. **배포 파일 저장**
   ```powershell
   mkdir C:\Deploy
   Copy-Item .\dist\AI분석서배포.zip C:\Deploy\
   ```

2. **설치 가이드 동봉**
   - WINDOWS_EXE_GUIDE.md 복사
   - ZIP 파일과 함께 제공

3. **고객 배포**
   - ZIP + 가이드 전달
   - 고객이 exe 더블클릭하면 끝!

---

**모든 단계를 완료했으면 이 문서에서 ✅ 체크리스트를 확인하세요!**
