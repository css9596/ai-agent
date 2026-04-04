import json
import re
import time
from typing import Any, Dict, Optional

from anthropic import Anthropic


class ClaudeClient:
    def __init__(self, api_key: Optional[str], model: str = "claude-sonnet-4-5", mock: bool = False) -> None:
        self.model = model
        self.mock = mock
        self._client = Anthropic(api_key=api_key) if api_key and not mock else None

    def request_json(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        if self.mock or self._client is None:
            return self._mock_json_response(system_prompt, user_prompt)

        last_error: Optional[Exception] = None
        last_text: str = ""
        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=1800,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = self._extract_text(response)
                last_text = text
                return self._parse_json_safely(text)
            except Exception as exc:
                last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(1.5 * attempt)
        # Final fallback: try to repair malformed JSON once.
        if last_text:
            try:
                repaired = self.request_text(
                    system_prompt="Fix malformed JSON. Return only valid JSON object.",
                    user_prompt=f"다음 텍스트를 유효한 JSON 객체로만 변환하세요:\n\n{last_text}",
                    max_retries=1,
                )
                return self._parse_json_safely(repaired)
            except Exception:
                return {"raw_response": last_text, "parse_error": str(last_error)}
        raise RuntimeError(f"Claude API request failed after {max_retries} attempts: {last_error}")

    def request_text(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        if self.mock or self._client is None:
            return self._mock_text_response(system_prompt, user_prompt)

        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=2400,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return self._extract_text(response)
            except Exception as exc:
                last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(1.5 * attempt)
        raise RuntimeError(f"Claude API request failed after {max_retries} attempts: {last_error}")

    @staticmethod
    def _extract_text(response: Any) -> str:
        texts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "\n".join(texts).strip()

    @staticmethod
    def _parse_json_safely(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
        if fenced:
            return json.loads(fenced.group(1))

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(text[start : end + 1])

        raise json.JSONDecodeError("No JSON object found", text, 0)

    @staticmethod
    def _mock_json_response(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        lower = (system_prompt + "\n" + user_prompt).lower()

        # 더 구체적인 조건을 먼저 확인 (quality는 planner 체크보다 먼저 와야 함)
        if "selected_agents" in lower or "orchestrator" in lower:
            return {
                "selected_agents": ["planner", "developer", "reviewer", "documenter"],
                "reason": "요구사항 분석, 기술 설계, 리스크 검토, 문서화가 모두 필요한 기능 추가 요청입니다.",
            }
        if "quality" in lower or "strict quality" in lower:
            return {
                "total_score": 88,
                "pass": False,
                "agent_scores": {
                    "planner": {"score": 92, "feedback": "요구사항 추출은 충분하나 비기능 요구사항에 응답 시간 기준이 누락되었습니다."},
                    "developer": {"score": 80, "feedback": "DB 스키마에 인덱스 전략이 없고 파일 저장 경로 관리 방식이 명시되지 않았습니다."},
                    "impact_analyzer": {"score": 91, "feedback": "파일 영향도는 잘 분석되었으나 공통 유틸리티(FileUtil.java) 영향이 누락되었습니다."},
                    "reviewer": {"score": 89, "feedback": "보안 리스크는 잘 도출되었으나 업로드 실패 시 트랜잭션 롤백 시나리오가 빠졌습니다."},
                },
                "retry_agents": ["developer"],
                "overall_feedback": "전체적으로 양호하나 developer 에이전트의 DB 인덱스 전략과 파일 경로 관리 방식이 구체적이지 않습니다.",
            }
        if "chat" in lower or "requirements refinement" in lower:
            # 질문 내용에 따라 다른 응답 제공
            if "s3" in lower or "저장소" in lower or "바꾸면" in lower:
                return {
                    "type": "reanalysis",
                    "requires_reanalysis": True,
                    "answer": "S3 저장소로 변경할 경우, 다음 부분이 영향받습니다:\n\n1. **AttachService.java**: S3 SDK(AWS SDK for Java) 의존성 추가, S3 업로드/다운로드 로직 변경\n2. **BoardController.java**: 로컬 경로 대신 S3 URL 반환\n3. **system_setting**: 로컬 경로 설정 대신 S3 버킷명, IAM 권한 설정 추가\n4. **보안**: IAM 권한 기반 접근 제어로 파일 접근 보안 강화\n5. **배포 일정**: S3 설정 및 테스트로 인해 1일 추가\n\n영향도: MEDIUM → HIGH로 상향 조정",
                    "reanalyzed_impact": {
                        "impact_summary": {
                            "total_files": 6,
                            "new_files": 1,
                            "modified_files": 5,
                            "impact_level": "HIGH"
                        },
                        "file_impacts": {
                            "service": [
                                {"file": "AttachService.java", "change_type": "MODIFY", "methods": ["uploadAttach", "downloadAttach"], "reason": "S3 SDK 추가, 로직 변경"}
                            ],
                            "controller": [
                                {"file": "BoardController.java", "change_type": "MODIFY", "methods": ["downloadAttach"], "reason": "S3 URL 반환"}
                            ],
                            "mapper": [
                                {"file": "system_setting_mapper.xml", "change_type": "MODIFY", "queries": ["updateS3Settings"], "reason": "S3 설정 추가"}
                            ]
                        }
                    },
                    "follow_up_suggestions": [
                        "S3 대신 Azure Blob Storage로 하면?",
                        "기존 로컬 첨부는 어떻게 마이그레이션?",
                        "비용 예상은?"
                    ]
                }
            else:
                return {
                    "type": "answer",
                    "requires_reanalysis": False,
                    "answer": "현재 분석에 따르면, 첨부파일 기능은 BoardController, AttachService, AttachDao, AttachMapper.xml 등 5개 주요 파일에 영향을 미칩니다. 보안 위험은 파일명 기반 경로조작 방지와 콘텐츠 타입 스푸핑 대응이 주요 항목입니다. 일정은 중간 난이도(M)로 약 4일 소요될 것으로 예상됩니다.",
                    "follow_up_suggestions": [
                        "보안 위험 상세 설명",
                        "다른 게시판도 함께 적용?",
                        "테스트 전략은?"
                    ]
                }
        if "planner" in lower:
            return {
                "core_requirements": [
                    "게시판에 파일 첨부 기능 추가",
                    "허용 확장자: jpg, png, pdf, xlsx",
                    "파일당 최대 10MB",
                    "게시글당 최대 5개",
                    "개별 삭제 가능",
                    "관리자 설정에서 용량 제한 변경 가능",
                ],
                "functional_requirements": [
                    "작성/수정 화면 첨부 업로드",
                    "목록/상세에서 첨부 표시",
                    "첨부파일 개별 삭제",
                    "관리자 설정 UI 및 저장",
                ],
                "non_functional_requirements": [
                    "파일 검증(확장자/크기)",
                    "보안(업로드 파일 검사 및 경로 보호)",
                    "성능(목록 조회시 N+1 방지)",
                ],
                "ambiguities": [
                    "기존 게시글의 첨부 마이그레이션 필요 여부",
                    "허용 확장자 정책이 게시판별인지 전역인지",
                ],
                "clarification_questions": [
                    "첨부파일 저장소는 로컬/오브젝트 스토리지 중 무엇을 사용하나요?",
                    "이미 업로드된 비허용 확장자는 어떻게 처리하나요?",
                ],
            }
        if "developer" in lower:
            return {
                "technical_spec": [
                    "Java Controller에서 multipart 업로드 처리",
                    "JSP/jQuery로 다중 첨부 UI 제공",
                    "MyBatis Mapper로 첨부 메타데이터 CRUD",
                ],
                "db_changes": [
                    {"table": "board_attachment", "columns": ["id", "post_id", "file_name", "file_size", "ext", "path", "created_at"]},
                    {"table": "system_setting", "columns": ["attach_max_size_mb"]},
                ],
                "impacted_modules": [
                    "게시글 작성/수정 JSP",
                    "게시글 상세/목록 JSP",
                    "BoardController",
                    "AttachmentService",
                    "BoardMapper.xml",
                ],
                "effort": "M",
            }
        if "reviewer" in lower:
            return {
                "cross_review": [
                    "확장자 검증은 클라이언트/서버 이중 체크 필요",
                    "업로드 실패 시 트랜잭션 롤백 전략 필요",
                ],
                "missing_exceptions": [
                    "파일 6개 이상 첨부 시 에러 처리",
                    "10MB 초과 파일 업로드 시 사용자 안내",
                ],
                "security_risks": [
                    "파일명 기반 경로조작 방지",
                    "콘텐츠 타입 스푸핑 대응",
                ],
                "performance_risks": [
                    "첨부 목록 조인 쿼리 최적화 필요",
                ],
                "schedule_risks": [
                    "관리자 설정 화면 및 권한 반영 누락 가능성",
                ],
            }
        if "impact" in lower:
            return {
                "impact_summary": {
                    "total_files": 8,
                    "new_files": 3,
                    "modified_files": 5,
                    "impact_level": "MEDIUM",
                },
                "db_changes": [
                    {
                        "table": "BOARD_ATTACH",
                        "change_type": "NEW",
                        "columns": ["ATTACH_ID", "BOARD_ID", "FILE_NAME", "FILE_SIZE", "FILE_EXT", "FILE_PATH", "REG_DT"],
                        "reason": "첨부파일 메타데이터 저장",
                    },
                    {
                        "table": "SYSTEM_SETTING",
                        "change_type": "ADD_COLUMN",
                        "columns": ["ATTACH_MAX_SIZE_MB", "ATTACH_ALLOWED_EXT"],
                        "reason": "관리자 첨부파일 설정",
                    },
                ],
                "file_impacts": {
                    "controller": [
                        {"file": "BoardController.java", "change_type": "MODIFY", "methods": ["writeBoard", "modifyBoard", "deleteBoard", "downloadAttach"], "reason": "첨부파일 업로드/다운로드 처리"},
                    ],
                    "service": [
                        {"file": "AttachService.java", "change_type": "NEW", "methods": ["uploadAttach", "deleteAttach", "getAttachList", "validateFile"], "reason": "첨부파일 비즈니스 로직"},
                    ],
                    "dao": [
                        {"file": "AttachDao.java", "change_type": "NEW", "methods": ["insertAttach", "deleteAttach", "selectAttachList", "selectAttachById"], "reason": "첨부파일 DB 접근"},
                    ],
                    "mapper": [
                        {"file": "AttachMapper.xml", "change_type": "NEW", "queries": ["insertAttach", "deleteAttachById", "selectAttachListByBoardId"], "reason": "첨부파일 CRUD 쿼리"},
                    ],
                    "jsp": [
                        {"file": "boardWrite.jsp", "change_type": "MODIFY", "reason": "다중 파일 첨부 UI 추가"},
                        {"file": "boardDetail.jsp", "change_type": "MODIFY", "reason": "첨부파일 목록 및 다운로드 링크 표시"},
                        {"file": "adminSetting.jsp", "change_type": "MODIFY", "reason": "첨부파일 설정 항목 추가"},
                    ],
                    "javascript": [
                        {"file": "boardWrite.js", "change_type": "MODIFY", "reason": "jQuery 다중 파일 첨부/삭제 처리"},
                    ],
                },
                "dependency_chain": (
                    "BOARD_ATTACH 테이블 신규 → AttachMapper.xml 쿼리 추가 → "
                    "AttachDao.java 신규 → AttachService.java 신규 → "
                    "BoardController.java 수정 → boardWrite.jsp / boardDetail.jsp 화면 수정"
                ),
            }
        return {"message": "mock response"}

    @staticmethod
    def _mock_text_response(system_prompt: str, user_prompt: str) -> str:
        return (
            "# 개발 분석서\n\n"
            "## 1. 요청 요약\n"
            "- 배경: 기존 게시판에 첨부 기능 부재\n"
            "- 목표: 첨부 업로드/삭제/관리자 설정 제공\n"
            "- 범위(In): 작성/수정/삭제/관리자 설정, 범위(Out): 대용량 스토리지 전환\n\n"
            "## 2. 요구사항 명세\n"
            "### 2.1 기능 요구사항\n"
            "| ID | 요구사항 | 우선순위 | 비고 |\n"
            "|---|---|---|---|\n"
            "| FR-01 | 게시글 작성/수정 시 파일 첨부 | High | 최대 5개 |\n"
            "| FR-02 | 허용 확장자 검증 | High | jpg,png,pdf,xlsx |\n"
            "| FR-03 | 첨부파일 개별 삭제 | High | 권한 체크 필요 |\n"
            "| FR-04 | 관리자 용량 제한 설정 | Medium | 설정 페이지 |\n\n"
            "### 2.2 비기능 요구사항\n"
            "| 항목 | 요구사항 | 측정 기준 |\n"
            "|---|---|---|\n"
            "| 성능 | 게시글 조회 시 첨부 로딩 최적화 | 95p 1초 이내 |\n"
            "| 보안 | 서버측 확장자/크기 검증 | 우회 업로드 차단 |\n\n"
            "### 2.3 명확화 필요사항\n"
            "| 항목 | 질문 | 결정 필요일 |\n"
            "|---|---|---|\n"
            "| 저장소 | 로컬/오브젝트 스토리지 선택? | 개발 착수 전 |\n\n"
            "## 3. 기술 설계 (Java/JSP/jQuery/MyBatis)\n"
            "- Controller multipart 처리 + Service 검증\n"
            "- JSP/jQuery 다중 파일 업로드 및 개별 삭제 UI\n"
            "- MyBatis Mapper로 첨부 메타데이터 CRUD\n\n"
            "## 4. DB 변경사항\n"
            "| 테이블 | 변경 유형(신규/수정) | 컬럼 | 설명 |\n"
            "|---|---|---|---|\n"
            "| board_attachment | 신규 | id, post_id, file_name, file_size, ext, path | 첨부 메타 저장 |\n"
            "| system_setting | 수정 | attach_max_size_mb | 관리자 설정 |\n\n"
            "## 5. 영향 범위 (레이어별 상세)\n"
            "### 5.1 DB 변경사항\n"
            "| 테이블 | 변경 유형 | 컬럼 | 이유 |\n"
            "|---|---|---|---|\n"
            "| BOARD_ATTACH | 신규 | ATTACH_ID, BOARD_ID, FILE_NAME, FILE_SIZE, FILE_EXT, FILE_PATH, REG_DT | 첨부파일 메타데이터 |\n"
            "| SYSTEM_SETTING | 컬럼추가 | ATTACH_MAX_SIZE_MB, ATTACH_ALLOWED_EXT | 관리자 설정 |\n\n"
            "### 5.2 소스 파일 영향도\n"
            "| 레이어 | 파일명 | 변경 유형 | 변경 메서드/쿼리 | 이유 |\n"
            "|---|---|---|---|---|\n"
            "| Controller | BoardController.java | 수정 | writeBoard, modifyBoard, downloadAttach | 첨부 처리 |\n"
            "| Service | AttachService.java | 신규 | uploadAttach, deleteAttach, validateFile | 첨부 비즈니스 로직 |\n"
            "| DAO | AttachDao.java | 신규 | insertAttach, deleteAttach, selectAttachList | 첨부 DB 접근 |\n"
            "| Mapper | AttachMapper.xml | 신규 | insertAttach, deleteAttachById, selectAttachListByBoardId | 첨부 CRUD 쿼리 |\n"
            "| JSP | boardWrite.jsp | 수정 | - | 다중 파일 첨부 UI |\n"
            "| JSP | boardDetail.jsp | 수정 | - | 첨부파일 목록 표시 |\n"
            "| JS | boardWrite.js | 수정 | - | jQuery 첨부 처리 |\n\n"
            "### 5.3 변경 연쇄 순서\n"
            "- BOARD_ATTACH 신규 → AttachMapper.xml → AttachDao.java → AttachService.java → BoardController.java → boardWrite.jsp / boardDetail.jsp\n\n"
            "## 6. 검토 결과 (리스크/예외/보안/성능)\n"
            "| 구분 | 내용 | 대응 방안 | 우선순위 |\n"
            "|---|---|---|---|\n"
            "| 보안 | 콘텐츠 타입 스푸핑 | 서버측 MIME/시그니처 검증 | High |\n"
            "| 예외 | 10MB 초과 업로드 | 사용자 메시지 + 서버 차단 | High |\n\n"
            "## 7. 일정 및 공수 제안\n"
            "- 총 공수: M\n"
            "- 분석 0.5d / 개발 2d / 테스트 1d / 배포 0.5d\n"
            "- 선행조건: 저장소 정책/권한 정책 확정\n\n"
            "## 8. 개발팀 실행 체크리스트\n"
            "- [ ] 명확화 이슈 확정\n"
            "- [ ] DB 변경안 리뷰\n"
            "- [ ] 보안 점검 항목 반영\n"
            "- [ ] 테스트 케이스 작성\n"
            "- [ ] 배포/롤백 계획 확정\n\n"
            "## 9. 품질 검사 결과\n"
            "| 에이전트 | 점수 | 피드백 |\n"
            "|---|---|---|\n"
            "| 종합 | 88점 | 전체적으로 양호하나 developer 에이전트의 DB 인덱스 전략이 구체적이지 않습니다. |\n"
            "| planner | 92점 | 비기능 요구사항에 응답 시간 기준 누락 |\n"
            "| developer | 80점 | DB 인덱스 전략 및 파일 경로 관리 방식 미명시 |\n"
            "| impact_analyzer | 91점 | 공통 유틸리티(FileUtil.java) 영향 누락 |\n"
            "| reviewer | 89점 | 트랜잭션 롤백 시나리오 누락 |\n"
        )
