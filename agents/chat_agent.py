import json
from typing import Any, Dict, List

from utils.claude_client import ClaudeClient
from utils.context_builder import KOREAN_INSTRUCTION


class ChatAgent:
    name = "ChatAgent"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(self, context: Dict[str, Any], message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        사용자 질문을 분석하고 답변을 생성합니다.
        변경 요청인 경우 ImpactAnalyzer를 재실행하여 영향도를 재분석합니다.

        Args:
            context: 기존 분석 결과 (planner, developer, impact_analyzer, reviewer)
            message: 사용자 질문
            chat_history: 이전 대화 히스토리

        Returns:
            {
                "type": "answer|reanalysis",
                "answer": "텍스트 답변",
                "requires_reanalysis": bool,
                "reanalyzed_impact": {...},  # 재분석 결과 (있을 때만)
                "follow_up_suggestions": ["질문1", "질문2", "질문3"]
            }
        """
        print("[ChatAgent] 질문 분석 중...")

        # 이전 대화 포맷팅
        history_text = self._format_chat_history(chat_history)

        # 기존 분석 결과 요약
        planner = context.get("planner", {})
        developer = context.get("developer", {})
        impact = context.get("impact_analyzer", {})
        reviewer = context.get("reviewer", {})

        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "사용자의 요구사항 정제 질문을 분석하세요.\n"
            "질문 유형을 판단하고 답변을 제공하세요.\n\n"
            "질문 분류:\n"
            "- 'answer': 기존 분석 결과를 바탕으로 설명 또는 제안 (예: '보안 위험은 뭔가요?', '왜 M 공수인가요?')\n"
            "- 'reanalysis': 기술/요구사항을 변경하는 질문, 영향도 재분석 필요 (예: 'S3로 바꾸면?', '파일 크기 100MB로 늘리면?')\n\n"
            "변경을 시사하는 키워드: 바꾸면, 변경, 추가, 제거, 분리, 통합, 늘리면, 줄이면, 다른 기술\n\n"
            "응답 형식 (JSON만):\n"
            "{\n"
            '  "type": "answer|reanalysis",\n'
            '  "requires_reanalysis": false,  # reanalysis일 때 true\n'
            '  "answer": "사용자 질문에 대한 구체적 답변",\n'
            '  "follow_up_suggestions": ["제안 질문1", "제안 질문2", "제안 질문3"]\n'
            "}\n\n"
            f"[대화 히스토리]\n{history_text}\n\n"
            f"[새 질문]\n{message}\n\n"
            f"[기존 분석 결과 요약]\n"
            f"Planner: {json.dumps(planner, ensure_ascii=False, default=str)[:500]}...\n"
            f"Developer: {json.dumps(developer, ensure_ascii=False, default=str)[:500]}...\n"
            f"Impact: {json.dumps(impact, ensure_ascii=False, default=str)[:500]}...\n"
            f"Reviewer: {json.dumps(reviewer, ensure_ascii=False, default=str)[:500]}...\n"
        )

        result = self.client.request_json(
            system_prompt="You are a helpful requirements refinement assistant. Analyze user questions and provide answers based on the analysis context. Always respond in Korean only.",
            user_prompt=prompt,
        )

        # 재분석이 필요한 경우 ImpactAnalyzer 재실행
        if result.get("requires_reanalysis"):
            print("[ChatAgent] ImpactAnalyzer 재실행 중...")
            from agents.impact_analyzer import ImpactAnalyzerAgent

            impact_agent = ImpactAnalyzerAgent(self.client)
            feedback = f"사용자 변경 요청: {message}\n기존 영향도를 바탕으로 변경된 부분만 재분석하세요."

            # 컨텍스트를 복사해서 재분석 실행 (원본 영향도는 유지)
            reanalysis_context = context.copy()
            reanalysis_context = impact_agent.run(reanalysis_context, feedback=feedback)

            # 재분석된 영향도를 결과에 포함
            result["reanalyzed_impact"] = reanalysis_context.get("impact_analyzer", {})

        return result

    @staticmethod
    def _format_chat_history(chat_history: List[Dict[str, str]]) -> str:
        """대화 히스토리를 텍스트로 포맷팅."""
        if not chat_history:
            return "(대화 히스토리 없음)"

        lines = []
        for msg in chat_history:
            role = "👤 사용자" if msg.get("role") == "user" else "🤖 어시스턴트"
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    @staticmethod
    def pretty(result: Dict[str, Any]) -> str:
        return json.dumps(result, ensure_ascii=False, indent=2)
