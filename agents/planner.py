import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient


class PlannerAgent:
    name = "Planner"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "") -> Dict[str, Any]:
        print("[Planner] 분석 중...")
        document = context["input_document"]
        feedback_section = (
            f"\n\n[이전 분석 피드백 - 반드시 반영하세요]\n{feedback}" if feedback else ""
        )
        prompt = (
            "다음 요청 문서에서 핵심 요구사항/기능 목록/비기능 요구사항/모호점/명확화 질문을 추출하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"core_requirements": [], "functional_requirements": [], "non_functional_requirements": [], '
            '"ambiguities": [], "clarification_questions": []'
            "}\n\n"
            f"[요청 문서]\n{document}"
            f"{feedback_section}"
        )
        result = self.client.request_json(system_prompt="You are a senior planner agent.", user_prompt=prompt)
        context["planner"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("planner", {}), ensure_ascii=False, indent=2)
