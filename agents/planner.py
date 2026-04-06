import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient
from utils.context_builder import build_profile_section as _build_profile_section
from utils.context_builder import build_history_section as _build_history_section
from utils.context_builder import KOREAN_INSTRUCTION


class PlannerAgent:
    name = "Planner"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "", examples: list = None) -> Dict[str, Any]:
        print("[Planner] 분석 중...")
        document = context["input_document"]

        profile_section = _build_profile_section(context.get("profile_context", ""))
        history_section = _build_history_section(context.get("history_context", []))

        feedback_section = (
            f"\n\n[이전 분석 피드백 - 반드시 반영하세요]\n{feedback}" if feedback else ""
        )
        examples_section = ""
        if examples:
            examples_section = "\n\n[참고 예시 - 아래 예시와 동일한 수준으로 작성]\n"
            for i, ex in enumerate(examples[:2], 1):
                input_preview = ex.get("input_text", "")[:200]
                output_preview = ex.get("output_markdown", "")[:300]
                examples_section += f"\n예시 {i}:\n"
                examples_section += f"입력: {input_preview}...\n"
                examples_section += f"출력(일부): {output_preview}...\n"
        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "다음 요청 문서에서 핵심 요구사항/기능 목록/비기능 요구사항/모호점/명확화 질문을 추출하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"core_requirements": [], "functional_requirements": [], "non_functional_requirements": [], '
            '"ambiguities": [], "clarification_questions": []'
            "}\n\n"
            f"[요청 문서]\n{document}"
            f"{profile_section}"
            f"{history_section}"
            f"{examples_section}"
            f"{feedback_section}"
        )
        result = self.client.request_json(system_prompt="You are a senior planner agent. Always respond in Korean only.", user_prompt=prompt)
        context["planner"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("planner", {}), ensure_ascii=False, indent=2)
