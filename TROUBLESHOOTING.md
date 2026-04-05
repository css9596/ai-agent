# 종합 트러블슈팅 가이드

**마지막 업데이트**: 2026-04-06

---

## 📋 목차

1. [설치 단계 문제](#설치-단계-문제)
2. [Docker 문제](#docker-문제)
3. [웹 UI 문제](#웹-ui-문제)
4. [분석 실행 문제](#분석-실행-문제)
5. [성능 문제](#성능-문제)
6. [오프라인 환경 문제](#오프라인-환경-문제)

---

## 설치 단계 문제

### 문제 1: Docker Desktop 설치 후 실행 안 됨

**증상**:
```
docker: command not found
또는
Docker Desktop이 실행되지 않음
```

**해결 방법**:

**Mac**:
```bash
# 1. 설치 확인
ls /Applications/Docker.app

# 2. Docker 시작
open /Applications/Docker.app

# 3. 아이콘이 메뉴바에 나타날 때까지 대기 (약 30초)

# 4. 확인
docker --version
```

**Windows**:
```powershell
# 1. 설치 확인
ls "C:\Program Files\Docker"

# 2. Docker Desktop 시작 (시작 메뉴)
# 또는 PowerShell: & "C:\Program Files\Docker\Docker\Docker for Windows.exe"

# 3. 아이콘이 시스템 트레이에 나타날 때까지 대기

# 4. 확인
docker --version
```

### 문제 2: git pull 후 충돌

**증상**:
```
error: Your local changes to the following files would be overwritten by merge
```

**해결 방법**:
```bash
# 방법 1: 변경사항 버리기 (주의!)
git reset --hard HEAD
git pull

# 방법 2: 변경사항 저장
git stash
git pull
git stash pop

# 방법 3: 현재 브랜치 삭제 후 다시 클론
cd ..
rm -rf multi-agent
git clone <url>
```

---

## Docker 문제

### 문제 1: 컨테이너가 계속 restart 상태

**증상**:
```
STATUS: "Restarting (1) 5 seconds ago"
또는 "health: unhealthy"
```

**해결 방법**:

**Step 1**: 로그 확인
```bash
docker-compose logs app | head -50
docker-compose logs ollama | head -50
```

**Step 2**: 문제별 해결

| 오류 | 원인 | 해결 |
|------|------|------|
| `unable to open database file` | data/ 디렉토리 없음 | `mkdir -p data/` |
| `model 'qwen2.5:7b' not found` | 모델 미다운로드 | `docker-compose exec ollama ollama pull qwen2.5:7b` |
| `Connection refused` | Ollama 미시작 | `docker-compose up -d --build` |
| `Disk quota exceeded` | 디스크 부족 | `docker system prune -a` |

**Step 3**: 강제 재시작
```bash
# 모든 컨테이너 정지
docker-compose down

# 캐시 완전 삭제
docker system prune -a -f --volumes

# 재빌드
docker-compose up -d --build
```

### 문제 2: "pull access denied" 오류

**증상**:
```
pull access denied for multi-agent-app
```

**원인**: Docker 이미지가 로컬에 없고, Docker Hub에서도 찾지 못함

**해결 방법**:
```bash
# 이미지 빌드 (중요!)
docker-compose build --no-cache

# 또는
docker-compose up -d --build
```

### 문제 3: 포트가 이미 사용 중

**증상**:
```
Ports are not available: exposing port UDP 0.0.0.0:8000 -> 0.0.0.0:0
```

**해결 방법**:

**Mac/Linux**:
```bash
# 포트 8000을 사용하는 프로세스 확인
lsof -i :8000

# 종료
kill -9 <PID>

# 또는 다른 포트 사용
PORT=8080 docker-compose up -d
```

**Windows PowerShell**:
```powershell
# 포트 8000을 사용하는 프로세스 확인
netstat -ano | findstr :8000

# 종료
taskkill /PID <PID> /F

# 또는 .env에서 변경
# PORT=8080
```

### 문제 4: Docker 이미지 크기 문제

**증상**:
```
no space left on device
또는 Docker 이미지가 너무 큼
```

**해결 방법**:
```bash
# 사용하지 않는 이미지 정리
docker image prune -a

# 모든 컨테이너/이미지/볼륨 정리 (주의!)
docker system prune -a -f --volumes

# 디스크 용량 확인
df -h  # Mac/Linux
dir C:\  # Windows
```

---

## 웹 UI 문제

### 문제 1: CSS가 로드되지 않음 (흰색 배경만)

**증상**:
```
- 배경색, 스타일 없음
- 텍스트만 보임
- 아이콘 안 보임
```

**원인**: 
- tailwind.min.css 로드 실패
- Font Awesome webfonts 없음
- 브라우저 캐시

**해결 방법**:

**Step 1**: 파일 확인
```bash
ls -la static/vendor/
# 다음 파일들이 있는지 확인:
# - tailwind.min.css (2.8MB 이상)
# - fontawesome/css/all.min.css
# - fontawesome/webfonts/*.woff2
```

**Step 2**: Docker 이미지 재빌드
```bash
docker-compose down
docker rmi multi-agent-app:offline
docker-compose up -d --build
```

**Step 3**: 브라우저 캐시 삭제
```
개발자 도구 (F12) → Network 탭 → "Disable cache" 체크
또는
Ctrl+Shift+Del (캐시 삭제)
새로고침 (Ctrl+F5)
```

### 문제 2: 헤더의 로고와 제목이 안 보임

**증상**:
```
- 헤더에 그라데이션만 있음
- 텍스트 없음
- 아이콘 없음
```

**원인**: text-gradient-primary CSS 미적용

**해결 방법**:
```bash
# 최신 코드 pull
git pull

# 브라우저 캐시 삭제
Ctrl+Shift+Del → 캐시 삭제 → 새로고침
```

### 문제 3: 헤더 배경이 투명하게 변함 (스크롤 시)

**증상**:
```
- 스크롤하면 헤더 배경이 투명해짐
- 텍스트가 겹침
```

**원인**: Tailwind v2 `bg-white/80` 미지원

**해결 방법**:
```bash
git pull  # 최신 CSS 반영
docker-compose restart app
브라우저 캐시 삭제 후 새로고침
```

### 문제 4: 파일 업로드 실패

**증상**:
```
- 파일을 선택해도 "선택된 파일 없음"
- 업로드 버튼이 비활성화됨
```

**원인**:
- 파일 크기 초과 (최대 10MB 클라이언트, 50MB 서버)
- 지원하지 않는 형식
- JavaScript 오류

**해결 방법**:

**Step 1**: 파일 확인
```
- 파일 크기: 10MB 미만
- 지원 형식: .txt, .md, .pdf, .xlsx, .pptx, .docx
```

**Step 2**: 브라우저 콘솔 확인
```
F12 → Console 탭 → 오류 메시지 확인
```

**Step 3**: marked.js 로드 확인
```bash
# 파일 존재 확인
ls -la static/vendor/marked.min.js

# 파일 크기 30KB 이상인지 확인
```

---

## 분석 실행 문제

### 문제 1: "model 'qwen2.5:7b' not found"

**증상**:
```
LLM API request failed: Error code: 404 - model 'qwen2.5:7b' not found
```

**원인**: Ollama에 모델이 없음 (아직 다운로드 중이거나 실패)

**해결 방법**:

**Step 1**: 모델 다운로드 상태 확인
```bash
docker-compose logs ollama | tail -50
# "Pulling" 문구가 있으면 다운로드 중
```

**Step 2**: 수동 다운로드
```bash
# 다운로드
docker-compose exec ollama ollama pull qwen2.5:7b

# 진행 상황 모니터링 (5-20분)
docker-compose logs -f ollama

# 완료 확인
docker-compose exec ollama ollama list
# qwen2.5:7b이 표시되면 성공
```

**Step 3**: 재시도
```
http://localhost:8000에서 다시 분석 시작
```

### 문제 2: "LLM API request failed after 3 attempts"

**증상**:
```
LLM API request failed after 3 attempts: Connection refused
또는 Timeout
```

**원인**:
- Ollama가 실행되지 않음
- Ollama 응답 느림
- 네트워크 문제

**해결 방법**:

**Step 1**: Ollama 상태 확인
```bash
docker-compose ps ollama
# STATUS: "Up (health: healthy)"인지 확인

# 또는 헬스 체크
curl http://localhost:11434/api/tags
```

**Step 2**: 시간 대기
```
- Ollama 시작 중: 30초 대기
- 모델 로드 중: 1-2분 대기
- 분석 중: 1-5분 대기
```

**Step 3**: 재시작
```bash
docker-compose restart ollama
docker-compose logs -f ollama
```

### 문제 3: 분석이 너무 느림

**증상**:
```
분석이 5분 이상 걸림
```

**원인**:
- 첫 분석: Ollama 모델 로드 (1-2분)
- CPU 부족: 4코어 미만
- RAM 부족: 8GB 미만
- 큰 입력 문서

**해결 방법**:

**Step 1**: 첫 분석은 기다리기
```
첫 분석: 1-2분 정상
이후 분석: 15-60초
```

**Step 2**: 더 작은 모델 사용
```bash
# .env 파일 수정
LLM_MODEL=llama3.2:3b  # 더 빠름, 2.5GB

# Ollama에서 다운로드
docker-compose exec ollama ollama pull llama3.2:3b

# Docker 재시작
docker-compose restart app
```

**Step 3**: 입력 문서 축소
```
- 짧은 텍스트로 테스트
- PDF 첫 몇 페이지만 업로드
- 핵심 내용만 입력
```

### 문제 4: Ollama가 응답하지 않음

**증상**:
```
curl http://localhost:11434/api/tags
→ Connection refused
```

**원인**:
- Ollama 컨테이너가 실행되지 않음
- Ollama 포트 11434 사용 중
- 메모리 부족

**해결 방법**:

**Mac/Linux**:
```bash
# 포트 확인
lsof -i :11434

# 프로세스 종료
kill -9 <PID>

# Ollama 재시작
docker-compose restart ollama
```

**Windows**:
```powershell
# 포트 확인
netstat -ano | findstr :11434

# 프로세스 종료
taskkill /PID <PID> /F

# Ollama 재시작
docker-compose restart ollama
```

---

## 성능 문제

### 문제 1: 메모리 부족

**증상**:
```
컨테이너가 자주 죽음
또는 시스템이 느려짐
```

**확인**:
```bash
# Docker 리소스 확인
docker stats

# 시스템 메모리 확인
free -h  # Linux
vm_stat | grep "Pages free"  # Mac
```

**해결 방법**:

**Option 1**: 더 작은 모델 사용
```
qwen2.5:7b (5GB) → llama3.2:3b (2.5GB)
```

**Option 2**: Docker 메모리 증가
```bash
# Docker Desktop에서 설정
Mac: Docker 아이콘 → Preferences → Resources → Memory: 16GB
Windows: Docker Desktop → Settings → Resources → Memory: 16GB
```

### 문제 2: 디스크 부족

**증상**:
```
"no space left on device"
```

**확인**:
```bash
df -h  # Mac/Linux
dir C:\  # Windows
```

**해결 방법**:

```bash
# 사용하지 않는 이미지 삭제
docker image prune -a

# 볼륨 삭제
docker volume prune

# 전체 정리
docker system prune -a -f --volumes
```

---

## 오프라인 환경 문제

### 문제 1: 오프라인 환경에서 CSS 미로드

**증상**:
```
CSS 없이 흰색 배경만 보임
JavaScript 오류: marked.min.js 로드 실패
```

**원인**: 로컬 CSS/JS 파일이 없음

**확인**:
```bash
ls -la static/vendor/
# 다음 파일들이 있는지 확인:
# - tailwind.min.css
# - fontawesome/
# - marked.min.js
```

**해결 방법**:
```bash
# 온라인 환경에서 파일 다운로드
curl -o static/vendor/tailwind.min.css https://cdn.jsdelivr.net/npm/tailwindcss@2/dist/tailwind.min.css

# 또는 git pull (이미 파일이 커밋됨)
git pull
```

### 문제 2: Docker 이미지 빌드 실패 (오프라인)

**증상**:
```
unable to pull image
또는 404 not found
```

**원인**: 온라인 환경에서 미리 빌드한 이미지가 없음

**해결 방법**:

**온라인 환경에서 (1회)**:
```bash
docker-compose up -d --build
# 이미지가 로컬에 저장됨
```

**오프라인 환경에서**:
```bash
# 이미 빌드된 이미지 사용
docker-compose up -d
# (rebuild 필요 없음)
```

### 문제 3: Ollama 모델 미다운로드 (오프라인)

**증상**:
```
model 'qwen2.5:7b' not found
```

**원인**: 온라인 환경에서 모델을 미리 다운로드하지 않음

**해결 방법**:

**온라인 환경에서 (1회)**:
```bash
docker-compose exec ollama ollama pull qwen2.5:7b
# 모델이 로컬 볼륨에 저장됨
```

**오프라인 환경에서**:
```bash
# 다시 다운로드 불가능 (인터넷 필요)
# 단, 온라인에서 미리 다운로드했다면:
docker-compose exec ollama ollama list
# 모델이 표시됨
```

---

## 더 도움이 필요하면?

1. **로그 확인**: `docker-compose logs -f app`
2. **DEPLOYMENT_COMPLETE.md**: 배포 가이드
3. **CLAUDE.md**: 아키텍처 및 개발 가이드
4. **GitHub Issues**: 버그 리포트

---

**트러블슈팅 완료!** 대부분의 문제는 이 가이드에서 해결할 수 있습니다. 🎯
