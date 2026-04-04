import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents.developer import DeveloperAgent
from agents.documenter import DocumenterAgent
from agents.planner import PlannerAgent
from agents.reviewer import ReviewerAgent
from utils.claude_client import ClaudeClient


class Orchestrator:
    def __init__(self, client: ClaudeClient, output_dir: str = "output", on_event: Optional[Callable] = None) -> None:
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent_map = {
            "planner": PlannerAgent(client),
            "developer": DeveloperAgent(client),
            "reviewer": ReviewerAgent(client),
            "documenter": DocumenterAgent(client),
        }
        self.emit = on_event or (lambda t, d: None)

    def select_agents(self, document: str) -> Dict[str, Any]:
        self.emit("status", {"agent": "orchestrator", "message": "에이전트 선택 중..."})
        prompt = (
            "입력 문서를 분석해 필요한 전문가 에이전트를 선택하세요.\n"
            "사용 가능한 에이전트: planner, developer, reviewer, documenter\n"
            "반드시 JSON으로만 답변하세요.\n"
            '형식: {"selected_agents": [...], "reason": "..."}\n\n'
            f"[입력 문서]\n{document}"
        )
        selection = self.client.request_json(system_prompt="You are an orchestrator agent.", user_prompt=prompt)
        selected_agents = selection.get("selected_agents", [])
        if "documenter" not in selected_agents:
            selected_agents.append("documenter")
        selection["selected_agents"] = [a for a in selected_agents if a in self.agent_map]
        self.emit("selection", {"agents": selection["selected_agents"]})
        return selection

    def run(self, document: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {"input_document": document}
        selection = self.select_agents(document)
        context["orchestrator"] = selection

        ordered = self._resolve_order(selection["selected_agents"])
        for agent_name in ordered:
            self.emit("agent_start", {"agent": agent_name})
            context = self.agent_map[agent_name].run(context)
            result = context.get(agent_name)
            self.emit("agent_done", {"agent": agent_name, "result": result})

            # 중간 결과 상세 정보 전송 (UI에서 탭 표시용)
            agent_summary = self._summarize_agent_result(agent_name, result)
            self.emit("agent_result", {
                "agent": agent_name,
                "summary": agent_summary,
                "data": result
            })

        markdown = context.get("documenter", {}).get("markdown", "# 결과 없음")
        file_path = self._save_markdown(markdown)
        context["output_file"] = str(file_path)
        self.emit("complete", {"output_file": file_path.name})
        return context

    @staticmethod
    def _resolve_order(selected_agents: List[str]) -> List[str]:
        standard_order = ["planner", "developer", "reviewer", "documenter"]
        return [name for name in standard_order if name in selected_agents]

    @staticmethod
    def _summarize_agent_result(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 결과를 UI 표시용으로 요약"""
        if not result:
            return {}

        if agent_name == "planner":
            return {
                "label": "기획자",
                "icon": "📋",
                "sections": [
                    {
                        "title": "핵심 요구사항",
                        "items": result.get("core_requirements", [])[:5]
                    },
                    {
                        "title": "기능 요구사항",
                        "items": result.get("functional_requirements", [])[:8]
                    },
                    {
                        "title": "명확화 질문",
                        "items": result.get("clarification_questions", [])[:3]
                    }
                ]
            }

        elif agent_name == "developer":
            return {
                "label": "개발자",
                "icon": "💻",
                "sections": [
                    {
                        "title": "기술 스택",
                        "items": [result.get("technical_spec", "정보 없음")]
                    },
                    {
                        "title": "영향 모듈",
                        "items": result.get("impacted_modules", [])
                    },
                    {
                        "title": "예상 작업량",
                        "items": [result.get("effort", "정보 없음")]
                    }
                ]
            }

        elif agent_name == "reviewer":
            return {
                "label": "검토자",
                "icon": "🔍",
                "sections": [
                    {
                        "title": "보안 리스크",
                        "items": result.get("security_risks", [])
                    },
                    {
                        "title": "성능 리스크",
                        "items": result.get("performance_risks", [])
                    },
                    {
                        "title": "일정 리스크",
                        "items": result.get("schedule_risks", [])
                    }
                ]
            }

        elif agent_name == "documenter":
            markdown = result.get("markdown", "")
            preview = markdown[:300] + "..." if len(markdown) > 300 else markdown
            return {
                "label": "문서화",
                "icon": "📝",
                "sections": [
                    {
                        "title": "마크다운 미리보기",
                        "content": preview
                    }
                ]
            }

        return {}

    def _save_markdown(self, markdown: str) -> Path:
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename
        file_path.write_text(markdown, encoding="utf-8")
        return file_path

    @staticmethod
    def pretty_selection(context: Dict[str, Any]) -> str:
        return json.dumps(context.get("orchestrator", {}), ensure_ascii=False, indent=2)
