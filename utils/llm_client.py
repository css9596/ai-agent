import json
import re
import time
from typing import Any, Dict, Optional

from openai import OpenAI


class LLMClient:
    """내부 LLM(Ollama, vLLM 등) OpenAI 호환 API 클라이언트

    ClaudeClient와 동일한 인터페이스를 제공하지만,
    Anthropic API 대신 OpenAI 호환 API를 사용합니다.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        mock: bool = False
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.mock = mock
        self._client = OpenAI(api_key=api_key, base_url=base_url) if not mock else None

    @staticmethod
    def _korean_system_prompt(system_prompt: str) -> str:
        """한국어 응답 지시를 system_prompt에 추가"""
        return system_prompt + "\n반드시 한국어로만 답변하세요. Never respond in Chinese or English."

    def request_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """JSON 응답을 요청합니다."""
        if self.mock or self._client is None:
            return self._mock_json_response(system_prompt, user_prompt)

        last_error: Optional[Exception] = None
        last_text: str = ""
        system_prompt = self._korean_system_prompt(system_prompt)

        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    max_tokens=1800,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                text = response.choices[0].message.content
                last_text = text
                return self._parse_json_safely(text)
            except Exception as exc:
                last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(1.5 * attempt)

        # 최종 폴백: 마지막 응답이 있으면 JSON 복구 시도
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

        raise RuntimeError(f"LLM API request failed after {max_retries} attempts: {last_error}")

    def request_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        """텍스트 응답을 요청합니다."""
        if self.mock or self._client is None:
            return self._mock_text_response(system_prompt, user_prompt)

        last_error: Optional[Exception] = None
        system_prompt = self._korean_system_prompt(system_prompt)

        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    max_tokens=2400,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(1.5 * attempt)

        raise RuntimeError(f"LLM API request failed after {max_retries} attempts: {last_error}")

    @staticmethod
    def _parse_json_safely(text: str) -> Dict[str, Any]:
        """JSON 문자열을 여러 형식으로 파싱 시도합니다."""
        # 1. 직접 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Markdown fence에 감싼 JSON 찾기
        fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
        if fenced:
            return json.loads(fenced.group(1))

        # 3. 첫 { 부터 마지막 } 까지 추출
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(text[start : end + 1])

        raise json.JSONDecodeError("No JSON object found", text, 0)

    @staticmethod
    def _mock_json_response(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Mock JSON 응답 (사용자 입력 반영)"""
        # 사용자의 입력 내용 추출
        input_text = user_prompt.lower()

        lower = (system_prompt + "\n" + user_prompt).lower()

        if "selected_agents" in lower or "orchestrator" in lower:
            return {
                "selected_agents": ["planner", "developer", "reviewer", "documenter"],
                "reason": "요구사항 분석, 기술 설계, 리스크 검토, 문서화가 모두 필요합니다.",
            }

        if "planner" in lower:
            # 사용자 입력 내용에서 주요 키워드 추출
            keywords = []
            if "파일" in input_text or "첨부" in input_text or "upload" in input_text:
                keywords.append("파일 첨부 기능")
            if "회원" in input_text or "사용자" in input_text or "user" in input_text:
                keywords.append("회원 관리 기능")
            if "이메일" in input_text or "email" in input_text:
                keywords.append("이메일 검증")
            if "로그인" in input_text or "login" in input_text or "sso" in input_text:
                keywords.append("소셜 로그인")
            if "검색" in input_text or "search" in input_text:
                keywords.append("검색 기능")
            if "알림" in input_text or "notification" in input_text:
                keywords.append("실시간 알림")

            core_reqs = keywords if keywords else ["사용자 요청 기능 구현"]

            return {
                "core_requirements": core_reqs,
                "functional_requirements": [
                    f"{req} 구현" for req in core_reqs
                ] + ["UI/UX 개선", "에러 처리", "데이터 유효성 검증"],
                "non_functional_requirements": [
                    "데이터 보안 강화",
                    "성능 최적화 (응답 시간 1초 이내)",
                    "확장성 고려 (향후 기능 추가 대비)",
                ],
                "ambiguities": [
                    "요구사항의 우선순위 확인 필요",
                    "기술 스택 및 아키텍처 확정 필요",
                ],
                "clarification_questions": [
                    "구현 우선순위가 있나요?",
                    "기존 시스템과의 통합 방식은?",
                    "배포 일정이 정해져 있나요?",
                ],
            }

        if "developer" in lower:
            return {
                "technical_spec": [
                    "REST API 기반 백엔드 설계",
                    "데이터베이스 스키마 설계",
                    "프론트엔드 UI 컴포넌트 구현",
                ],
                "db_changes": [
                    {"table": "user_feature", "columns": ["id", "user_id", "feature_type", "created_at"]},
                    {"table": "feature_config", "columns": ["key", "value", "updated_at"]},
                ],
                "impacted_modules": [
                    "백엔드 API",
                    "데이터베이스",
                    "프론트엔드",
                    "관리자 대시보드",
                ],
                "effort": "M",
            }

        if "reviewer" in lower:
            return {
                "cross_review": [
                    "요구사항과 설계의 일관성 검토 필요",
                    "기술 선택의 타당성 확인",
                ],
                "missing_exceptions": [
                    "에러 시나리오별 처리 방안 누락",
                    "롤백 전략 미정의",
                ],
                "security_risks": [
                    "입력값 검증 필수",
                    "인증/인가 체계 강화",
                ],
                "performance_risks": [
                    "대용량 데이터 처리 성능 확인",
                    "동시 접속 시 안정성 테스트 필요",
                ],
                "schedule_risks": [
                    "예상 공수 검토 필요",
                    "마이그레이션 계획 필요",
                ],
            }

        return {"message": "mock response"}

    @staticmethod
    def _mock_text_response(system_prompt: str, user_prompt: str) -> str:
        """Mock 텍스트 응답 (사용자 입력 반영)"""
        input_text = user_prompt

        # 제목 및 요약 생성
        title = "개발 분석서"
        if "파일" in input_text or "첨부" in input_text:
            title = "파일 첨부 기능 분석서"
        elif "회원" in input_text or "사용자" in input_text:
            title = "회원 관리 기능 분석서"
        elif "검색" in input_text:
            title = "검색 기능 분석서"

        return (
            f"# {title}\n\n"
            "## 1. 요청 요약\n"
            f"**사용자 입력**: {input_text[:150]}\n\n"
            "**분석 목표**:\n"
            "- 요구사항 명확화\n"
            "- 기술 설계 방안 제시\n"
            "- 리스크 분석 및 대응책\n"
            "- 일정/공수 예측\n\n"
            "**범위(In)**: 기능 설계, 기술 스택 정의, 리스크 분석\n"
            "**범위(Out)**: 구현 코드, 실제 배포\n\n"
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
