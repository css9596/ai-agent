import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient


class ReviewerAgent:
    name = "Reviewer"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print("[Reviewer] 분석 중...")
        planner_data = context.get("planner", {})
        developer_data = context.get("developer", {})
        prompt = (
            "기획안과 개발 스펙을 교차 검토해서 누락 예외처리/보안/성능/일정 리스크를 도출하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"cross_review": [], "missing_exceptions": [], "security_risks": [], '
            '"performance_risks": [], "schedule_risks": []'
            "}\n\n"
            f"[기획]\n{json.dumps(planner_data, ensure_ascii=False)}\n\n"
            f"[개발]\n{json.dumps(developer_data, ensure_ascii=False)}"
        )
        result = self.client.request_json(system_prompt="You are a strict software reviewer agent.", user_prompt=prompt)
        context["reviewer"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("reviewer", {}), ensure_ascii=False, indent=2)
