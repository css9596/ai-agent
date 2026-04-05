# exe 빌드 시뮬레이션 가이드

실제로 exe를 빌드하고 배포하는 전체 과정을 시뮬레이션합니다.

---

## 📋 체크리스트: 필요한 것들

### 1단계: 온라인 환경 준비 (exe 빌드)

#### 필수 확인 사항
```
✅ Python 3.9+
   확인: python --version 또는 python3 --version
   
✅ pip (Python 패키지 관리자)
   확인: pip --version 또는 pip3 --version
   
✅ PyInstaller (exe 빌드 도구)
   설치: pip install pyinstaller
   확인: pyinstaller --version
   
✅ Docker Desktop (최종 테스트용)
   확인: docker --version
   
✅ 인터넷 연결
   → PyInstaller 다운로드 필요
   → pip 패키지 설치 필요
```

#### 파일 확인
```
✅ scripts/run-app.py (메인 스크립트)
✅ scripts/build-exe.sh 또는 build-exe.ps1 (빌드 스크립트)
✅ docker-compose.yml (서비스 설정)
✅ .env.offline (환경 설정)
✅ static/ 폴더 (UI 파일)
```

---

### 2단계: exe 빌드

#### 방법 선택

**Option A: macOS/Linux (현재 권장)**
```bash
chmod +x scripts/build-exe.sh
./scripts/build-exe.sh
# 결과: dist/AI분석서생성.exe 생성
```

**Option B: Windows PowerShell**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1
# 결과: dist\AI분석서생성.exe 생성
```

**Option C: 직접 빌드**
```bash
pip install pyinstaller
python -m PyInstaller \
    --onefile \
    --name "AI분석서생성" \
    --console \
    scripts/run-app.py
```

#### 예상 결과
```
dist/
├── AI분석서생성.exe (10-15MB)  ✅ 생성됨!
└── ...

build/
├── run_app/
└── run_app.spec

(이 파일들은 빌드 후 배포에 불필요, 정리 가능)
```

#### 소요 시간
- PyInstaller 설치: 2-3분
- exe 빌드: 3-5분
- **총 5-10분**

---

### 3단계: 배포 패키지 준비

#### 폴더 구조 만들기

```bash
# 배포용 폴더 생성
mkdir dist/AI분석서배포

# exe 복사
cp dist/AI분석서생성.exe dist/AI분석서배포/

# 전체 multi-agent 폴더 복사
cp -r . dist/AI분석서배포/multi-agent/
# (또는 별도 폴더에 수동으로 복사)

# 최종 구조
dist/AI분석서배포/
├── AI분석서생성.exe (10-15MB)
└── multi-agent/
    ├── docker-compose.yml
    ├── .env.offline
    ├── Dockerfile
    ├── static/
    ├── agents/
    ├── utils/
    └── ... (모든 폴더/파일)

# 크기 확인
du -sh dist/AI분석서배포/
# 예상: 2-3GB
```

---

### 4단계: 배포 파일 준비

#### 옵션 1: ZIP 압축 (권장)
```bash
cd dist
zip -r AI분석서배포.zip AI분석서배포/
# 결과: AI분석서배포.zip (2-3GB)

# 압축 확인
unzip -l AI분석서배포.zip | head -20
```

#### 옵션 2: 폴더 직접 배포
```bash
# 폴더 전체를 USB에 복사 또는 클라우드 업로드
cp -r dist/AI분석서배포/ /mnt/usb/
```

---

### 5단계: 오프라인 환경 시뮬레이션

#### 시뮬레이션 환경 준비

```bash
# 새로운 테스트 폴더 생성 (오프라인 환경 시뮬레이션)
mkdir -p ~/test-offline/AI분석서

# 배포 파일 복사
cp -r dist/AI분석서배포/multi-agent ~/test-offline/AI분석서/
cp dist/AI분석서배포/AI분석서생성.exe ~/test-offline/AI분석서/

# 폴더 구조 확인
ls -la ~/test-offline/AI분석서/
```

#### exe 실행 테스트

```bash
# 테스트 폴더로 이동
cd ~/test-offline/AI분석서

# exe 실행 (macOS/Linux는 직접 실행 불가, 원본에서 테스트)
# Windows라면:
#   AI분석서생성.exe 더블클릭 또는 명령어 실행

# 또는 Python 스크립트로 직접 테스트
python /path/to/scripts/run-app.py
```

---

## 🔧 시뮬레이션 단계별 실행

### Step 1: 환경 준비 확인

```bash
# 1. Python 버전 확인
python --version
# 필요: Python 3.9 이상

# 2. Docker 실행 확인
docker ps
# 필요: Docker Desktop이 실행 중

# 3. 현재 디렉토리 확인
pwd
# 필요: multi-agent 폴더 위치
```

### Step 2: exe 빌드

```bash
# 1. PyInstaller 설치
pip install pyinstaller

# 2. 빌드 스크립트 실행
chmod +x scripts/build-exe.sh
./scripts/build-exe.sh

# 3. 결과 확인
ls -lh dist/AI분석서생성.exe
file dist/AI분석서생성.exe
```

### Step 3: 배포 패키지 준비

```bash
# 1. 배포 폴더 구조 생성
mkdir -p dist/AI분석서배포
cp dist/AI분석서생성.exe dist/AI분석서배포/

# 2. multi-agent 폴더 복사 (불필요 파일 제외)
cp -r . dist/AI분석서배포/multi-agent/ \
    --exclude=.git \
    --exclude=build \
    --exclude=dist \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=htmlcov

# 3. 크기 확인
du -sh dist/AI분석서배포/

# 4. 구조 확인
tree -L 2 dist/AI분석서배포/ | head -30
```

### Step 4: 시뮬레이션 환경 구성

```bash
# 1. 테스트 폴더 생성
rm -rf ~/test-simulation
mkdir -p ~/test-simulation/AI분석서

# 2. 배포 파일 복사 (오프라인 환경 시뮬레이션)
cp -r dist/AI분석서배포/multi-agent ~/test-simulation/AI분석서/
cp dist/AI분석서배포/AI분석서생성.exe ~/test-simulation/AI분석서/

# 3. 폴더 확인
ls -la ~/test-simulation/AI분석서/
```

### Step 5: 시뮬레이션 실행

```bash
# 1. 테스트 폴더로 이동
cd ~/test-simulation/AI분석서

# 2. exe 없이 Python 스크립트로 테스트 (macOS/Linux)
python multi-agent/scripts/run-app.py

# 또는 docker-compose 직접 테스트
cd multi-agent
docker-compose up -d

# 3. 서비스 확인
docker-compose ps

# 4. 웹 접속 확인
curl http://localhost:8000/api/health

# 5. 종료
docker-compose down
```

---

## 📊 시뮬레이션 체크포인트

### 체크포인트 1: 빌드 완료
```
✅ dist/AI분석서생성.exe 파일 존재
✅ 파일 크기 10-15MB
✅ 파일 타입: PE 32-bit executable (Windows)
```

### 체크포인트 2: 패키지 준비 완료
```
✅ dist/AI분석서배포/ 폴더 생성
✅ AI분석서생성.exe 포함
✅ multi-agent/ 폴더 포함
✅ docker-compose.yml 포함
✅ .env.offline 포함
```

### 체크포인트 3: 배포 가능
```
✅ ZIP 파일 생성 (또는 폴더 복사)
✅ 파일/폴더 크기: 2-3GB
✅ 압축 무결성 확인
```

### 체크포인트 4: 시뮬레이션 성공
```
✅ 테스트 폴더에서 docker-compose 실행
✅ 컨테이너 정상 시작
✅ http://localhost:8000 응답
✅ 분석 기능 작동
```

---

## 🎯 시뮬레이션 결과

### 성공한 경우
```
✅ exe 파일이 정상적으로 생성됨
✅ 배포 패키지가 준비됨
✅ 오프라인 환경에서 docker-compose가 정상 작동
✅ 웹 인터페이스에 접속 가능
✅ 분석 기능이 정상 작동

→ 실제 배포 준비 완료!
```

### 실패한 경우
```
❌ exe 빌드 실패
   → PyInstaller 재설치
   → Python 버전 확인
   → 스크립트 경로 확인

❌ 패키지 크기가 너무 작음
   → multi-agent 폴더 복사 확인
   → 필수 파일 누락 확인

❌ docker-compose 실행 실패
   → Docker Desktop 실행 확인
   → docker-compose.yml 파일 확인
   → .env.offline 파일 확인

❌ 웹 접속 불가
   → 포트 충돌 확인
   → 방화벽 확인
   → Ollama 서비스 상태 확인
```

---

## 💾 시뮬레이션 후 정리

### 임시 파일 제거 (선택사항)
```bash
# build 폴더 정리 (재빌드 하려면 유지)
rm -rf build/

# 테스트 폴더 정리
rm -rf ~/test-simulation/

# dist 폴더 정리 (배포 필요 없으면)
# rm -rf dist/
```

### 배포 파일 저장
```bash
# 배포용 파일만 보관
mkdir -p ~/deploy
cp dist/AI분석서배포.zip ~/deploy/
# 또는
cp -r dist/AI분석서배포/ ~/deploy/
```

---

## 📝 시뮬레이션 체크리스트

### 사전 준비
- [ ] Python 3.9+ 설치 확인
- [ ] pip 설치 확인
- [ ] Docker Desktop 설치 확인
- [ ] 인터넷 연결 확인
- [ ] 현재 multi-agent 폴더 위치 확인

### exe 빌드
- [ ] PyInstaller 설치
- [ ] build-exe.sh 실행 권한 확인
- [ ] 빌드 스크립트 실행
- [ ] dist/AI분석서생성.exe 생성 확인
- [ ] 파일 크기 10-15MB 확인

### 패키지 준비
- [ ] dist/AI분석서배포/ 폴더 생성
- [ ] exe 파일 복사
- [ ] multi-agent 폴더 복사
- [ ] 필수 파일 포함 확인 (docker-compose.yml, .env.offline)
- [ ] 전체 크기 2-3GB 확인

### 배포 파일
- [ ] ZIP 압축 (또는 폴더 복사)
- [ ] 압축 무결성 확인
- [ ] 배포 위치 결정 (USB, 클라우드, 웹)

### 오프라인 시뮬레이션
- [ ] 테스트 폴더 생성
- [ ] 배포 파일 복사
- [ ] Python 스크립트로 테스트
- [ ] docker-compose up -d 실행
- [ ] 컨테이너 상태 확인
- [ ] http://localhost:8000 응답 확인
- [ ] 분석 기능 테스트

### 최종 정리
- [ ] 불필요한 파일 제거 (선택사항)
- [ ] 배포 파일 저장 위치 확정
- [ ] 배포 방법 결정 (USB, 이메일, 웹 등)

---

## 🚀 시뮬레이션 시작!

위 체크리스트를 따라 진행하면 실제로 exe 빌드부터 배포까지 전체 과정을 경험할 수 있습니다.

**예상 소요 시간**: 30-45분
- PyInstaller 설치: 2-3분
- exe 빌드: 3-5분
- 패키지 준비: 5-10분
- 시뮬레이션: 10-15분
- 정리: 5분

**성공하면**:
✅ 실제 배포를 위한 완벽한 패키지 준비 완료
✅ 고객에게 배포 가능한 상태
✅ exe 작동 확인 완료

**추가 질문 있으면**:
- exe 빌드 중 오류 발생?
- 특정 단계에서 막혔나?
- 다른 방식의 배포를 원하나?
