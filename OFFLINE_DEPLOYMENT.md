# 오프라인 환경 배포 가이드

온라인 환경이 없는 폐쇄망에서 이 AI 개발 분석서 생성 프로그램을 사용하기 위한 완벽한 가이드입니다.

---

## 📋 개요

### 배포 흐름
```
[온라인 환경에서 1회 준비]          [오프라인 환경에서 사용]
setup-offline.sh/bat  ──→ 배포 패키지  ──→ docker-compose up -d
  ↳ CDN 다운로드                      ↳ http://localhost:8000
  ↳ pip 패키지 다운로드
  ↳ Docker 이미지 빌드
  ↳ Ollama 모델 다운로드
```

### 포함된 것
- ✅ **Tailwind CSS**: 완전한 UI 스타일
- ✅ **Font Awesome**: 모든 아이콘 (webfonts 포함)
- ✅ **marked.js**: Markdown 렌더링
- ✅ **pip 패키지**: 모든 Python 의존성
- ✅ **Ollama LLM**: 무료 오픈소스 AI 모델 (로컬 실행)
- ✅ **Docker Compose**: 전체 시스템 자동 구성

### 시스템 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| CPU | 2코어 | 4코어+ |
| RAM | 8GB | 16GB+ |
| 디스크 | 20GB | 50GB+ |
| OS | Windows 10/11, macOS, Linux | 최신 버전 |
| Docker | Desktop (v4.0+) | 최신 버전 |

---

## 🚀 1단계: 온라인 환경에서 준비 (1회성)

### 1-1. 필수 소프트웨어 설치

**macOS/Linux:**
```bash
# Docker Desktop
# https://www.docker.com/products/docker-desktop 에서 다운로드

# curl 확인 (보통 기본 설치)
curl --version
```

**Windows:**
1. Docker Desktop 다운로드: https://www.docker.com/products/docker-desktop
2. 설치하고 실행 (`C:\Program Files\Docker\Docker\Docker Desktop.exe`)
3. Docker Desktop 실행 상태 확인 (시스템 트레이에서 Docker 아이콘 확인)

### 1-2. 배포 패키지 준비

**macOS/Linux:**
```bash
cd multi-agent

# 스크립트 실행 권한 확인
chmod +x scripts/setup-offline.sh

# 설정 스크립트 실행 (5-10분 소요)
./scripts/setup-offline.sh
```

**Windows:**
1. `multi-agent` 폴더 열기
2. `scripts\setup-offline.bat` 더블클릭 또는
   ```cmd
   cd multi-agent
   scripts\setup-offline.bat
   ```

### 1-3. 생성된 배포 패키지 확인

스크립트 완료 후 다음 폴더들이 생성됩니다:

```
multi-agent/
├── static/vendor/            # 로컬화된 UI 라이브러리 (~1.5GB)
│   ├── tailwind.min.css
│   ├── marked.min.js
│   └── fontawesome/
│       ├── css/
│       └── webfonts/
├── packages/                 # pip wheel 파일들 (~150-200MB)
│   └── *.whl
├── .env                      # 자동 생성된 환경 파일
├── Dockerfile               # Docker 빌드 파일
├── docker-compose.yml       # Docker Compose 설정
└── scripts/                 # 설치 스크립트
```

**크기**: 약 **2-3GB** (모델 다운로드 포함 시 5-10GB 추가)

### 1-4. 배포 패키지 전달

**통째로 전달:**
```bash
# multi-agent 폴더 전체를 ZIP으로 압축
zip -r multi-agent-offline.zip multi-agent/

# 또는 폴더 복사 (USB, 네트워크 드라이브 등)
cp -r multi-agent/ /mnt/usb/multi-agent-offline/
```

---

## 💻 2단계: 오프라인 환경에서 실행

### 2-1. 배포 패키지 복사

받은 `multi-agent` 폴더를 원하는 위치에 저장합니다.

```bash
# 예: C:\Program Files\ 또는 /opt/ 등
```

### 2-2. Docker Compose 시작

**모든 OS:**
```bash
cd multi-agent

# 서비스 시작 (app + Ollama)
docker-compose up -d

# 잠깐 대기 (서비스 시작, 10-20초 소요)
sleep 30

# 상태 확인
docker-compose ps
```

**상태 확인 결과 예상:**
```
NAME                    STATUS              PORTS
multi-agent-app         Up 2 minutes        0.0.0.0:8000->8000/tcp
multi-agent-ollama      Up 2 minutes        0.0.0.0:11434->11434/tcp
```

### 2-3. 웹 브라우저에서 접속

```
http://localhost:8000
```

**UI 확인 사항:**
- ✅ 아이콘 표시됨 (Font Awesome)
- ✅ 스타일 정상 (Tailwind CSS)
- ✅ 로고, 버튼 표시됨

### 2-4. 기본 기능 테스트

**분석 탭에서:**
```
텍스트 입력: "기존 게시판에 파일 첨부 기능을 추가하고 싶습니다"
분석 시작 버튼 클릭
→ 실시간 진행 상황 표시
→ 약 30-60초 후 분석 완료
→ Markdown 결과 표시
```

---

## 🔧 3단계: 설정 변경

### 모델 변경

`.env` 파일 수정 (선택 사항):

```ini
# 모델 옵션:
# - qwen2.5:7b       (권장, 5GB RAM)
# - llama3.2:3b      (저사양, 2.5GB RAM)
# - llama3.3:70b     (고사양, 40GB RAM)

LLM_MODEL=qwen2.5:7b
```

변경 후 재시작:
```bash
docker-compose restart app
```

### 포트 변경

`.env` 파일 수정:
```ini
PORT=8080  # 기본값 8000에서 변경
```

`docker-compose.yml` 수정:
```yaml
ports:
  - "8080:8000"  # 왼쪽이 호스트 포트, 오른쪽이 컨테이너 포트
```

재시작:
```bash
docker-compose up -d
```

---

## 📊 4단계: 모니터링 및 관리

### 로그 확인

```bash
# 실시간 로그 보기
docker-compose logs -f app

# Ollama 로그 확인
docker-compose logs -f ollama

# 특정 시간 로그
docker-compose logs app --tail 100
```

### 성능 확인

```bash
# 컨테이너 리소스 사용량
docker stats

# 디스크 사용량
docker system df

# Ollama 모델 확인
curl http://localhost:11434/api/tags | python3 -m json.tool
```

### 데이터베이스 확인

분석 이력은 `analysis_history.db`에 저장됩니다:
```bash
ls -lh analysis_history.db
```

분석 결과는 `output/` 폴더에 저장됩니다:
```bash
ls -lh output/
```

---

## 🛠️ 5단계: 유지보수

### 서비스 재시작

```bash
# 전체 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart app
docker-compose restart ollama
```

### 로그 정리

```bash
# Docker 로그 정리 (오래된 로그)
docker system prune -a

# 분석 이력 삭제 (180일 이상)
# → 자동으로 매일 실행됨 (config.py의 RETENTION_DAYS)
```

### 새 모델 추가

```bash
# 새로운 모델 다운로드
docker-compose run --rm ollama ollama pull llama3.3:70b

# 또는 대화형으로
docker-compose exec ollama ollama pull llama3.3:70b

# .env 파일에서 LLM_MODEL 변경
# docker-compose restart app
```

---

## 📋 6단계: 문제 해결

### 문제 1: 서버가 시작되지 않음

**증상:**
```
docker-compose ps에서 app이 Exit or Restarting
```

**해결:**
```bash
# 로그 확인
docker-compose logs app --tail 50

# 문제 발생 시 재빌드
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### 문제 2: Ollama가 모델을 로드하지 못함

**증상:**
```
분석 시 오류: "ollama connection failed"
```

**해결:**
```bash
# Ollama 재시작
docker-compose restart ollama

# 모델 다시 다운로드
docker-compose run --rm ollama ollama pull qwen2.5:7b

# Ollama 상태 확인
curl http://localhost:11434/api/tags
```

### 문제 3: 웹페이지 스타일이 깨짐

**증상:**
```
아이콘이 안 보이거나, 색상이 이상함
```

**확인:**
```bash
# vendor 파일 확인
ls -lh static/vendor/

# 파일 누락 시 다시 다운로드
./scripts/setup-offline.sh
```

### 문제 4: 디스크 공간 부족

**확인:**
```bash
# 사용 중인 공간
docker system df -v

# 불필요한 이미지 제거
docker image prune -a

# 로그 정리
docker system prune -a
```

---

## 🌐 완전 에어갭 환경 (인터넷 완전 차단)

완전히 인터넷이 없는 환경이라면:

### 추가 준비 (온라인 환경에서)

```bash
# Docker 이미지 저장
docker pull python:3.9-slim ollama/ollama:latest
docker save python:3.9-slim ollama/ollama:latest -o docker-images.tar

# setup 스크립트가 생성한 배포 패키지와 함께 저장
# docker-images.tar를 multi-agent/ 폴더에 복사
```

### 오프라인 환경에서 로드

```bash
# 저장된 이미지 로드
docker load -i docker-images.tar

# 이후 docker-compose up -d 실행
```

---

## 📝 체크리스트

### 배포 준비 (온라인 환경)

- [ ] Docker Desktop 설치
- [ ] `scripts/setup-offline.sh` 또는 `.bat` 실행
- [ ] `static/vendor/` 폴더 생성 확인
- [ ] `packages/` 폴더 생성 확인
- [ ] `.env` 파일 생성 확인
- [ ] 배포 패키지 압축 또는 복사

### 배포 실행 (오프라인 환경)

- [ ] Docker Desktop 설치 및 실행
- [ ] `multi-agent` 폴더 복사
- [ ] `docker-compose up -d` 실행
- [ ] 컨테이너 상태 확인 (`docker-compose ps`)
- [ ] 웹 브라우저로 `http://localhost:8000` 접속
- [ ] UI 스타일 및 아이콘 확인
- [ ] 분석 기능 테스트

---

## 💡 팁

### 자동 정리

Docker Compose를 종료해도 데이터는 유지됩니다:
```bash
# 일시 중지 (데이터 보존)
docker-compose stop

# 재개
docker-compose start

# 완전 제거 (데이터 삭제)
docker-compose down -v
```

### 성능 최적화

`.env` 파일에서:
```ini
# 동시 분석 수 조정 (RAM에 따라)
MAX_CONCURRENT_ANALYSES=2  # 기본값, 더 적게 하면 RAM 절약

# 타임아웃 조정 (긴 분석이 필요하면)
ANALYSIS_TIMEOUT_MINUTES=60
```

### 백업

```bash
# 분석 결과 백업
cp -r output/ /mnt/backup/output-$(date +%Y%m%d)/

# 데이터베이스 백업
cp analysis_history.db /mnt/backup/analysis_history-$(date +%Y%m%d).db
```

---

## 📞 지원

### 명령어 빠른 참조

| 작업 | 명령어 |
|------|--------|
| 시작 | `docker-compose up -d` |
| 중지 | `docker-compose down` |
| 재시작 | `docker-compose restart` |
| 로그 | `docker-compose logs -f` |
| 상태 | `docker-compose ps` |
| 진입 | `docker-compose exec app bash` |

### 더 알아보기

- Docker Compose 문서: https://docs.docker.com/compose/
- Ollama 가이드: https://ollama.ai/
- 프로젝트 README: `README.md`

---

**배포 성공을 기원합니다! 🎉**

이 가이드에 문제가 있거나 추가 정보가 필요하면 프로젝트 저장소를 확인하세요.
