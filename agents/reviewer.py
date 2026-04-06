import json
from typing import Any, Dict, List, Optional

from utils.claude_client import ClaudeClient
from utils.context_builder import KOREAN_INSTRUCTION


class ReviewerAgent:
    name = "Reviewer"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "", examples: Optional[List[Dict]] = None) -> Dict[str, Any]:
        print("[Reviewer] 분석 중...")
        planner_data = context.get("planner", {})
        developer_data = context.get("developer", {})
        impact_data = context.get("impact_analyzer", {})
        feedback_section = (
            f"\n\n[이전 분석 피드백 - 반드시 반영하세요]\n{feedback}" if feedback else ""
        )
        examples_section = ""
        if examples:
            examples_section = "\n\n[참고 예시 - 아래 예시와 동일한 수준의 품질로 작성]\n"
            for i, ex in enumerate(examples[:2], 1):
                title = ex.get("title", f"예시 {i}")
                output_preview = ex.get("output_markdown", "")[:400]
                examples_section += f"\n예시 {i} ({title}):\n{output_preview}...\n"
        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "기획안, 개발 스펙, 영향도 분석을 교차 검토해서 누락 예외처리/보안/성능/일정 리스크를 도출하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"cross_review": [], "missing_exceptions": [], "security_risks": [], '
            '"performance_risks": [], "schedule_risks": []'
            "}\n\n"
            f"[기획]\n{json.dumps(planner_data, ensure_ascii=False)}\n\n"
            f"[개발]\n{json.dumps(developer_data, ensure_ascii=False)}\n\n"
            f"[영향도]\n{json.dumps(impact_data, ensure_ascii=False)}"
            f"{examples_section}"
            f"{feedback_section}"
        )
        result = self.client.request_json(system_prompt="You are a strict software reviewer agent. Always respond in Korean only.", user_prompt=prompt)
        context["reviewer"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("reviewer", {}), ensure_ascii=False, indent=2)
