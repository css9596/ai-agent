"""Claude API 클라이언트 단위 테스트"""

import json
import pytest
from utils.claude_client import ClaudeClient


class TestParseJsonSafely:
    """JSON 파싱 안정성 테스트"""

    def test_parse_clean_json(self):
        """순수 JSON 문자열 파싱"""
        text = '{"key": "value", "number": 42}'
        result = ClaudeClient._parse_json_safely(text)
        assert result == {"key": "value", "number": 42}

    def test_parse_fenced_json(self):
        """마크다운 펜스 처리"""
        text = "```json\n{\"key\": \"value\"}\n```"
        result = ClaudeClient._parse_json_safely(text)
        assert result == {"key": "value"}

    def test_parse_embedded_json(self):
        """산문에 내장된 JSON 추출"""
        text = "다음은 분석 결과입니다:\n{\"analysis\": \"complete\"}\n참고용"
        result = ClaudeClient._parse_json_safely(text)
        assert result == {"analysis": "complete"}

    def test_parse_no_json_found(self):
        """JSON 없을 때 에러"""
        text = "This is plain text with no JSON"
        with pytest.raises(json.JSONDecodeError):
            ClaudeClient._parse_json_safely(text)

    def test_parse_malformed_json_in_fence(self):
        """펜스 내 손상된 JSON"""
        text = "```json\n{invalid json}\n```"
        with pytest.raises(json.JSONDecodeError):
            ClaudeClient._parse_json_safely(text)

    def test_parse_complex_nested_json(self):
        """복잡한 중첩 JSON"""
        text = '{"outer": {"inner": [1, 2, 3]}, "array": ["a", "b"]}'
        result = ClaudeClient._parse_json_safely(text)
        assert result["outer"]["inner"] == [1, 2, 3]
        assert result["array"] == ["a", "b"]


class TestMockJsonResponse:
    """모의 JSON 응답 테스트"""

    def test_mock_orchestrator_response(self):
        """오케스트레이터 모의 응답"""
        system_prompt = "You are orchestrator"
        user_prompt = "Select agents from input"
        result = ClaudeClient._mock_json_response(system_prompt, user_prompt)

        assert "selected_agents" in result
        assert "reason" in result
        assert isinstance(result["selected_agents"], list)

    def test_mock_planner_response(self):
        """기획자 모의 응답"""
        system_prompt = "You are planner"
        user_prompt = "Analyze requirements"
        result = ClaudeClient._mock_json_response(system_prompt, user_prompt)

        assert "core_requirements" in result
        assert "functional_requirements" in result
        assert "non_functional_requirements" in result
        assert "clarification_questions" in result

    def test_mock_developer_response(self):
        """개발자 모의 응답"""
        system_prompt = "You are developer"
        user_prompt = "Design technical solution"
        result = ClaudeClient._mock_json_response(system_prompt, user_prompt)

        assert "technical_spec" in result
        assert "db_changes" in result
        assert "impacted_modules" in result

    def test_mock_reviewer_response(self):
        """검토자 모의 응답"""
        system_prompt = "You are reviewer"
        user_prompt = "Review risks"
        result = ClaudeClient._mock_json_response(system_prompt, user_prompt)

        assert "cross_review" in result
        assert "security_risks" in result
        assert "performance_risks" in result

    def test_mock_default_response(self):
        """기본 모의 응답"""
        system_prompt = "Unknown system prompt"
        user_prompt = "Unknown prompt"
        result = ClaudeClient._mock_json_response(system_prompt, user_prompt)

        assert "message" in result


class TestMockTextResponse:
    """모의 텍스트 응답 테스트"""

    def test_mock_text_returns_markdown(self):
        """텍스트 응답은 마크다운"""
        result = ClaudeClient._mock_text_response("", "")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result  # 마크다운 헤더 포함


class TestClientInitialization:
    """클라이언트 초기화 테스트"""

    def test_mock_mode_no_client(self):
        """모의 모드는 API 클라이언트 생성 안 함"""
        client = ClaudeClient(api_key=None, mock=True)
        assert client.mock is True
        assert client._client is None

    def test_mock_false_no_api_key(self):
        """API 키 없이 모의 모드 아닐 때"""
        client = ClaudeClient(api_key=None, mock=False)
        assert client._client is None

    def test_model_override(self):
        """모델 선택"""
        client = ClaudeClient(api_key=None, model="claude-custom", mock=True)
        assert client.model == "claude-custom"


class TestRequestJson:
    """request_json 메서드 테스트"""

    def test_request_json_mock_mode(self):
        """모의 모드에서 JSON 반환"""
        client = ClaudeClient(api_key=None, mock=True)
        result = client.request_json(
            system_prompt="You are planner",
            user_prompt="Analyze"
        )
        assert isinstance(result, dict)
        assert "core_requirements" in result

    def test_request_json_different_agents(self):
        """다양한 에이전트 모의 응답"""
        client = ClaudeClient(api_key=None, mock=True)

        # 기획자
        result = client.request_json("planner", "analyze")
        assert "functional_requirements" in result

        # 개발자
        result = client.request_json("developer", "design")
        assert "technical_spec" in result

        # 검토자
        result = client.request_json("reviewer", "review")
        assert "security_risks" in result


class TestRequestText:
    """request_text 메서드 테스트"""

    def test_request_text_mock_mode(self):
        """모의 모드에서 텍스트 반환"""
        client = ClaudeClient(api_key=None, mock=True)
        result = client.request_text(
            system_prompt="Generate markdown",
            user_prompt="Create documentation"
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestExtractText:
    """_extract_text 정적 메서드 테스트"""

    def test_extract_text_single_block(self):
        """단일 텍스트 블록"""
        # 간단한 mock 객체 생성
        class MockContent:
            def __init__(self):
                self.type = "text"
                self.text = "Hello world"

        class MockResponse:
            def __init__(self):
                self.content = [MockContent()]

        response = MockResponse()
        result = ClaudeClient._extract_text(response)
        assert result == "Hello world"

    def test_extract_text_multiple_blocks(self):
        """여러 텍스트 블록 결합"""
        class MockContent:
            def __init__(self, text):
                self.type = "text"
                self.text = text

        class MockResponse:
            def __init__(self):
                self.content = [
                    MockContent("First block"),
                    MockContent("Second block")
                ]

        response = MockResponse()
        result = ClaudeClient._extract_text(response)
        assert "First block" in result
        assert "Second block" in result

    def test_extract_text_empty(self):
        """빈 응답"""
        class MockResponse:
            def __init__(self):
                self.content = []

        response = MockResponse()
        result = ClaudeClient._extract_text(response)
        assert result == ""
