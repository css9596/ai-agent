from typing import Any, Dict

from utils.claude_client import ClaudeClient
from utils.context_builder import build_profile_section as _build_profile_section
from utils.context_builder import build_history_section as _build_history_section
from utils.context_builder import KOREAN_INSTRUCTION, KOREAN_SUFFIX


class DocumenterAgent:
    name = "Documenter"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "", examples: list = None) -> Dict[str, Any]:
        print("[Documenter] 분석 중...")
        examples_section = ""
        if examples:
            examples_section = "\n\n[참고 예시 - 아래 예시와 동일한 수준의 품질로 작성]\n"
            for i, ex in enumerate(examples[:2], 1):
                title = ex.get("title", f"예시 {i}")
                output_preview = ex.get("output_markdown", "")[:400]
                examples_section += f"\n예시 {i} ({title}):\n{output_preview}...\n"
        template = (
            "# 개발 분석서\n\n"
            "## 1. 요청 요약\n"
            "- 배경\n"
            "- 목표\n"
            "- 범위(In/Out)\n\n"
            "## 2. 요구사항 명세\n"
            "### 2.1 기능 요구사항\n"
            "| ID | 요구사항 | 우선순위 | 비고 |\n"
            "|---|---|---|---|\n\n"
            "### 2.2 비기능 요구사항\n"
            "| 항목 | 요구사항 | 측정 기준 |\n"
            "|---|---|---|\n\n"
            "### 2.3 명확화 필요사항\n"
            "| 항목 | 질문 | 결정 필요일 |\n"
            "|---|---|---|\n\n"
            "## 3. 기술 설계 (Java/JSP/jQuery/MyBatis)\n"
            "- 아키텍처/흐름\n"
            "- 서버 처리 로직\n"
            "- 프론트 동작\n"
            "- API/엔드포인트\n\n"
            "## 4. DB 변경사항\n"
            "| 테이블 | 변경 유형(신규/수정) | 컬럼 | 설명 |\n"
            "|---|---|---|---|\n\n"
            "## 5. 영향 범위 (레이어별 상세)\n"
            "### 5.1 DB 변경사항\n"
            "| 테이블 | 변경 유형 | 컬럼 | 이유 |\n"
            "|---|---|---|---|\n\n"
            "### 5.2 소스 파일 영향도\n"
            "| 레이어 | 파일명 | 변경 유형 | 변경 메서드/쿼리 | 이유 |\n"
            "|---|---|---|---|---|\n\n"
            "### 5.3 변경 연쇄 순서\n"
            "- (A → B → C 순서)\n\n"
            "## 6. 검토 결과 (리스크/예외/보안/성능)\n"
            "| 구분 | 내용 | 대응 방안 | 우선순위 |\n"
            "|---|---|---|---|\n\n"
            "## 7. 일정 및 공수 제안\n"
            "- 총 공수(S/M/L/XL)\n"
            "- 단계별 일정(분석/개발/테스트/배포)\n"
            "- 선행조건\n\n"
            "## 8. 개발팀 실행 체크리스트\n"
            "- [ ] 명확화 이슈 확정\n"
            "- [ ] DB 변경안 리뷰\n"
            "- [ ] 보안 점검 항목 반영\n"
            "- [ ] 테스트 케이스 작성\n"
            "- [ ] 배포/롤백 계획 확정\n\n"
            "## 9. 품질 검사 결과\n"
            "| 에이전트 | 점수 | 피드백 |\n"
            "|---|---|---|\n"
            "| 종합 | - | - |\n"
        )
        profile_section = _build_profile_section(context.get("profile_context", ""))
        history_section = _build_history_section(context.get("history_context", []))

        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "다음 분석 결과를 바탕으로 개발팀이 바로 사용할 수 있는 마크다운 개발 분석서를 작성하세요.\n"
            "아래 템플릿 섹션과 표 구조를 반드시 유지하세요.\n"
            "모든 섹션은 실제 내용으로 채우고, 비어 있는 섹션은 '추가 확인 필요'로 명시하세요.\n"
            "지나치게 장황하지 않게 실무용으로 간결하게 작성하세요.\n\n"
            f"[출력 템플릿]\n{template}\n\n"
            f"{profile_section}"
            f"{history_section}"
            f"{examples_section}"
            f"[통합 컨텍스트]\n{context}"
            f"{KOREAN_SUFFIX}"
        )
        markdown = self.client.request_text(
            system_prompt="You are a technical documentation agent. Always respond in Korean only.",
            user_prompt=prompt,
        )
        context["documenter"] = {"markdown": markdown}
        return context
