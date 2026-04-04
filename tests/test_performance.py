"""성능 벤치마크 테스트"""

import json
import time
import tempfile
from pathlib import Path
import pytest
from orchestrator import Orchestrator
from utils.claude_client import ClaudeClient
from database import Database
from utils.file_processor import extract_text_from_file


@pytest.fixture
def mock_client():
    """모의 Claude 클라이언트"""
    return ClaudeClient(api_key=None, mock=True)


class TestPipelinePerformance:
    """파이프라인 성능 테스트"""

    def test_full_pipeline_execution_time(self, mock_client):
        """전체 파이프라인 실행 시간"""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = Orchestrator(mock_client, tmpdir)

            start = time.time()
            context = orchestrator.run("게시판에 파일 첨부 기능을 추가해주세요")
            elapsed = time.time() - start

            # 모의 모드는 3초 이내 완료 예상
            assert elapsed < 5.0, f"Pipeline took {elapsed:.2f}s, expected < 5s"
            assert "output_file" in context

    def test_agent_selection_time(self, mock_client):
        """에이전트 선택 시간"""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = Orchestrator(mock_client, tmpdir)

            start = time.time()
            selection = orchestrator.select_agents("Test requirement")
            elapsed = time.time() - start

            # 모의 모드는 1초 이내
            assert elapsed < 1.0, f"Agent selection took {elapsed:.2f}s, expected < 1s"
            assert "selected_agents" in selection


class TestJsonParsingPerformance:
    """JSON 파싱 성능 테스트"""

    def test_parse_json_throughput(self):
        """JSON 파싱 처리량 (1000개 반복)"""
        test_json = '{"key": "value", "number": 42, "array": [1, 2, 3]}'

        start = time.time()
        for _ in range(1000):
            ClaudeClient._parse_json_safely(test_json)
        elapsed = time.time() - start

        # 1000번 파싱 < 1초
        assert elapsed < 1.0, f"1000 parse operations took {elapsed:.2f}s, expected < 1s"
        avg_ns = (elapsed * 1_000_000_000) / 1000
        print(f"Average parse time: {avg_ns:.2f}ns")

    def test_parse_fenced_json_performance(self):
        """펜스 처리 성능"""
        fenced_json = "```json\n{\"status\": \"complete\", \"data\": [1, 2, 3]}\n```"

        start = time.time()
        for _ in range(500):
            ClaudeClient._parse_json_safely(fenced_json)
        elapsed = time.time() - start

        # 500번 파싱 < 1초
        assert elapsed < 1.0, f"500 fenced parse operations took {elapsed:.2f}s"


class TestDatabasePerformance:
    """데이터베이스 성능 테스트"""

    def test_create_analysis_performance(self):
        """레코드 생성 성능"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            start = time.time()
            for i in range(100):
                db.create_analysis(
                    analysis_id=f"id_{i}",
                    job_id=f"job_{i}",
                    file_name=f"file_{i}.txt"
                )
            elapsed = time.time() - start

            # 100개 레코드 생성 < 1초
            assert elapsed < 1.0, f"100 creates took {elapsed:.2f}s, expected < 1s"

    def test_read_analysis_performance(self):
        """레코드 읽기 성능"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            # 50개 레코드 생성
            for i in range(50):
                db.create_analysis(f"id_{i}", f"job_{i}")

            # 읽기 성능 측정
            start = time.time()
            for i in range(50):
                db.get_analysis(f"id_{i}")
            elapsed = time.time() - start

            # 50개 읽기 < 0.5초
            assert elapsed < 0.5, f"50 reads took {elapsed:.2f}s"

    def test_pagination_performance(self):
        """페이지네이션 성능"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            # 1000개 레코드 생성
            for i in range(1000):
                db.create_analysis(f"id_{i}", f"job_{i}")

            # 페이지네이션 성능
            start = time.time()
            for offset in range(0, 1000, 50):
                db.get_analyses(limit=50, offset=offset)
            elapsed = time.time() - start

            # 20페이지 조회 < 1초
            assert elapsed < 1.0, f"20 page queries took {elapsed:.2f}s"

    def test_statistics_performance(self):
        """통계 계산 성능"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            # 500개 분석 데이터 생성
            for i in range(500):
                db.create_analysis(f"id_{i}", f"job_{i}")
                if i % 3 == 0:
                    db.update_analysis_success(f"id_{i}", f"output_{i}.md")
                elif i % 3 == 1:
                    db.update_analysis_error(f"id_{i}", "error")

            # 통계 계산 성능
            start = time.time()
            for _ in range(100):
                db.get_statistics()
            elapsed = time.time() - start

            # 100번 통계 계산 < 1초
            assert elapsed < 1.0, f"100 statistics calls took {elapsed:.2f}s"


class TestFileExtractionPerformance:
    """파일 추출 성능 테스트"""

    def test_text_file_extraction_speed(self):
        """텍스트 파일 추출 속도"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            # 1MB 파일 생성
            f.write("A" * (1024 * 1024))
            temp_path = f.name

        try:
            start = time.time()
            result = extract_text_from_file(temp_path, "test.txt")
            elapsed = time.time() - start

            # 1MB 파일 < 0.5초
            assert elapsed < 0.5, f"Text extraction took {elapsed:.2f}s"
            assert result.success is True
        finally:
            Path(temp_path).unlink()

    def test_small_file_processing_speed(self):
        """작은 파일 여러 개 처리"""
        temp_files = []

        try:
            # 10개 파일 생성 (각 10KB)
            for i in range(10):
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", suffix=".txt", delete=False
                ) as f:
                    f.write("X" * (10 * 1024))
                    temp_files.append(f.name)

            # 전체 처리 시간
            start = time.time()
            for file_path in temp_files:
                extract_text_from_file(file_path, Path(file_path).name)
            elapsed = time.time() - start

            # 10개 파일 처리 < 2초
            assert elapsed < 2.0, f"Processing 10 files took {elapsed:.2f}s"
        finally:
            for file_path in temp_files:
                Path(file_path).unlink()


class TestMockResponsePerformance:
    """모의 응답 생성 성능"""

    def test_mock_response_generation_speed(self):
        """모의 응답 생성 속도"""
        start = time.time()
        for i in range(100):
            ClaudeClient._mock_json_response(
                "You are planner",
                f"Analyze requirement {i}"
            )
        elapsed = time.time() - start

        # 100개 모의 응답 < 0.1초
        assert elapsed < 0.1, f"100 mock responses took {elapsed:.2f}s"

    def test_orchestrator_mock_mode_speed(self):
        """오케스트레이터 전체 모의 모드 속도"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = ClaudeClient(api_key=None, mock=True)
            orchestrator = Orchestrator(client, tmpdir)

            start = time.time()
            for i in range(10):
                orchestrator.run(f"Test requirement {i}")
            elapsed = time.time() - start

            avg_time = elapsed / 10
            # 평균 < 0.5초/실행
            assert avg_time < 0.5, f"Avg orchestrator run took {avg_time:.2f}s"


class TestMemoryEfficiency:
    """메모리 효율성 테스트"""

    def test_context_dict_memory(self):
        """context 딕셔너리 메모리 사용량"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = ClaudeClient(api_key=None, mock=True)
            orchestrator = Orchestrator(client, tmpdir)

            context = orchestrator.run("Test requirement")

            # context 크기 확인 (상식적인 범위)
            context_json = json.dumps(context, default=str)
            size_kb = len(context_json) / 1024

            # 10MB 이하 (정상 범위)
            assert size_kb < 10240, f"Context too large: {size_kb:.2f}KB"


class TestResourceUsage:
    """리소스 사용량 테스트"""

    def test_concurrent_operations_simulation(self):
        """동시 작업 시뮬레이션"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            # 10개 동시 분석 시뮬레이션
            start = time.time()
            for i in range(10):
                db.create_analysis(f"id_{i}", f"job_{i}")

            for i in range(10):
                db.update_analysis_success(f"id_{i}", f"output_{i}.md")

            elapsed = time.time() - start

            # 20개 작업 < 0.5초
            assert elapsed < 0.5, f"20 concurrent ops took {elapsed:.2f}s"

    def test_large_batch_performance(self):
        """대량 배치 처리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(str(Path(tmpdir) / "test.db"))

            start = time.time()
            # 500개 분석
            for i in range(500):
                db.create_analysis(f"id_{i}", f"job_{i}")

            # 모두 완료
            for i in range(500):
                db.update_analysis_success(f"id_{i}", f"output_{i}.md")

            elapsed = time.time() - start

            # 500개 분석 처리 < 5초
            assert elapsed < 5.0, f"500 analyses took {elapsed:.2f}s"
