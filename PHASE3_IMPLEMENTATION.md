# Phase 3: Should Have (사용자 경험 향상) - 상세 구현 계획

## 목표
사용자가 더 많은 정보를 더 쉽게 얻을 수 있도록 개선

---

## 구현 항목

### 3.1 중간 결과 미리보기
**목표**: 각 에이전트 실행 결과를 실시간으로 표시

**UI 변화**:
```
모니터링 화면
├─ 파이프라인 상태 (기존)
├─ 로그 (기존)
└─ 중간 결과 카드 (NEW)
   ├─ Planner 결과
   │  ├─ 핵심 요구사항 (5개)
   │  ├─ 기능 요구사항 (8개)
   │  └─ 명확화 질문 (3개)
   ├─ Developer 결과
   │  ├─ 기술 스택
   │  ├─ DB 변경 테이블
   │  └─ 영향 모듈 목록
   ├─ Reviewer 결과
   │  ├─ 보안 리스크 (2개)
   │  ├─ 성능 리스크 (1개)
   │  └─ 일정 리스크 (1개)
   └─ Documenter 결과
      └─ 마크다운 미리보기 (처음 500자)
```

**구현**:
- `static/index.html`의 모니터링 섹션에 탭 추가
- SSE 이벤트에 `agent_result` 타입 추가
- 각 에이전트별 결과를 JSON으로 전송
- UI에서 JSON을 보기 좋게 렌더링

---

### 3.2 분석 결과 비교
**목표**: 이전 버전과 현재 분석 비교

**기능**:
1. 비교 대상 선택
   - 현재 분석
   - 이전 분석 선택 (드롭다운)

2. 비교 결과 표시
   - 추가된 항목 (녹색)
   - 삭제된 항목 (빨강)
   - 변경된 항목 (노랑)
   - 동일한 항목 (회색)

3. diff 형식
   ```
   요구사항 비교:
   - 게시판에 파일 첨부 기능 추가 (기존)
   + 실시간 알림 기능 추가 (신규)
   ~ 파일 크기 제한: 10MB → 50MB (변경)
   ```

**API**:
- `GET /api/analyses/{id1}/compare/{id2}` - 두 분석 비교

**UI**:
- 새로운 화면: "비교 분석"
- 나란히 표시 또는 diff 뷰

---

### 3.3 내보내기 형식 확대

#### 3.3.1 HTML 내보내기
**특징**:
- 마크다운을 HTML로 변환
- 스타일링 포함 (CSS)
- 자체 포함 (standalone, CDN 없음)
- 인쇄 가능

**구현**:
- `markdown-to-html` 라이브러리 (또는 직접 구현)
- CSS를 HTML에 인라인

**파일**: 
- `analysis_20260403_200355.html`

#### 3.3.2 PDF 내보내기
**특징**:
- HTML → PDF 변환
- 페이지 레이아웃 예쁨
- 메타정보 포함 (작성일, 분석자 등)

**구현**:
- `weasyprint` (추천) 또는 `reportlab`
- HTML 버전 → PDF로 변환

**파일**:
- `analysis_20260403_200355.pdf`

#### 3.3.3 Word 내보내기
**특징**:
- .docx 포맷
- 테이블, 이미지, 목차 지원
- 편집 가능

**구현**:
- `python-docx` 라이브러리
- 마크다운 파싱 후 Word 문서 생성

**파일**:
- `analysis_20260403_200355.docx`

#### 3.3.4 JSON 내보내기
**특징**:
- 모든 중간 결과 포함
- 프로그래밍 방식 처리 가능

**구현**:
- orchestrator 실행 후 context 전체를 JSON으로

**파일**:
- `analysis_20260403_200355.json`

---

## 새로운 API 엔드포인트

```
# 중간 결과 (이미 SSE로 제공되지만 API로도 제공)
GET  /api/analyses/{id}/results      → 모든 중간 결과 JSON

# 비교
GET  /api/analyses/{id1}/compare/{id2}  → 비교 결과

# 내보내기
GET  /api/download/{filename}/html   → HTML 다운로드
GET  /api/download/{filename}/pdf    → PDF 다운로드
GET  /api/download/{filename}/docx   → Word 다운로드
GET  /api/download/{filename}/json   → JSON 다운로드
```

---

## 구현 순서 & 소요 시간

### 1단계: 중간 결과 미리보기 (3시간)
- [ ] SSE 이벤트 수정 (`orchestrator.py`)
- [ ] 결과 저장 (`database.py`)
- [ ] API 엔드포인트 추가 (`app.py`)
- [ ] UI 업데이트 (`static/index.html`)
- [ ] 테스트

### 2단계: 내보내기 기능 (3시간)
- [ ] 유틸리티 함수 (`utils/export_formats.py`)
  - HTML 변환
  - PDF 변환
  - Word 생성
  - JSON 저장
- [ ] API 엔드포인트 (`app.py`)
- [ ] UI 버튼 추가 (`static/index.html`)
- [ ] 테스트

### 3단계: 비교 기능 (2시간)
- [ ] 비교 로직 (`utils/comparison.py`)
- [ ] API 엔드포인트 (`app.py`)
- [ ] UI 화면 (`static/index.html`)
- [ ] 테스트

**총 예상 시간**: 8시간 (2일)

---

## 파일 수정/추가 계획

```
추가 파일:
  utils/export_formats.py     ← HTML/PDF/Word 내보내기
  utils/comparison.py         ← 분석 비교 로직

수정 파일:
  app.py                      ← 새 API 엔드포인트
  orchestrator.py             ← 중간 결과 저장
  database.py                 ← 중간 결과 저장
  static/index.html           ← UI 업데이트
  requirements.txt            ← 새 패키지
```

---

## 새 패키지

```
markdown2              # Markdown → HTML
weasyprint            # HTML → PDF
python-docx           # Word 문서 생성
difflib               # Python 내장 (비교)
```

---

## 테스트 시나리오

### 중간 결과 미리보기
1. 분석 시작
2. 각 에이전트 실행 시 결과 카드에 표시되는지 확인
3. JSON 데이터가 제대로 파싱되는지 확인

### 내보내기
1. 분석 완료
2. HTML 다운로드 → 브라우저에서 열기
3. PDF 다운로드 → PDF 리더에서 열기
4. Word 다운로드 → Word에서 열기
5. JSON 다운로드 → 검증

### 비교
1. 두 개의 분석 실행
2. 비교 화면에서 차이점 확인
3. diff 형식 검증

---

## 완료 기준

- [ ] 모니터링 중 각 에이전트 결과 실시간 표시
- [ ] 결과 카드들이 보기 좋게 렌더링됨
- [ ] HTML 내보내기 정상 작동
- [ ] PDF 내보내기 정상 작동
- [ ] Word 내보내기 정상 작동
- [ ] JSON 내보내기 정상 작동
- [ ] 비교 기능 정상 작동
- [ ] 모든 UI 버튼 클릭 가능
- [ ] 에러 처리 완벽

