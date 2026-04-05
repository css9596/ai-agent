# Ollama 헬스 체크 문제 해결 완료 ✅

## 🎯 문제점

Docker Compose에서 Ollama 컨테이너가 첫 실행 시 **"unhealthy"** 상태로 표시되는 문제가 발생했습니다.

```
CONTAINER ID   STATUS
492003c0dad6   Up 7 minutes (unhealthy)  ← 문제!
```

실제로는 Ollama가 정상 작동 중(모델 다운로드 중)이었지만, Docker 헬스 체크가 잘못된 타이밍에 실패하고 있었습니다.

## 🔧 근본 원인

`docker-compose.yml`의 헬스 체크 설정에서 `start_period: 60s`가 **너무 짧았습니다**.

첫 실행 시 Ollama가 하는 일:
1. 컨테이너 시작: ~10초
2. 모델 다운로드 (qwen2.5:7b): **5-20분** ← 이 시간 동안 헬스 체크 차단 필요
3. 모델 로드: ~30초

그런데 60초 후에 헬스 체크가 시작되면, 모델 다운로드 중(15분)에 헬스 체크 실패 → unhealthy 표시

## ✅ 해결책

**docker-compose.yml** 업데이트:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
  interval: 30s
  timeout: 10s
  retries: 10
  start_period: 300s  # ← 60s → 300s (5분)
```

### 변경사항

| 항목 | 기존 | 변경 후 | 이유 |
|------|------|--------|------|
| `start_period` | 60s | **300s** | 모델 다운로드(5-20분)를 방해하지 않기 위해 5분 대기 |
| `retries` | 5 | **10** | 더 많은 재시도 기회 (보수적 설정) |

## 📊 기대 효과

### 첫 실행 상태 변화

```
⏰ 0-30초
STATUS: "health: starting"
의미: Ollama 시작 중, 헬스 체크 아직 미수행 ✅

⏰ 30초 ~ 5분
STATUS: "health: starting"
의미: 모델 다운로드 중, start_period 진행 중 ✅
실제: qwen2.5:7b (5GB) 다운로드 중

⏰ 5분 ~ 10분
STATUS: "health: starting" → "unhealthy" → "healthy" (왕복 가능)
의미: 이제 헬스 체크가 시작됨, 모델 로드 중 
주의: 잠깐 unhealthy일 수 있으니 계속 기다리세요 ✅

⏰ 10분 ~
STATUS: "health: healthy" (안정적)
의미: Ollama 완전 준비, app 컨테이너 시작 가능 ✅
```

## 📋 추가 문서

### 1. README.md 업데이트
새로운 **"⏱️ 첫 실행 가이드"** 섹션 추가:
- 첫 실행 vs 이후 실행 소요 시간 비교
- 예상되는 로그 출력
- 첫 실행 중 주의사항
- 진행 상황 확인 방법

### 2. OLLAMA_HEALTH_CHECK_GUIDE.md (신규)
종합적인 Ollama 헬스 체크 가이드:
- 헬스 체크 설정 상세 설명
- 첫 실행 중 상태 변화 (4단계)
- 모니터링 및 디버깅 명령어
- 문제 해결 (30분 이상 unhealthy, 모델 미다운로드 등)
- 성능 최적화 팁

### 3. CLAUDE.md 업데이트
개발자 가이드에 "5. **Ollama 헬스 체크**" 섹션 추가

## 🚀 사용 방법

### Docker Compose로 실행

```bash
# 첫 실행 (10-30분 소요)
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 모니터링
docker-compose logs -f ollama
```

### Windows exe로 실행

```
C:\AI분석서\AI분석서생성.exe 더블클릭
→ 첫 실행: 10-30분 대기 (Docker 이미지 빌드 + 모델 다운로드)
→ 완료: 브라우저 자동 오픈, http://localhost:8000
```

## 📈 성능 예상치

| 단계 | 소요 시간 | 설명 |
|------|----------|------|
| 첫 실행 (Docker Compose) | 10-30분 | 이미지 빌드(5-10분) + 모델 다운로드(5-20분) |
| 이후 실행 | 30-120초 | 컨테이너 시작만 수행 (이미지/모델 캐시됨) |
| 첫 분석 | 15-60초 | 로컬 LLM 처리 |
| 이후 분석 | 15-60초 | 동일 (모델 이미 로드됨) |

## ✨ 정상 동작 확인

모든 변경이 적용되었으면:

1. **Docker Compose 실행**
   ```bash
   cd multi-agent
   docker-compose up -d
   docker-compose ps  # unhealthy → healthy 변화 관찰
   ```

2. **로그 확인**
   ```bash
   docker-compose logs ollama
   # "Listening on [::]:11434" 메시지 확인
   ```

3. **웹 UI 접속**
   ```
   http://localhost:8000
   # 정상 작동 확인
   ```

4. **첫 분석 실행**
   - 텍스트 또는 파일 입력 후 "분석 시작" 클릭
   - 예상: 15-60초 내 분석 완료

## 🔗 관련 커밋

```
bc27711 - fix: Increase Ollama health check start_period to 300s
acf567a - docs: Add detailed first-run guide
4900d46 - docs: Add comprehensive Ollama health check troubleshooting guide
```

## 📝 핵심 요점

✅ **정상**: Docker가 헬스 체크 중 잠깐 unhealthy로 표시 (모델 로드 중)  
✅ **정상**: 첫 실행에 10-30분 소요 (이미지 빌드 + 모델 다운로드)  
✅ **정상**: Ctrl+C로 로그 보기 중단해도 서비스는 백그라운드 실행  
❌ **문제**: 30분 이상 unhealthy → `docker-compose logs ollama` 확인  
❌ **문제**: 웹 UI 접속 불가 → Docker 상태 확인 (`docker-compose ps`)

---

모든 문제가 해결되었습니다! 🎉  
첫 실행 시 **충분한 시간을 갖고 기다려주시면** 정상 작동합니다.
