"""AI 에이전트 단위 테스트"""

import json
import pytest
from agents.planner import PlannerAgent
from agents.developer import DeveloperAgent
from agents.reviewer import ReviewerAgent
from agents.documenter import DocumenterAgent
from utils.claude_client import ClaudeClient


@pytest.fixture
def mock_client():
    """모의 Claude 클라이언트"""
    return ClaudeClient(api_key=None, mock=True)


@pytest.fixture
def sample_context():
    """샘플 컨텍스트"""
    return {
        "input_document": "게시판에 파일 첨부 기능을 추가해주세요"
    }


class TestPlannerAgent:
    """기획자 에이전트 테스트"""

    def test_planner_run_stores_result(self, mock_client, sample_context):
        """run 메서드가 결과를 저장"""
        agent = PlannerAgent(mock_client)
        result_context = agent.run(sample_context)

        assert "planner" in result_context
        assert isinstance(result_context["planner"], dict)

    def test_planner_run_required_keys(self, mock_client, sample_context):
        """기획자 결과에 필수 키 포함"""
        agent = PlannerAgent(mock_client)
        result_context = agent.run(sample_context)

        planner_result = result_context["planner"]
        assert "core_requirements" in planner_result
        assert "functional_requirements" in planner_result
        assert "non_functional_requirements" in planner_result

    def test_planner_returns_context(self, mock_client, sample_context):
        """원본 context 반환"""
        agent = PlannerAgent(mock_client)
        result_context = agent.run(sample_context)

        assert "input_document" in result_context
        assert result_context["input_document"] == sample_context["input_document"]

    def test_planner_pretty_existing_key(self, mock_client, sample_context):
        """pretty() - 기획자 결과 있을 때"""
        agent = PlannerAgent(mock_client)
        context = agent.run(sample_context)
        pretty_str = agent.pretty(context)

        assert isinstance(pretty_str, str)
        parsed = json.loads(pretty_str)
        assert "core_requirements" in parsed

    def test_planner_pretty_missing_key(self, mock_client):
        """pretty() - 기획자 결과 없을 때"""
        agent = PlannerAgent(mock_client)
        pretty_str = agent.pretty({})

        assert pretty_str == "{}"

    def test_planner_handles_empty_input(self, mock_client):
        """빈 input_document 처리"""
        agent = PlannerAgent(mock_client)
        context = {"input_document": ""}
        result_context = agent.run(context)

        assert "planner" in result_context


class TestDeveloperAgent:
    """개발자 에이전트 테스트"""

    def test_developer_run_stores_result(self, mock_client, sample_context):
        """run 메서드가 결과를 저장"""
        # 먼저 planner 실행
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        # 개발자 실행
        agent = DeveloperAgent(mock_client)
        result_context = agent.run(context)

        assert "developer" in result_context
        assert isinstance(result_context["developer"], dict)

    def test_developer_run_required_keys(self, mock_client, sample_context):
        """개발자 결과에 필수 키 포함"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        result_context = developer.run(context)

        dev_result = result_context["developer"]
        assert "technical_spec" in dev_result
        assert "impacted_modules" in dev_result

    def test_developer_without_planner(self, mock_client):
        """planner 결과 없이 실행"""
        agent = DeveloperAgent(mock_client)
        context = {}
        result_context = agent.run(context)

        assert "developer" in result_context

    def test_developer_pretty(self, mock_client, sample_context):
        """pretty() 메서드"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)
        pretty_str = developer.pretty(context)

        assert isinstance(pretty_str, str)
        parsed = json.loads(pretty_str)
        assert "technical_spec" in parsed


class TestReviewerAgent:
    """검토자 에이전트 테스트"""

    def test_reviewer_run_stores_result(self, mock_client, sample_context):
        """run 메서드가 결과를 저장"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        agent = ReviewerAgent(mock_client)
        result_context = agent.run(context)

        assert "reviewer" in result_context
        assert isinstance(result_context["reviewer"], dict)

    def test_reviewer_run_required_keys(self, mock_client, sample_context):
        """검토자 결과에 필수 키 포함"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        reviewer = ReviewerAgent(mock_client)
        result_context = reviewer.run(context)

        review_result = result_context["reviewer"]
        assert "security_risks" in review_result
        assert "performance_risks" in review_result

    def test_reviewer_without_upstream(self, mock_client):
        """upstream 결과 없이 실행"""
        agent = ReviewerAgent(mock_client)
        context = {}
        result_context = agent.run(context)

        assert "reviewer" in result_context

    def test_reviewer_pretty(self, mock_client, sample_context):
        """pretty() 메서드"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        reviewer = ReviewerAgent(mock_client)
        context = reviewer.run(context)
        pretty_str = reviewer.pretty(context)

        assert isinstance(pretty_str, str)
        parsed = json.loads(pretty_str)
        assert "security_risks" in parsed


class TestDocumenterAgent:
    """문서화자 에이전트 테스트"""

    def test_documenter_run_generates_markdown(self, mock_client, sample_context):
        """run 메서드가 마크다운 생성"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        reviewer = ReviewerAgent(mock_client)
        context = reviewer.run(context)

        agent = DocumenterAgent(mock_client)
        result_context = agent.run(context)

        assert "documenter" in result_context
        assert isinstance(result_context["documenter"], dict)

    def test_documenter_markdown_not_empty(self, mock_client, sample_context):
        """생성된 마크다운이 비어있지 않음"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        reviewer = ReviewerAgent(mock_client)
        context = reviewer.run(context)

        agent = DocumenterAgent(mock_client)
        result_context = agent.run(context)

        markdown = result_context["documenter"].get("markdown", "")
        assert len(markdown) > 0
        assert "#" in markdown  # 최소한 마크다운 헤더 포함

    def test_documenter_with_all_upstream(self, mock_client, sample_context):
        """모든 upstream 데이터와 함께 실행"""
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)

        reviewer = ReviewerAgent(mock_client)
        context = reviewer.run(context)

        agent = DocumenterAgent(mock_client)
        result_context = agent.run(context)

        # 모든 필수 upstream 데이터 확인
        assert "planner" in result_context
        assert "developer" in result_context
        assert "reviewer" in result_context
        assert "documenter" in result_context

    def test_documenter_with_minimal_context(self, mock_client):
        """최소한의 컨텍스트로 실행"""
        agent = DocumenterAgent(mock_client)
        context = {}
        result_context = agent.run(context)

        assert "documenter" in result_context


class TestAgentIntegration:
    """에이전트 통합 테스트"""

    def test_full_pipeline(self, mock_client, sample_context):
        """완전한 파이프라인"""
        # 기획자
        planner = PlannerAgent(mock_client)
        context = planner.run(sample_context)
        assert "planner" in context

        # 개발자
        developer = DeveloperAgent(mock_client)
        context = developer.run(context)
        assert "developer" in context

        # 검토자
        reviewer = ReviewerAgent(mock_client)
        context = reviewer.run(context)
        assert "reviewer" in context

        # 문서화자
        documenter = DocumenterAgent(mock_client)
        context = documenter.run(context)
        assert "documenter" in context

        # 모든 결과 확인
        assert isinstance(context["planner"], dict)
        assert isinstance(context["developer"], dict)
        assert isinstance(context["reviewer"], dict)
        assert isinstance(context["documenter"], dict)

    def test_context_accumulation(self, mock_client):
        """context 누적 확인"""
        context = {"input_document": "test requirement"}

        # 각 에이전트는 context를 수정하고 반환
        planner = PlannerAgent(mock_client)
        context = planner.run(context)
        context_keys_1 = set(context.keys())

        developer = DeveloperAgent(mock_client)
        context = developer.run(context)
        context_keys_2 = set(context.keys())

        # 새로운 키가 추가됨
        assert context_keys_2 > context_keys_1
        assert "developer" in context_keys_2
