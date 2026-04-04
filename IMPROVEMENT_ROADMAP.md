# 개발 분석서 생성 시스템 - 개선 로드맵

## 🎯 목표
프로덕션 레벨의 안정적이고 사용하기 쉬운 시스템 구축

---

## 📋 전체 개선 계획

### Phase 1: Critical (1주) - 서버 안정성 & 사용자 경험
**목표**: 기본적인 안정성과 피드백 확보

- [x] **1.1 에러 핸들링 강화**
  - 파일 처리 에러 상세 메시지
  - API 에러별 구체적 피드백
  - 사용자 대면 에러 메시지 개선
  - 에러 발생 시 재시도 옵션
  
- [x] **1.2 분석 결과 자동 정리**
  - 30일 이상 된 파일 자동 삭제
  - output/ 디렉토리 용량 관리
  - SQLite 분석 이력 저장 (메타데이터)
  
- [x] **1.3 동시 분석 제한 & 큐 시스템**
  - 동시 분석 최대 3개 제한
  - 나머지는 큐에 대기
  - 큐 상태를 UI에 표시
  - 분석 취소 기능
  
- [x] **1.4 입력 검증 강화**
  - 파일 크기 제한 (최대 50MB)
  - 문서 길이 제한 (max 100K 토큰)
  - 지원하지 않는 파일 형식 필터링
  - XSS/Injection 방어

---

### Phase 2: Important (2주) - 운영 가능성
**목표**: 서버 모니터링과 기본 관리 기능

- [ ] **2.1 로깅 시스템**
  - 구조화된 로그 (JSON 형식)
  - 분석 시작/종료/실패 기록
  - API 응답 시간 측정
  - LLM API 토큰 사용량 추적
  - 로그 파일 자동 로테이션 (daily)
  
- [ ] **2.2 관리자 대시보드 (기본)**
  - 분석 이력 조회 & 검색
  - 실시간 분석 상태 모니터링
  - 시스템 통계 (일일 분석 수, 평균 시간 등)
  - LLM 서버 상태 체크
  - 로그 뷰어
  
- [ ] **2.3 설정 관리**
  - 관리자 UI에서 설정 변경 (LLM 모델, 최대 파일 크기 등)
  - 런타임 설정 재로드 (서버 재시작 필요 없음)
  - 설정 백업 & 복구
  
- [ ] **2.4 Health Check & Alerting**
  - `/health` 엔드포인트 (LLM 서버 연결 상태)
  - 에러율 모니터링
  - 자동 복구 (재연결 시도)

---

### Phase 3: Should Have (2주) - 사용자 경험 향상
**목표**: 사용자가 더 많은 정보를 더 쉽게 얻기

- [ ] **3.1 중간 결과 미리보기**
  - 각 에이전트 결과를 JSON으로 실시간 표시
  - Planner → 추출된 요구사항 카드
  - Developer → 기술 스택 다이어그램
  - Reviewer → 리스크 맵
  
- [ ] **3.2 분석 결과 비교**
  - 이전 버전과 비교 (diff 표시)
  - 변경사항 하이라이트
  
- [ ] **3.3 내보내기 형식 확대**
  - HTML 내보내기 (스타일 포함)
  - Word (.docx) 내보내기
  - PDF 내보내기
  - JSON 데이터 내보내기
  
- [ ] **3.4 공유 & 협업**
  - 분석 결과 공유 링크 (읽기 전용)
  - 댓글/토론 기능
  - 버전 관리 (변경 이력)

---

### Phase 4: Nice to Have (1주) - 고급 기능
**목표**: 파워 유저 기능

- [ ] **4.1 배치 분석**
  - 여러 파일 동시 업로드
  - 스케줄 분석 (매일 밤 12시 등)
  
- [ ] **4.2 LLM 모델 비교**
  - 같은 입력으로 여러 모델 분석 후 비교
  
- [ ] **4.3 API 모드**
  - RESTful API (프로그래밍 방식 사용)
  - WebSocket (실시간 결과 스트리밍)
  - 인증 & API Key 관리
  
- [ ] **4.4 템플릿 시스템**
  - 분석 결과 커스텀 템플릿
  - 산업별 템플릿 (금융, 의료, 소매 등)

---

## 📊 파일 구조 (개선 후)

```
multi-agent/
├── app.py                          # FastAPI 메인 (수정)
├── main.py                         # CLI (유지)
├── orchestrator.py                 # 오케스트레이터 (유지)
├── requirements.txt                # 의존성 (수정)
├── IMPROVEMENT_ROADMAP.md          # 이 파일
│
├── agents/                         # 에이전트들 (유지)
│   ├── planner.py
│   ├── developer.py
│   ├── reviewer.py
│   └── documenter.py
│
├── utils/
│   ├── claude_client.py            # (유지)
│   ├── llm_client.py               # (유지)
│   ├── file_processor.py           # (유지)
│   ├── logger.py                   # NEW: 구조화된 로깅
│   ├── storage.py                  # NEW: DB + 파일 관리
│   └── queue_manager.py            # NEW: 분석 큐 관리
│
├── services/
│   ├── analysis_service.py         # NEW: 분석 비즈니스 로직
│   └── storage_service.py          # NEW: 분석 이력 관리
│
├── static/
│   ├── index.html                  # (수정: 더 나은 UX)
│   ├── admin.html                  # NEW: 관리자 대시보드
│   └── css/
│       └── styles.css              # NEW: 공용 스타일
│
├── config.py                       # NEW: 설정 관리
├── database.py                     # NEW: SQLite 초기화
└── output/                         # 분석 결과 저장
```

---

## 🔄 Phase 1 세부 구현 계획

### 1.1 에러 핸들링 강화

**file_processor.py**
```python
# 각 추출 함수에 상세 에러 메시지 추가
# → 사용자가 뭐가 잘못됐는지 알 수 있음

def extract_from_pdf(file_path: str) -> tuple[str, Optional[str]]:
    """
    Returns: (extracted_text, error_message)
    error_message는 None이면 성공, 있으면 실패 이유
    """
```

**app.py**
```python
# 모든 API 응답에 상세한 에러 정보 포함
{
    "status": "error",
    "error_code": "FILE_SIZE_EXCEEDED",
    "message": "파일 크기가 50MB를 초과했습니다",
    "details": {"max_size": "50MB", "actual_size": "150MB"},
    "actions": ["파일 크기를 줄이세요", "여러 파일로 나누세요"]
}
```

### 1.2 분석 결과 자동 정리

**storage.py** (NEW)
```python
# SQLite 분석 이력 저장
# - analysis_id, file_name, file_size, created_at, output_file, status
# APScheduler로 30일 이상 파일 자동 삭제
```

### 1.3 동시 분석 제한 & 큐

**queue_manager.py** (NEW)
```python
class AnalysisQueue:
    - max_concurrent = 3
    - waiting_queue (in-memory)
    - current_jobs tracking
    - cancel_job(job_id)
```

### 1.4 입력 검증

**app.py** (수정)
```python
# 파일 크기: 50MB 제한
# 문서 길이: 100K 토큰 제한
# 파일 형식: 화이트리스트만 허용
# 특수 문자: XSS 방지
```

---

## ⏱️ 예상 일정

| Phase | 기간 | 우선순위 | 상태 |
|-------|------|---------|------|
| Phase 1 | 1주 | Critical | 진행 예정 |
| Phase 2 | 2주 | Important | 예정 |
| Phase 3 | 2주 | Should Have | 예정 |
| Phase 4 | 1주 | Nice to Have | 예정 |

**총 예상 기간**: 6주

---

## 🚀 시작 시점

- **Phase 1 시작**: 지금 바로
- 각 Phase 완료 후 테스트 및 배포
- 사용자 피드백 반영 후 다음 Phase 진행

---

## 💾 버전 관리

- **v0.1**: 기본 기능 (현재)
- **v0.2**: Phase 1 완료 (Critical 기능)
- **v1.0**: Phase 1-2 완료 (프로덕션 레벨)
- **v1.1**: Phase 3 완료 (UX 향상)
- **v2.0**: Phase 4 완료 (고급 기능)
