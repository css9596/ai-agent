# Ollama 헬스 체크 가이드

## 개요

Docker Compose가 Ollama 컨테이너의 상태를 모니터링하기 위해 헬스 체크를 수행합니다. 첫 실행 시 모델 다운로드 중에 헬스 체크가 실패하는 것은 **정상**입니다.

## 헬스 체크 설정 (docker-compose.yml)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
  interval: 30s
  timeout: 10s
  retries: 10
  start_period: 300s  # 첫 실행: 5분 대기 후 헬스 체크 시작
```

### 각 옵션의 의미

| 옵션 | 값 | 설명 |
|------|-----|------|
| `test` | `curl -f http://localhost:11434/api/tags` | Ollama `/api/tags` 엔드포인트 호출 |
| `interval` | 30s | 30초마다 헬스 체크 수행 |
| `timeout` | 10s | 응답 대기 시간 최대 10초 |
| `retries` | 10 | 최대 10회 실패 후 unhealthy (5분 = 10 * 30초) |
| `start_period` | 300s | 첫 5분간은 헬스 체크 보류 (모델 다운로드 시간 확보) |

## 첫 실행 중 상태 변화

### 1단계: 컨테이너 시작 (0-30초)

```
docker ps

STATUS
"30 seconds ago (health: starting)"
```

- 상태: `health: starting`
- 의미: 방금 시작됨, 아직 헬스 체크 미수행
- 조치: 기다리세요 ⏳

### 2단계: 모델 다운로드 (30초 ~ 5분)

```
STATUS
"2 minutes ago (health: starting)"
```

- 상태: 여전히 `health: starting`
- 의미: start_period (300s = 5분) 중이므로 헬스 체크 미수행
- 실제: Ollama가 qwen2.5:7b 모델 다운로드 중
- 확인: `docker-compose logs ollama` 에서 다운로드 진행률 확인
- 조치: 모델 다운로드를 방해하지 마세요 ⏳

### 3단계: 모델 다운로드 완료 (5분 ~ 10분)

```
STATUS
"7 minutes ago (unhealthy)" 또는 "7 minutes ago (healthy)"
```

- 상태: `healthy` 또는 `unhealthy` (시점마다 다름)
- 의미: 이제 헬스 체크가 시작됨 (start_period 종료)
- 실제: Ollama 시작 완료, 모델 로드 중 또는 준비됨
- 주의: 잠깐 unhealthy로 표시될 수 있음 (정상)
- 조치: 계속 기다리세요 ⏳

### 4단계: 완전 준비 (10분 ~ 15분)

```
STATUS
"10 minutes ago (healthy)"
```

- 상태: 안정적으로 `healthy`
- 의미: Ollama가 완전히 준비되고 응답 중
- app 컨테이너: 이제 올라올 수 있음
- 웹 UI: http://localhost:8000 접속 가능
- 조치: 분석 시작 가능 ✅

## 모니터링 및 디버깅

### Docker 상태 확인

```bash
# 전체 컨테이너 상태
docker-compose ps

# 상세 상태 (health 포함)
docker-compose ps --no-trunc

# 실시간 로그
docker-compose logs -f ollama
```

### 예상되는 로그 메시지

**정상 시작 로그**:
```
2026-04-06T12:00:00.000Z INFO Listening on [::]:11434 (version 0.20.2)
2026-04-06T12:00:05.000Z INFO Runners started in 5.2s
```

**모델 다운로드 중 로그**:
```
2026-04-06T12:00:10.000Z Pulling manifest...
2026-04-06T12:00:15.000Z Pulling 3a4fdf6f2a30... (1.2GB)
2026-04-06T12:00:20.000Z Pulling 5a4fdf6f2a30... (5.2GB)
...
2026-04-06T12:15:00.000Z Verifying SHA256 digest
2026-04-06T12:15:05.000Z SUCCESS
```

### 직접 엔드포인트 테스트

```bash
# 첫 실행 중 (모델 다운로드 중 또는 후)
curl -f http://localhost:11434/api/tags

# 응답 예시 (정상)
{
  "models": [
    {
      "name": "qwen2.5:7b",
      "modified_at": "2026-04-06T12:30:00.000Z",
      "size": 5240000000
    }
  ]
}

# 응답 실패 (모델 로드 중)
curl: (7) Failed to connect to localhost port 11434
```

## 문제 해결

### 문제 1: 30분 이상 unhealthy 상태

**증상**: 
```
STATUS
"35 minutes ago (unhealthy)"
```

**원인**:
- 디스크 공간 부족 (모델 다운로드 중단)
- 네트워크 끊김 (모델 다운로드 실패)
- CPU/메모리 부족 (Ollama 응답 지연)

**해결**:
```bash
# 로그 확인
docker-compose logs ollama | tail -100

# 디스크 여유 공간 확인
df -h

# 메모리 여유 확인
free -h  # 또는 top

# 컨테이너 재시작
docker-compose restart ollama
```

### 문제 2: app 컨테이너가 시작되지 않음

**증상**:
```
PORTS
포트 8000이 바인딩되지 않음
```

**원인**:
```yaml
depends_on:
  ollama:
    condition: service_healthy  # ← ollama가 healthy가 될 때까지 대기
```

app이 ollama의 `healthy` 상태를 기다리고 있음.

**해결**:
1. ollama가 healthy될 때까지 기다리기 (위의 4단계 참고)
2. 또는 docker-compose.yml에서 `condition` 제거 (권장하지 않음)

### 문제 3: Ollama 모델이 없음

**증상**:
```bash
docker-compose exec ollama ollama list
# 출력 없음 또는 빈 목록
```

**원인**:
- 모델 다운로드 미완료
- 다운로드 실패 후 재시도 없음

**해결**:
```bash
# 모델 명시적으로 다운로드
docker-compose exec ollama ollama pull qwen2.5:7b

# 또는 로그 확인해서 실패 원인 파악
docker-compose logs ollama | grep -i "error"
```

## 성능 최적화

### 모델 다운로드 속도 향상

1. **네트워크 대역폭 확인**
   ```bash
   # 현재 다운로드 속도 확인
   docker-compose logs ollama | grep -i "pulling"
   ```

2. **더 작은 모델 사용** (개발/테스트용)
   ```bash
   # .env에서 모델 변경
   LLM_MODEL=llama3.2:3b  # 2.5GB, 빠름
   LLM_MODEL=qwen2.5:7b   # 5GB, 균형 (기본)
   LLM_MODEL=llama3.3:70b # 40GB, 느리지만 정확
   ```

3. **모델 캐시 활용**
   - 첫 다운로드 후 `/root/.ollama` 볼륨에 저장됨
   - docker-compose down 해도 모델 유지됨 (볼륨이 영구 저장)
   - 다시 시작하면 캐시된 모델 사용 (빠름)

### 헬스 체크 커스터마이징

필요시 `docker-compose.yml`의 헬스 체크 설정을 조정:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
  interval: 30s      # 더 자주 체크: 10s, 덜 자주: 60s
  timeout: 10s       # 더 긴 timeout: 20s (느린 네트워크)
  retries: 10        # 더 많은 재시도: 20 (불안정한 환경)
  start_period: 300s # 더 긴 대기: 600s (느린 네트워크)
```

## 정상 vs 문제 상황

| 상황 | 상태 | 조치 |
|------|------|------|
| 시작 직후 | `health: starting` | 기다리세요 ✅ |
| 모델 다운로드 중 | `health: starting` (5분까지) | 기다리세요 ✅ |
| 모델 다운로드 중 | `health: unhealthy` (5-10분) | 정상, 기다리세요 ✅ |
| 완전 준비 | `health: healthy` (10분 후) | 시작 가능 ✅ |
| 30분 이상 unhealthy | `health: unhealthy` | 로그 확인, 재시작 ❌ |
| ollama 리소스 부족 | 응답 없음 | 메모리/디스크 확인 ❌ |

## 참고 문서

- `docker-compose.yml` - 헬스 체크 설정
- `README.md` - 첫 실행 가이드
- `CLAUDE.md` - 개발자 가이드
