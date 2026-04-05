import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient
from utils.context_builder import KOREAN_INSTRUCTION


class ImpactAnalyzerAgent:
    name = "ImpactAnalyzer"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "") -> Dict[str, Any]:
        print("[ImpactAnalyzer] 분석 중...")
        planner_data = context.get("planner", {})
        developer_data = context.get("developer", {})
        feedback_section = (
            f"\n\n[이전 분석 피드백 - 반드시 반영하세요]\n{feedback}" if feedback else ""
        )
        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "기획/개발 분석 결과를 바탕으로 Java/JSP/jQuery/MyBatis 프로젝트의 영향도를 분석하세요.\n"
            "각 레이어(Controller/Service/DAO/Mapper/JSP/JS)별로 변경·신규 파일과 메서드를 구체적으로 명시하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{\n"
            '  "impact_summary": {"total_files": 0, "new_files": 0, "modified_files": 0, "impact_level": "LOW|MEDIUM|HIGH"},\n'
            '  "db_changes": [{"table": "", "change_type": "NEW|ADD_COLUMN|MODIFY", "columns": [], "reason": ""}],\n'
            '  "file_impacts": {\n'
            '    "controller": [{"file": "", "change_type": "NEW|MODIFY", "methods": [], "reason": ""}],\n'
            '    "service":    [{"file": "", "change_type": "NEW|MODIFY", "methods": [], "reason": ""}],\n'
            '    "dao":        [{"file": "", "change_type": "NEW|MODIFY", "methods": [], "reason": ""}],\n'
            '    "mapper":     [{"file": "", "change_type": "NEW|MODIFY", "queries": [], "reason": ""}],\n'
            '    "jsp":        [{"file": "", "change_type": "NEW|MODIFY", "reason": ""}],\n'
            '    "javascript": [{"file": "", "change_type": "NEW|MODIFY", "reason": ""}]\n'
            "  },\n"
            '  "dependency_chain": "A → B → C 순서로 변경 필요한 연쇄 설명"\n'
            "}\n\n"
            f"[기획 결과]\n{json.dumps(planner_data, ensure_ascii=False)}\n\n"
            f"[개발 분석 결과]\n{json.dumps(developer_data, ensure_ascii=False)}"
            f"{feedback_section}"
        )
        result = self.client.request_json(
            system_prompt=(
                "You are a senior impact analysis agent "
                "specializing in Java/JSP/MyBatis enterprise systems. "
                "Always respond in Korean only."
            ),
            user_prompt=prompt,
        )
        context["impact_analyzer"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("impact_analyzer", {}), ensure_ascii=False, indent=2)
