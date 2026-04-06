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
from utils.context_builder import KOREAN_INSTRUCTION, strip_forbidden_text
from utils.logger import logger
from database import db

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
            f"{KOREAN_INSTRUCTION}\n\n"
            "아래 입력 문서를 분석하여 필요한 에이전트만 선택하세요.\n"
            "불필요한 에이전트는 제외해서 분석 시간을 단축하세요.\n\n"
            "사용 가능한 에이전트와 호출 기준:\n"
            "- planner: 기능/비기능 요구사항 추출 필요 시 (거의 항상 필요)\n"
            "- developer: 기술 설계, DB 설계, API 설계 필요 시\n"
            "- impact_analyzer: 기존 시스템 파일/클래스/쿼리 영향도 분석 필요 시 (수정/추가 요청)\n"
            "- reviewer: 보안·성능·일정 리스크 검토 필요 시 (중요도 높은 기능)\n\n"
            "quality_checker와 documenter는 항상 자동 포함됩니다.\n\n"
            "예시:\n"
            '- "간단한 버튼 색상 변경" → ["planner"]\n'
            '- "로그인 기능 추가" → ["planner", "developer", "reviewer"]\n'
            '- "기존 게시판에 파일첨부 추가" → ["planner", "developer", "impact_analyzer", "reviewer"]\n\n'
            "반드시 JSON으로만 답변하세요.\n"
            '형식: {"selected_agents": [...], "reason": "선택 이유 한 줄"}\n\n'
            f"[입력 문서]\n{document}"
        )
        selection = self.client.request_json(
            system_prompt="You are an orchestrator agent. Always respond in Korean only.",
            user_prompt=prompt,
        )
        selected_agents = selection.get("selected_agents", list(ANALYSIS_ORDER))
        # 빈 결과 방어 처리
        if not selected_agents:
            selected_agents = list(ANALYSIS_ORDER)
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

        # AI 비서 컨텍스트 로드 (프로필 + 히스토리 + 학습 예시)
        examples = db.get_training_examples(limit=2)
        context["profile_context"] = db.get_all_profile()
        context["history_context"] = db.get_recent_context_analyses(limit=3)

        # 선택된 에이전트를 실행 순서대로 정렬 (quality_checker, documenter 제외)
        analysis_agents = [
            a for a in ANALYSIS_ORDER
            if a in selection.get("selected_agents", ANALYSIS_ORDER)
        ]
        if not analysis_agents:
            analysis_agents = list(ANALYSIS_ORDER)

        self.emit("status", {
            "agent": "orchestrator",
            "message": f"실행 에이전트: {', '.join(analysis_agents)} → quality_checker → documenter",
        })

        # 1단계: 선택된 분석 에이전트 순차 실행
        for agent_name in analysis_agents:
            context = self._run_agent(agent_name, context, examples=examples)

        # 2단계: 품질 검사 루프 (최대 MAX_RETRIES회 재시도)
        for attempt in range(MAX_RETRIES + 1):
            context = self._run_agent("quality_checker", context)
            qc = context.get("quality_checker", {})
            score = qc.get("total_score", 0)
            agent_scores = qc.get("agent_scores", {})
            # agent_scores가 dict가 아닌 경우 방어 처리 (LLM이 예상치 못한 형태로 반환 시)
            if not isinstance(agent_scores, dict):
                agent_scores = {}

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

            # 재시도: 낮은 점수 에이전트 피드백과 함께 재실행
            retry_agents = [a for a in qc.get("retry_agents", []) if a in analysis_agents]

            # retry_agents가 비어 있어도 점수 미달이면 점수 낮은 순으로 자동 선택
            if not retry_agents:
                scored = [
                    (a, agent_scores.get(a, {}).get("score", 0) if isinstance(agent_scores.get(a), dict) else 0)
                    for a in analysis_agents
                ]
                retry_agents = [a for a, s in scored if s < QUALITY_THRESHOLD]
                if not retry_agents:
                    retry_agents = [min(scored, key=lambda x: x[1])[0]]

            self.emit("status", {
                "agent": "quality_checker",
                "message": (
                    f"🔄 품질 점수 {score}점 (기준 {QUALITY_THRESHOLD}점) — "
                    f"{[a for a in retry_agents]} 재실행 (시도 {attempt + 1}/{MAX_RETRIES})"
                ),
            })

            self._emit_retry_feedback(retry_agents, agent_scores)

            # 가장 앞 순서 에이전트부터 피드백 반영 재실행 → 이후 에이전트 연쇄 재실행
            for agent_name in analysis_agents:
                if agent_name not in retry_agents:
                    continue
                score_data_f = agent_scores.get(agent_name, {})
                feedback = score_data_f.get("feedback", "") if isinstance(score_data_f, dict) else ""
                context = self._run_agent(agent_name, context, feedback=feedback, examples=examples)

                idx = analysis_agents.index(agent_name)
                for downstream in analysis_agents[idx + 1:]:
                    # 다운스트림도 해당 피드백이 있으면 반영
                    ds_score_data = agent_scores.get(downstream, {})
                    ds_feedback = ds_score_data.get("feedback", "") if isinstance(ds_score_data, dict) else ""
                    context = self._run_agent(downstream, context, feedback=ds_feedback, examples=examples)
                break  # 가장 앞 에이전트 재실행 → 나머지는 연쇄 재실행으로 커버

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
        if not agent_scores or not isinstance(agent_scores, dict):
            return

        # 헤더 메시지
        self.emit("status", {
            "agent": "quality_checker",
            "message": f"📊 [Quality Check] 점수: {total_score}점 (기준: {QUALITY_THRESHOLD}점)",
        })

        # 각 에이전트의 점수와 피드백 표시
        for agent_name in list(agent_scores.keys()):
            if agent_name not in agent_scores:
                continue

            score_data = agent_scores[agent_name]
            # score_data가 dict이 아닌 경우 방어 처리 (LLM이 list 등으로 반환 시)
            if not isinstance(score_data, dict):
                score_data = {}
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

            score_data_r = agent_scores.get(agent_name, {})
            if not isinstance(score_data_r, dict):
                score_data_r = {}
            feedback = score_data_r.get("feedback", "")
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
        logger.info(f"에이전트 시작", agent=agent_name)
        agent = self.agent_map[agent_name]

        # 스트리밍 콜백 설정 (Ollama 실시간 출력용)
        def _stream_cb(full_text: str):
            self.emit("agent_thinking", {"agent": agent_name, "text": full_text})

        if hasattr(self.client, "_stream_cb"):
            self.client._stream_cb = _stream_cb

        try:
            if agent_name != "quality_checker":
                kwargs = {}
                if feedback:
                    kwargs["feedback"] = feedback
                if examples:
                    kwargs["examples"] = examples
                context = agent.run(context, **kwargs) if kwargs else agent.run(context)
            else:
                context = agent.run(context)
        except Exception as exc:
            logger.error(f"에이전트 오류", agent=agent_name, error=str(exc))
            raise
        finally:
            if hasattr(self.client, "_stream_cb"):
                self.client._stream_cb = None

        result = context.get(agent_name)
        logger.info(f"에이전트 완료", agent=agent_name)
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
    def _to_list(value, limit: int = None) -> list:
        """LLM이 list/dict/str 등 다양한 형태로 반환할 때 안전하게 문자열 list로 변환"""
        if isinstance(value, list):
            raw = value
        elif isinstance(value, dict):
            raw = list(value.values())
        elif isinstance(value, str):
            raw = [value] if value else []
        else:
            raw = []

        # 각 항목도 문자열로 정규화 (list 안에 dict/list가 있을 경우)
        result = []
        for item in raw:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # 대표 키 순서로 텍스트 추출
                for key in ("content", "description", "requirement", "text", "name", "title", "value", "item"):
                    if key in item and isinstance(item[key], str):
                        result.append(item[key])
                        break
                else:
                    # 대표 키 없으면 첫 번째 str 값 사용
                    str_vals = [str(v) for v in item.values() if v is not None]
                    result.append(" | ".join(str_vals[:2]) if str_vals else "")
            else:
                result.append(str(item))

        # 금지 언어(아랍어·중국어·일본어) 필터링
        result = [strip_forbidden_text(r) for r in result]
        result = [r for r in result if r.strip()]
        return result[:limit] if limit else result

    @staticmethod
    def _summarize_agent_result(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 결과를 UI 표시용으로 요약"""
        if not result or not isinstance(result, dict):
            return {}

        to_list = Orchestrator._to_list

        if agent_name == "planner":
            return {
                "label": "기획자",
                "icon": "📋",
                "sections": [
                    {"title": "핵심 요구사항", "items": to_list(result.get("core_requirements"), 5)},
                    {"title": "기능 요구사항", "items": to_list(result.get("functional_requirements"), 8)},
                    {"title": "명확화 질문", "items": to_list(result.get("clarification_questions"), 3)},
                ],
            }

        if agent_name == "developer":
            return {
                "label": "개발자",
                "icon": "💻",
                "sections": [
                    {"title": "기술 스택", "items": to_list(result.get("technical_spec"), 5)},
                    {"title": "영향 모듈", "items": to_list(result.get("impacted_modules"))},
                    {"title": "예상 작업량", "items": [str(result.get("effort", "정보 없음"))]},
                ],
            }

        if agent_name == "impact_analyzer":
            summary = result.get("impact_summary", {})
            if not isinstance(summary, dict):
                summary = {}
            file_impacts = result.get("file_impacts", {})
            if not isinstance(file_impacts, dict):
                file_impacts = {}
            affected_files = []
            for layer, items in file_impacts.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
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
                    {"title": "변경 연쇄", "items": [str(result.get("dependency_chain", ""))]},
                ],
            }

        if agent_name == "reviewer":
            return {
                "label": "검토자",
                "icon": "🔍",
                "sections": [
                    {"title": "보안 리스크", "items": to_list(result.get("security_risks"))},
                    {"title": "성능 리스크", "items": to_list(result.get("performance_risks"))},
                    {"title": "일정 리스크", "items": to_list(result.get("schedule_risks"))},
                ],
            }

        if agent_name == "quality_checker":
            qc = result or {}
            agent_scores = qc.get("agent_scores", {})
            if not isinstance(agent_scores, dict):
                agent_scores = {}
            score_items = [
                f"{a}: {v.get('score', 0) if isinstance(v, dict) else v}점"
                for a, v in agent_scores.items()
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
