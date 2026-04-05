import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents.developer import DeveloperAgent
from agents.documenter import DocumenterAgent
from agents.impact_analyzer import ImpactAnalyzerAgent
from agents.planner import PlannerAgent
from agents.quality_checker import MAX_RETRIES, QUALITY_THRESHOLD, QualityCheckerAgent
from agents.reviewer import ReviewerAgent
from utils.claude_client import ClaudeClient
from database import Database

# 분석 에이전트 실행 순서 (documenter, quality_checker 제외)
ANALYSIS_ORDER = ["planner", "developer", "impact_analyzer", "reviewer"]


class Orchestrator:
    def __init__(self, client: ClaudeClient, output_dir: str = "output", on_event: Optional[Callable] = None) -> None:
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent_map = {
            "planner": PlannerAgent(client),
            "developer": DeveloperAgent(client),
            "impact_analyzer": ImpactAnalyzerAgent(client),
            "reviewer": ReviewerAgent(client),
            "quality_checker": QualityCheckerAgent(client),
            "documenter": DocumenterAgent(client),
        }
        self.emit = on_event or (lambda t, d: None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_agents(self, document: str) -> Dict[str, Any]:
        """입력 문서를 분석해 실행할 에이전트를 선택한다."""
        self.emit("status", {"agent": "orchestrator", "message": "에이전트 선택 중..."})
        prompt = (
            "입력 문서를 분석해 필요한 전문가 에이전트를 선택하세요.\n"
            "사용 가능한 에이전트: planner, developer, impact_analyzer, reviewer, documenter\n"
            "반드시 JSON으로만 답변하세요.\n"
            '형식: {"selected_agents": [...], "reason": "..."}\n\n'
            f"[입력 문서]\n{document}"
        )
        selection = self.client.request_json(
            system_prompt="You are an orchestrator agent.",
            user_prompt=prompt,
        )
        selected_agents = selection.get("selected_agents", [])
        # quality_checker, documenter는 항상 포함
        for required in ("quality_checker", "documenter"):
            if required not in selected_agents:
                selected_agents.append(required)
        selection["selected_agents"] = [a for a in selected_agents if a in self.agent_map]
        self.emit("selection", {"agents": selection["selected_agents"]})
        return selection

    def run(self, document: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {"input_document": document}
        selection = self.select_agents(document)
        context["orchestrator"] = selection

        # 학습 예시 조회
        db = Database()
        examples = db.get_training_examples(limit=2)

        # 1단계: 분석 에이전트 순차 실행
        for agent_name in ANALYSIS_ORDER:
            context = self._run_agent(agent_name, context, examples=examples)

        # 2단계: 품질 검사 루프 (최대 MAX_RETRIES회 재시도)
        for attempt in range(MAX_RETRIES + 1):
            context = self._run_agent("quality_checker", context)
            qc = context.get("quality_checker", {})
            score = qc.get("total_score", 0)
            agent_scores = qc.get("agent_scores", {})

            # 개별 에이전트 점수 표시
            self._emit_agent_scores(agent_scores, score)

            if qc.get("pass", True):
                self.emit("status", {
                    "agent": "quality_checker",
                    "message": f"✅ 품질 검사 통과 (점수: {score}점)",
                })
                break

            if attempt >= MAX_RETRIES:
                self.emit("status", {
                    "agent": "quality_checker",
                    "message": f"⚠️ 최대 재시도 초과, 현재 점수 {score}점으로 진행합니다.",
                })
                break

            # 재시도: 낮은 점수 에이전트만 피드백과 함께 재실행
            retry_agents = qc.get("retry_agents", [])
            self.emit("status", {
                "agent": "quality_checker",
                "message": (
                    f"🔄 품질 점수 {score}점 (기준 {QUALITY_THRESHOLD}점) — "
                    f"{retry_agents} 재실행 중... (시도 {attempt + 1}/{MAX_RETRIES})"
                ),
            })

            # 재시도 에이전트별 피드백 상세 표시
            self._emit_retry_feedback(retry_agents, agent_scores)

            for agent_name in ANALYSIS_ORDER:
                if agent_name not in retry_agents:
                    continue
                feedback = agent_scores.get(agent_name, {}).get("feedback", "")
                context = self._run_agent(agent_name, context, feedback=feedback, examples=examples)

                # 재실행된 에이전트 이후 에이전트들도 순서대로 다시 실행
                idx = ANALYSIS_ORDER.index(agent_name)
                for downstream in ANALYSIS_ORDER[idx + 1:]:
                    context = self._run_agent(downstream, context, examples=examples)
                break  # 가장 앞 순서 에이전트 1개씩 처리

        # 3단계: 문서화
        context = self._run_agent("documenter", context, examples=examples)

        markdown = context.get("documenter", {}).get("markdown", "# 결과 없음")
        file_path = self._save_markdown(markdown)
        context["output_file"] = str(file_path)
        self.emit("complete", {"output_file": file_path.name})
        return context

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_agent_scores(self, agent_scores: Dict[str, Any], total_score: int) -> None:
        """각 에이전트의 개별 점수와 피드백을 상세히 표시"""
        if not agent_scores:
            return

        # 헤더 메시지
        self.emit("status", {
            "agent": "quality_checker",
            "message": f"📊 [Quality Check] 점수: {total_score}점 (기준: {QUALITY_THRESHOLD}점)",
        })

        # 각 에이전트의 점수와 피드백 표시
        for agent_name in ANALYSIS_ORDER:
            if agent_name not in agent_scores:
                continue

            score_data = agent_scores[agent_name]
            agent_score = score_data.get("score", 0)
            feedback = score_data.get("feedback", "")

            # 점수에 따른 indicator 설정
            if agent_score >= 90:
                indicator = "✅"
            elif agent_score >= 80:
                indicator = "⚠️"
            else:
                indicator = "❌"

            # 에이전트 이름 매핑
            agent_label = {
                "planner": "기획자",
                "developer": "개발자",
                "impact_analyzer": "영향도 분석",
                "reviewer": "검토자",
            }.get(agent_name, agent_name)

            message = f"  ├─ {agent_label}: {agent_score}점 {indicator}"
            if feedback:
                message += f"\n     피드백: \"{feedback}\""

            self.emit("status", {
                "agent": "quality_checker",
                "message": message,
            })

    def _emit_retry_feedback(self, retry_agents: List[str], agent_scores: Dict[str, Any]) -> None:
        """재시도할 에이전트의 피드백을 상세히 표시"""
        if not retry_agents:
            return

        self.emit("status", {
            "agent": "quality_checker",
            "message": f"🔧 [Feedback 적용] 다음 에이전트 재실행 예정:",
        })

        for agent_name in retry_agents:
            agent_label = {
                "planner": "기획자",
                "developer": "개발자",
                "impact_analyzer": "영향도 분석",
                "reviewer": "검토자",
            }.get(agent_name, agent_name)

            feedback = agent_scores.get(agent_name, {}).get("feedback", "")
            if feedback:
                self.emit("status", {
                    "agent": "quality_checker",
                    "message": f"  ├─ {agent_label}: \"{feedback}\"",
                })
            else:
                self.emit("status", {
                    "agent": "quality_checker",
                    "message": f"  ├─ {agent_label}",
                })

    def _run_agent(self, agent_name: str, context: Dict[str, Any], feedback: str = "", examples: List[Dict] = None) -> Dict[str, Any]:
        """단일 에이전트 실행 + 이벤트 발행."""
        self.emit("agent_start", {"agent": agent_name})
        agent = self.agent_map[agent_name]

        # feedback/examples 지원 에이전트는 keyword argument로 전달
        if agent_name != "quality_checker":
            kwargs = {}
            if feedback:
                kwargs["feedback"] = feedback
            if examples:
                kwargs["examples"] = examples
            if kwargs:
                context = agent.run(context, **kwargs)
            else:
                context = agent.run(context)
        else:
            context = agent.run(context)

        result = context.get(agent_name)
        self.emit("agent_done", {"agent": agent_name, "result": result})
        agent_summary = self._summarize_agent_result(agent_name, result)
        self.emit("agent_result", {
            "agent": agent_name,
            "summary": agent_summary,
            "data": result,
        })
        return context

    @staticmethod
    def _resolve_order(selected_agents: List[str]) -> List[str]:
        standard_order = ["planner", "developer", "impact_analyzer", "reviewer", "quality_checker", "documenter"]
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
                    {"title": "핵심 요구사항", "items": result.get("core_requirements", [])[:5]},
                    {"title": "기능 요구사항", "items": result.get("functional_requirements", [])[:8]},
                    {"title": "명확화 질문", "items": result.get("clarification_questions", [])[:3]},
                ],
            }

        if agent_name == "developer":
            return {
                "label": "개발자",
                "icon": "💻",
                "sections": [
                    {"title": "기술 스택", "items": result.get("technical_spec", [])[:5]},
                    {"title": "영향 모듈", "items": result.get("impacted_modules", [])},
                    {"title": "예상 작업량", "items": [result.get("effort", "정보 없음")]},
                ],
            }

        if agent_name == "impact_analyzer":
            summary = result.get("impact_summary", {})
            file_impacts = result.get("file_impacts", {})
            affected_files = []
            for layer, items in file_impacts.items():
                for item in items:
                    change = "🆕" if item.get("change_type") == "NEW" else "✏️"
                    affected_files.append(f"{change} [{layer.upper()}] {item.get('file', '')}")
            return {
                "label": "영향도 분석",
                "icon": "🗺️",
                "sections": [
                    {
                        "title": f"영향 범위 ({summary.get('impact_level', '-')})",
                        "items": [
                            f"총 {summary.get('total_files', 0)}개 파일 "
                            f"(신규 {summary.get('new_files', 0)} / 수정 {summary.get('modified_files', 0)})"
                        ],
                    },
                    {"title": "파일 목록", "items": affected_files[:10]},
                    {"title": "변경 연쇄", "items": [result.get("dependency_chain", "")]},
                ],
            }

        if agent_name == "reviewer":
            return {
                "label": "검토자",
                "icon": "🔍",
                "sections": [
                    {"title": "보안 리스크", "items": result.get("security_risks", [])},
                    {"title": "성능 리스크", "items": result.get("performance_risks", [])},
                    {"title": "일정 리스크", "items": result.get("schedule_risks", [])},
                ],
            }

        if agent_name == "quality_checker":
            qc = result or {}
            agent_scores = qc.get("agent_scores", {})
            score_items = [
                f"{a}: {v.get('score', 0)}점" for a, v in agent_scores.items()
            ]
            status = "✅ 통과" if qc.get("pass") else "🔄 재시도 필요"
            return {
                "label": "품질 관리자",
                "icon": "🏆",
                "sections": [
                    {
                        "title": f"종합 점수: {qc.get('total_score', 0)}점 ({status})",
                        "items": score_items,
                    },
                    {"title": "종합 피드백", "items": [qc.get("overall_feedback", "")]},
                ],
            }

        if agent_name == "documenter":
            markdown = result.get("markdown", "")
            preview = markdown[:300] + "..." if len(markdown) > 300 else markdown
            return {
                "label": "문서화",
                "icon": "📝",
                "sections": [{"title": "마크다운 미리보기", "content": preview}],
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
