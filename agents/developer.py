import json
from typing import Any, Dict

from utils.claude_client import ClaudeClient
from utils.context_builder import build_profile_section as _build_profile_section
from utils.context_builder import build_history_section as _build_history_section
from utils.context_builder import KOREAN_INSTRUCTION, KOREAN_SUFFIX


class DeveloperAgent:
    name = "Developer"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], feedback: str = "", examples: list = None) -> Dict[str, Any]:
        print("[Developer] 분석 중...")
        planner_data = context.get("planner", {})

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
            f"{KOREAN_INSTRUCTION}"
            f"{feedback_section}"
            "\n\n기획 결과를 바탕으로 Java/JSP/jQuery/MyBatis 기준의 기술 스펙을 작성하세요.\n"
            "DB 설계 시 인덱스 전략과 파일 저장 경로 관리 방식도 포함하세요.\n"
            "반드시 JSON으로만 답변하세요.\n"
            "스키마:\n"
            "{"
            '"technical_spec": [], "db_changes": [], "impacted_modules": [], "effort": "S|M|L|XL"'
            "}\n\n"
            f"[기획 결과]\n{json.dumps(planner_data, ensure_ascii=False)}"
            f"{profile_section}"
            f"{history_section}"
            f"{examples_section}"
            f"{KOREAN_SUFFIX}"
        )
        result = self.client.request_json(system_prompt="You are a senior software developer agent. Always respond in Korean only.", user_prompt=prompt)
        context["developer"] = result
        return context

    @staticmethod
    def pretty(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("developer", {}), ensure_ascii=False, indent=2)
