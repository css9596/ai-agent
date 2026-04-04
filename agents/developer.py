import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient


class DeveloperAgent:
    name = "Developer"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print("[Developer] 분석 중...")
        planner_data = context.get("planner", {})
        prompt = (
            "기획 결과를 바탕으로 Java/JSP/jQuery/MyBatis 기준의 기술 스펙을 작성하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"technical_spec": [], "db_changes": [], "impacted_modules": [], "effort": "S|M|L|XL"'
            "}\n\n"
            f"[기획 결과]\n{json.dumps(planner_data, ensure_ascii=False)}"
        )
        result = self.client.request_json(system_prompt="You are a senior software developer agent.", user_prompt=prompt)
        context["developer"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("developer", {}), ensure_ascii=False, indent=2)
