# Phase 2: Important (운영 가능성) - 상세 구현 계획

## 목표
서버 모니터링과 기본 관리 기능 추가 → 운영 가능한 수준

---

## 구현 항목

### 2.1 로깅 시스템 ✅ (이미 구현됨)
**파일**: `utils/logger.py`

**기능**:
- JSON 형식 구조화된 로그
- 분석 시작/종료/실패 기록
- API 응답 시간 측정
- 로그 파일 자동 로테이션

**사용**:
```python
from utils.logger import logger

logger.analysis_start(analysis_id, file_name)
logger.analysis_complete(analysis_id, duration)
logger.analysis_error(analysis_id, error)
```

---

### 2.2 관리자 대시보드 (기본)
**파일**: `static/admin.html`

**기능**:
1. 시스템 통계
   - 일일/주간 분석 수
   - 성공률
   - 평균 분석 시간

2. 실시간 모니터링
   - 현재 실행 중인 분석
   - 대기 중인 작업
   - 최근 완료된 분석

3. 분석 이력 조회
   - 필터링 (상태, 날짜)
   - 검색
   - 상세 정보 조회

4. 로그 뷰어
   - 최근 로그 조회
   - 필터링 (레벨, 키워드)
   - 실시간 스트림

---

### 2.3 설정 관리
**파일**: `static/admin.html` (dashboard 탭)

**기능**:
- LLM 모델 변경 (70B ↔ 8B)
- 최대 파일 크기 조정
- 최대 동시 분석 수 변경
- 로그 레벨 설정
- 분석 결과 보관 기간 변경

**방식**: 
- GET `/api/admin/settings` - 현재 설정 조회
- POST `/api/admin/settings` - 설정 변경 (메모리에서만, 재시작 필요)

---

### 2.4 Health Check & Alerting
**엔드포인트**: 
- GET `/api/health` (이미 기본 구현)
- GET `/api/health/detailed` (추가)

**기능**:
- LLM 서버 연결 상태 체크
- 데이터베이스 상태 체크
- 디스크 용량 확인
- 메모리 사용량
- 에러율 모니터링

**상태 코드**:
- 200: 모든 시스템 정상
- 503: 하나 이상의 시스템 이상

---

## 새로운 API 엔드포인트

```
# 관리자 대시보드
GET  /admin                      → admin.html 반환
GET  /api/admin/dashboard        → 대시보드 데이터
GET  /api/admin/settings         → 현재 설정
POST /api/admin/settings         → 설정 변경
GET  /api/admin/logs             → 로그 조회
GET  /api/admin/logs/stream      → 로그 실시간 스트림 (SSE)

# 상세 헬스 체크
GET  /api/health/detailed        → 상세 시스템 상태
GET  /api/health/llm             → LLM 서버 상태만

# 통계 확장
GET  /api/statistics/daily       → 일일 통계
GET  /api/statistics/weekly      → 주간 통계
GET  /api/statistics/monthly     → 월간 통계
```

---

## 구현 순서

1. **로깅 시스템 통합** (20분)
   - logger 설정 확인
   - app.py에서 로깅 적용

2. **API 엔드포인트 추가** (40분)
   - 대시보드 데이터 엔드포인트
   - 설정 관리 엔드포인트
   - 로그 조회 엔드포인트
   - 상세 헬스 체크

3. **관리자 대시보드 UI** (60분)
   - HTML/CSS 작성
   - 통계 대시보드
   - 실시간 모니터링
   - 로그 뷰어
   - 설정 관리 폼

4. **테스트** (20분)
   - API 테스트
   - UI 테스트
   - 통합 테스트

**총 예상 시간**: 2-3시간

---

## 데이터 흐름

```
시스템 실행
    ↓
logger.py: 모든 활동을 JSON 로그로 기록 (logs/analysis.log)
    ↓
database.py: 분석 메타데이터를 SQLite에 저장
    ↓
app.py: API 엔드포인트들이 이 데이터를 조합해 제공
    ↓
admin.html: 관리자가 데이터를 시각화
```

---

## 파일 구조 (Phase 2 후)

```
multi-agent/
├── app.py                       (수정: 관리자 API 추가)
├── config.py                    (유지)
├── database.py                  (유지)
├── IMPROVEMENT_ROADMAP.md       (유지)
├── PHASE2_IMPLEMENTATION.md     (이 파일)
│
├── logs/                        (새로 생성)
│   └── analysis.log             (JSON 형식 로그)
│
├── utils/
│   ├── logger.py                (유지)
│   ├── queue_manager.py         (유지)
│   └── file_processor.py        (유지)
│
└── static/
    ├── index.html               (유지: 사용자 인터페이스)
    └── admin.html               (NEW: 관리자 대시보드)
```

---

## 테스트 방법

### 1. 대시보드 접속
```
http://127.0.0.1:8000/admin
```

### 2. 통계 확인
```bash
curl http://127.0.0.1:8000/api/admin/dashboard
```

### 3. 로그 확인
```bash
tail -f logs/analysis.log
```

### 4. 헬스 체크
```bash
curl http://127.0.0.1:8000/api/health/detailed
```

---

## 완료 기준

- [ ] 관리자 대시보드 접속 가능
- [ ] 통계 데이터 표시
- [ ] 실시간 모니터링 동작
- [ ] 로그 조회 가능
- [ ] 설정 변경 가능
- [ ] 헬스 체크 정상
- [ ] 모든 API 엔드포인트 정상 작동

