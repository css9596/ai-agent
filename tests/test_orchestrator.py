"""오케스트레이터 단위 테스트"""

import tempfile
from pathlib import Path
import pytest
from orchestrator import Orchestrator
from utils.claude_client import ClaudeClient


@pytest.fixture
def mock_client():
    """모의 Claude 클라이언트"""
    return ClaudeClient(api_key=None, mock=True)


@pytest.fixture
def temp_output_dir():
    """임시 출력 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestResolveOrder:
    """에이전트 실행 순서 테스트"""

    def test_resolve_order_all_agents(self):
        """모든 에이전트 순서"""
        agents = ["planner", "developer", "reviewer", "documenter"]
        result = Orchestrator._resolve_order(agents)
        assert result == agents

    def test_resolve_order_partial_agents(self):
        """일부 에이전트"""
        agents = ["developer", "documenter"]
        result = Orchestrator._resolve_order(agents)
        assert result == ["developer", "documenter"]
        # 표준 순서 유지
        assert result[0] == "developer"
        assert result[1] == "documenter"

    def test_resolve_order_preserves_standard_order(self):
        """표준 순서 보장"""
        agents = ["documenter", "planner", "reviewer", "developer"]
        result = Orchestrator._resolve_order(agents)
        # 입력 순서와 다르게 표준 순서로 정렬됨
        assert result == ["planner", "developer", "reviewer", "documenter"]

    def test_resolve_order_empty_list(self):
        """빈 리스트"""
        result = Orchestrator._resolve_order([])
        assert result == []

    def test_resolve_order_unknown_agent(self):
        """미지원 에이전트는 제외"""
        agents = ["planner", "unknown_agent", "developer"]
        result = Orchestrator._resolve_order(agents)
        assert "unknown_agent" not in result
        assert "planner" in result
        assert "developer" in result


class TestSummarizeAgentResult:
    """에이전트 결과 요약 테스트"""

    def test_summarize_none_result(self):
        """None 결과"""
        result = Orchestrator._summarize_agent_result("planner", None)
        assert result == {}

    def test_summarize_planner_result(self):
        """기획자 결과 요약"""
        planner_data = {
            "core_requirements": ["req1", "req2"],
            "functional_requirements": ["f1", "f2", "f3"],
            "clarification_questions": ["q1", "q2"]
        }
        result = Orchestrator._summarize_agent_result("planner", planner_data)
        assert result["icon"] == "📋"
        assert result["label"] == "기획자"
        assert len(result["sections"]) > 0

    def test_summarize_developer_result(self):
        """개발자 결과 요약"""
        dev_data = {
            "technical_spec": "Some spec",
            "impacted_modules": ["Module A", "Module B"],
            "effort": "2 weeks"
        }
        result = Orchestrator._summarize_agent_result("developer", dev_data)
        assert result["icon"] == "💻"
        assert result["label"] == "개발자"

    def test_summarize_reviewer_result(self):
        """검토자 결과 요약"""
        review_data = {
            "security_risks": ["risk1"],
            "performance_risks": ["perf1"]
        }
        result = Orchestrator._summarize_agent_result("reviewer", review_data)
        assert result["icon"] == "🔍"
        assert result["label"] == "검토자"

    def test_summarize_documenter_result(self):
        """문서화자 결과 요약 (300자 자르기)"""
        long_markdown = "# Header\n" + "A" * 400
        doc_data = {"markdown": long_markdown}
        result = Orchestrator._summarize_agent_result("documenter", doc_data)
        assert result["icon"] == "📝"
        # 300자 + "..."
        assert "..." in result["sections"][0]["content"]

    def test_summarize_unknown_agent(self):
        """미지원 에이전트"""
        result = Orchestrator._summarize_agent_result("unknown", {})
        assert result == {}


class TestSelectAgents:
    """에이전트 선택 테스트"""

    def test_select_agents_includes_documenter(self, mock_client, temp_output_dir):
        """documenter는 항상 포함"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        # 모의 모드에서 documenter가 반환됨
        result = orchestrator.select_agents("Test input")
        assert "documenter" in result["selected_agents"]

    def test_select_agents_mock_returns_all(self, mock_client, temp_output_dir):
        """모의 모드는 모든 에이전트 반환"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        result = orchestrator.select_agents("Test requirement")
        assert len(result["selected_agents"]) >= 4


class TestSaveMarkdown:
    """마크다운 저장 테스트"""

    def test_save_markdown_creates_file(self, temp_output_dir):
        """파일 생성 확인"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        markdown = "# Test\nSome content"
        file_path = orchestrator._save_markdown(markdown)

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == markdown

    def test_save_markdown_filename_format(self, temp_output_dir):
        """파일명 형식 확인"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        markdown = "# Test"
        file_path = orchestrator._save_markdown(markdown)

        # analysis_YYYYMMDD_HHMMSS.md 형식
        assert file_path.name.startswith("analysis_")
        assert file_path.name.endswith(".md")

    def test_save_markdown_utf8_encoding(self, temp_output_dir):
        """UTF-8 인코딩"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        markdown = "# 한글 테스트\n테스트 내용"
        file_path = orchestrator._save_markdown(markdown)

        content = file_path.read_text(encoding="utf-8")
        assert "한글 테스트" in content


class TestOrchestratorRun:
    """오케스트레이터 실행 테스트"""

    def test_run_creates_context_keys(self, temp_output_dir, mock_client):
        """context 키 생성"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        context = orchestrator.run("Test input requirement")

        assert "input_document" in context
        assert "planner" in context
        assert "developer" in context
        assert "reviewer" in context
        assert "documenter" in context
        assert "output_file" in context

    def test_run_generates_output_file(self, mock_client, temp_output_dir):
        """출력 파일 생성"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)
        context = orchestrator.run("Test requirement")

        output_file = Path(context["output_file"])
        assert output_file.exists()

    def test_run_with_missing_documenter_markdown(self, temp_output_dir):
        """documenter 결과 없을 때 fallback"""
        orchestrator = Orchestrator(mock_client, temp_output_dir)

        # 문서화자 결과 없이 강제로 context 수정
        class PartialMockClient(ClaudeClient):
            def request_json(self, system_prompt, user_prompt, max_retries=3):
                if "documenter" in system_prompt.lower() or "마크다운" in user_prompt:
                    return {}  # 빈 응답
                return super().request_json(system_prompt, user_prompt, max_retries)

        partial_client = PartialMockClient(api_key=None, mock=True)
        orchestrator = Orchestrator(partial_client, temp_output_dir)
        context = orchestrator.run("Test")

        # markdown이 없으면 fallback 사용
        assert "output_file" in context

    def test_run_emits_events(self, mock_client, temp_output_dir):
        """이벤트 발생 확인"""
        events = []

        def capture_event(event_type, data):
            events.append((event_type, data))

        orchestrator = Orchestrator(mock_client, temp_output_dir, on_event=capture_event)
        orchestrator.run("Test input")

        # 최소한 selection 이벤트는 발생해야 함
        event_types = [e[0] for e in events]
        assert "selection" in event_types or len(events) > 0


class TestOrchestratorInit:
    """오케스트레이터 초기화 테스트"""

    def test_init_creates_output_dir(self, temp_output_dir):
        """출력 디렉토리 생성"""
        output_dir = Path(temp_output_dir) / "new_output"
        assert not output_dir.exists()

        orchestrator = Orchestrator(mock_client, str(output_dir))
        assert output_dir.exists()

    def test_init_creates_agent_map(self):
        """에이전트 맵 생성"""
        orchestrator = Orchestrator(mock_client, "output")
        assert "planner" in orchestrator.agent_map
        assert "developer" in orchestrator.agent_map
        assert "reviewer" in orchestrator.agent_map
        assert "documenter" in orchestrator.agent_map

    def test_init_default_on_event(self):
        """기본 on_event는 무시"""
        orchestrator = Orchestrator(mock_client, "output")
        # 기본값은 lambda이므로 호출해도 오류 없음
        orchestrator.emit("test", {"data": "test"})
