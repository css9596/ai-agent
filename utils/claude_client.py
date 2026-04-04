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
        if "selected_agents" in lower or "orchestrator" in lower:
            return {
                "selected_agents": ["planner", "developer", "reviewer", "documenter"],
                "reason": "요구사항 분석, 기술 설계, 리스크 검토, 문서화가 모두 필요한 기능 추가 요청입니다.",
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
            "## 5. 영향 범위\n"
            "- 영향 모듈: BoardController, AttachmentService, Mapper\n"
            "- 영향 화면: 게시글 작성/수정/상세, 관리자 설정\n"
            "- 운영/배포 고려사항: 업로드 경로 권한 및 로그 모니터링\n\n"
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
            "- [ ] 배포/롤백 계획 확정\n"
        )
