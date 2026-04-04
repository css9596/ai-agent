import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient

QUALITY_THRESHOLD = 95
MAX_RETRIES = 2


class QualityCheckerAgent:
    name = "QualityChecker"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print("[QualityChecker] 품질 검사 중...")
        planner_data = context.get("planner", {})
        developer_data = context.get("developer", {})
        impact_data = context.get("impact_analyzer", {})
        reviewer_data = context.get("reviewer", {})

        prompt = (
            "다음 멀티에이전트 분석 결과의 품질을 엄격하게 평가하세요.\n"
            "각 에이전트의 결과를 0~100점으로 채점하고 부족한 부분에 구체적인 피드백을 제공하세요.\n"
            "95점 미만인 에이전트는 반드시 retry_agents 목록에 포함하세요.\n"
            "total_score는 4개 에이전트 점수의 평균입니다.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{\n"
            '  "total_score": 0,\n'
            '  "pass": false,\n'
            '  "agent_scores": {\n'
            '    "planner":         {"score": 0, "feedback": ""},\n'
            '    "developer":       {"score": 0, "feedback": ""},\n'
            '    "impact_analyzer": {"score": 0, "feedback": ""},\n'
            '    "reviewer":        {"score": 0, "feedback": ""}\n'
            "  },\n"
            '  "retry_agents": [],\n'
            '  "overall_feedback": ""\n'
            "}\n\n"
            f"[기획 결과]\n{json.dumps(planner_data, ensure_ascii=False)}\n\n"
            f"[개발 분석 결과]\n{json.dumps(developer_data, ensure_ascii=False)}\n\n"
            f"[영향도 분석 결과]\n{json.dumps(impact_data, ensure_ascii=False)}\n\n"
            f"[검토 결과]\n{json.dumps(reviewer_data, ensure_ascii=False)}"
        )
        result = self.client.request_json(
            system_prompt="You are a strict quality assurance manager agent.",
            user_prompt=prompt,
        )

        # total_score 기준으로 pass 재계산 (Claude 응답 보정)
        total_score = result.get("total_score", 0)
        result["pass"] = total_score >= QUALITY_THRESHOLD
        if not result.get("retry_agents"):
            result["retry_agents"] = []

        context["quality_checker"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("quality_checker", {}), ensure_ascii=False, indent=2)
