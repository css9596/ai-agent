"""데이터베이스 단위 테스트"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from database import Database


@pytest.fixture
def temp_db():
    """임시 데이터베이스"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db


class TestDatabaseInit:
    """데이터베이스 초기화 테스트"""

    def test_init_creates_db_file(self, temp_db):
        """DB 파일 생성"""
        assert Path(temp_db.db_path).exists()

    def test_init_creates_table(self, temp_db):
        """분석 테이블 생성"""
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='analyses'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_init_creates_indexes(self, temp_db):
        """인덱스 생성"""
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_job_id'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_init_idempotent(self, temp_db):
        """init 메서드 반복 호출 안전"""
        # 두 번 호출해도 오류 없음
        temp_db.init_db()
        temp_db.init_db()


class TestCreateAnalysis:
    """분석 레코드 생성 테스트"""

    def test_create_analysis_stores_record(self, temp_db):
        """레코드 저장"""
        temp_db.create_analysis(
            analysis_id="test_1",
            job_id="job_1",
            file_name="test.txt",
            file_size=1024
        )

        record = temp_db.get_analysis("test_1")
        assert record is not None
        assert record["job_id"] == "job_1"

    def test_create_analysis_truncates_input_text(self, temp_db):
        """input_text 500자 자르기"""
        long_text = "A" * 600
        temp_db.create_analysis(
            analysis_id="test_2",
            job_id="job_2",
            input_text=long_text
        )

        record = temp_db.get_analysis("test_2")
        assert len(record["input_text"]) == 500

    def test_create_analysis_sets_running_status(self, temp_db):
        """상태를 'running'으로 설정"""
        temp_db.create_analysis(
            analysis_id="test_3",
            job_id="job_3"
        )

        record = temp_db.get_analysis("test_3")
        assert record["status"] == "running"

    def test_create_analysis_duplicate_id_error(self, temp_db):
        """중복 analysis_id는 IntegrityError"""
        temp_db.create_analysis("dup_1", "job_1")

        with pytest.raises(sqlite3.IntegrityError):
            temp_db.create_analysis("dup_1", "job_2")

    def test_create_analysis_duplicate_job_id_error(self, temp_db):
        """중복 job_id는 IntegrityError"""
        temp_db.create_analysis("id_1", "dup_job")

        with pytest.raises(sqlite3.IntegrityError):
            temp_db.create_analysis("id_2", "dup_job")


class TestUpdateAnalysisSuccess:
    """분석 성공 업데이트 테스트"""

    def test_update_analysis_success_sets_completed(self, temp_db):
        """상태를 'completed'로 설정"""
        temp_db.create_analysis("id_1", "job_1")
        temp_db.update_analysis_success("id_1", "output.md")

        record = temp_db.get_analysis("id_1")
        assert record["status"] == "completed"
        assert record["output_file"] == "output.md"

    def test_update_analysis_success_calculates_duration(self, temp_db):
        """소요 시간 계산"""
        temp_db.create_analysis("id_2", "job_2")
        temp_db.update_analysis_success("id_2", "output.md")

        record = temp_db.get_analysis("id_2")
        assert record["duration_seconds"] is not None
        assert record["duration_seconds"] >= 0

    def test_update_analysis_success_with_null_started_at(self, temp_db):
        """started_at이 NULL일 때 크래시 없음"""
        # 직접 NULL로 레코드 생성
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO analyses (id, job_id, status, started_at) "
                "VALUES (?, ?, ?, ?)",
                ("id_3", "job_3", "running", None)
            )
            conn.commit()

        # update 호출해도 오류 없음
        temp_db.update_analysis_success("id_3", "output.md")

        record = temp_db.get_analysis("id_3")
        assert record["status"] == "completed"

    def test_update_nonexistent_analysis(self, temp_db):
        """존재하지 않는 레코드 업데이트는 무시"""
        # 오류 없이 조용히 무시
        temp_db.update_analysis_success("nonexistent", "output.md")


class TestUpdateAnalysisError:
    """분석 오류 업데이트 테스트"""

    def test_update_analysis_error_sets_failed(self, temp_db):
        """상태를 'failed'로 설정"""
        temp_db.create_analysis("id_4", "job_4")
        error_msg = "API timeout"
        temp_db.update_analysis_error("id_4", error_msg)

        record = temp_db.get_analysis("id_4")
        assert record["status"] == "failed"
        assert record["error_message"] == error_msg

    def test_update_analysis_error_nonexistent(self, temp_db):
        """존재하지 않는 레코드는 무시"""
        temp_db.update_analysis_error("nonexistent", "error")


class TestGetAnalysis:
    """분석 조회 테스트"""

    def test_get_analysis_exists(self, temp_db):
        """존재하는 레코드"""
        temp_db.create_analysis("id_5", "job_5", file_name="test.txt")

        record = temp_db.get_analysis("id_5")
        assert record is not None
        assert record["file_name"] == "test.txt"

    def test_get_analysis_not_exists(self, temp_db):
        """존재하지 않는 레코드"""
        result = temp_db.get_analysis("nonexistent")
        assert result is None


class TestGetAnalyses:
    """분석 목록 조회 테스트"""

    def test_get_analyses_empty(self, temp_db):
        """빈 DB"""
        result = temp_db.get_analyses()
        assert result == []

    def test_get_analyses_pagination(self, temp_db):
        """페이지네이션"""
        # 5개 레코드 생성
        for i in range(5):
            temp_db.create_analysis(f"id_{i}", f"job_{i}")

        # 첫 2개
        page1 = temp_db.get_analyses(limit=2, offset=0)
        assert len(page1) == 2

        # 다음 2개
        page2 = temp_db.get_analyses(limit=2, offset=2)
        assert len(page2) == 2

        # 마지막 1개
        page3 = temp_db.get_analyses(limit=2, offset=4)
        assert len(page3) == 1

    def test_get_analyses_status_filter(self, temp_db):
        """상태 필터"""
        temp_db.create_analysis("id_a", "job_a")
        temp_db.create_analysis("id_b", "job_b")
        temp_db.update_analysis_success("id_a", "output.md")

        # completed 필터
        completed = temp_db.get_analyses(status="completed")
        assert len(completed) == 1
        assert completed[0]["id"] == "id_a"

        # running 필터
        running = temp_db.get_analyses(status="running")
        assert len(running) == 1
        assert running[0]["id"] == "id_b"

    def test_get_analyses_order(self, temp_db):
        """최근 순서 정렬"""
        import time
        temp_db.create_analysis("id_1", "job_1")
        time.sleep(0.1)
        temp_db.create_analysis("id_2", "job_2")

        analyses = temp_db.get_analyses()
        # id_2가 가장 최근이므로 먼저 나옴
        assert analyses[0]["id"] == "id_2"
        assert analyses[1]["id"] == "id_1"


class TestDeleteOldAnalyses:
    """오래된 분석 삭제 테스트"""

    def test_delete_old_analyses_only_completed(self, temp_db):
        """'completed' 상태만 삭제"""
        # running 레코드
        temp_db.create_analysis("id_r", "job_r")

        # completed 레코드
        temp_db.create_analysis("id_c", "job_c", file_name="output.md")
        temp_db.update_analysis_success("id_c", "output.md")

        # 0일 이상 오래된 것만 (즉, 모든 completed)
        deleted = temp_db.delete_old_analyses(retention_days=0)

        # running은 남음
        running = temp_db.get_analysis("id_r")
        assert running is not None

    def test_delete_old_analyses_nonexistent_file(self, temp_db):
        """파일 없어도 DB 삭제"""
        temp_db.create_analysis("id_d", "job_d", file_name="missing.md")
        temp_db.update_analysis_success("id_d", "missing.md")

        # 존재하지 않는 파일도 무시하고 계속
        deleted = temp_db.delete_old_analyses(retention_days=0)
        # 파일 삭제 실패해도 DB에서는 삭제됨


class TestGetStatistics:
    """통계 조회 테스트"""

    def test_get_statistics_empty_db(self, temp_db):
        """빈 DB"""
        stats = temp_db.get_statistics()
        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["running"] == 0
        assert stats["success_rate"] == 0

    def test_get_statistics_with_data(self, temp_db):
        """데이터 있을 때"""
        # 3개 완료, 1개 실패, 2개 진행중
        for i in range(3):
            temp_db.create_analysis(f"id_c{i}", f"job_c{i}")
            temp_db.update_analysis_success(f"id_c{i}", f"output{i}.md")

        for i in range(1):
            temp_db.create_analysis(f"id_f{i}", f"job_f{i}")
            temp_db.update_analysis_error(f"id_f{i}", "error")

        for i in range(2):
            temp_db.create_analysis(f"id_r{i}", f"job_r{i}")

        stats = temp_db.get_statistics()
        assert stats["total"] == 6
        assert stats["completed"] == 3
        assert stats["failed"] == 1
        assert stats["running"] == 2
        assert stats["success_rate"] == 50.0  # 3/6 * 100

    def test_get_statistics_zero_division(self, temp_db):
        """0으로 나누기 방지"""
        stats = temp_db.get_statistics()
        assert stats["success_rate"] == 0
        assert stats["avg_duration_seconds"] == 0


class TestDatabaseEdgeCases:
    """엣지 케이스 테스트"""

    def test_create_with_none_values(self, temp_db):
        """None 값으로 생성"""
        temp_db.create_analysis("id_none", "job_none", file_name=None, file_size=None)
        record = temp_db.get_analysis("id_none")
        assert record["file_name"] is None
        assert record["file_size"] is None

    def test_create_with_empty_strings(self, temp_db):
        """빈 문자열"""
        temp_db.create_analysis("id_empty", "job_empty", file_name="", input_text="")
        record = temp_db.get_analysis("id_empty")
        assert record["file_name"] == ""
        assert record["input_text"] is None or record["input_text"] == ""
