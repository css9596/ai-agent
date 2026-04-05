"""SQLite 데이터베이스 관리"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import settings


class Database:
    """분석 이력 관리"""

    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 분석 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    job_id TEXT UNIQUE NOT NULL,
                    file_name TEXT,
                    file_size INTEGER,
                    input_text TEXT,
                    status TEXT DEFAULT 'pending',
                    output_file TEXT,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds INTEGER,
                    chat_history TEXT
                )
            """)

            # 채팅 히스토리 컬럼 마이그레이션 (기존 테이블에 컬럼이 없으면 추가)
            try:
                cursor.execute("PRAGMA table_info(analyses)")
                columns = [col[1] for col in cursor.fetchall()]
                if "chat_history" not in columns:
                    cursor.execute("ALTER TABLE analyses ADD COLUMN chat_history TEXT")
            except sqlite3.OperationalError:
                pass

            # Phase 6: 프로젝트 관리 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    zip_file_path TEXT,
                    snapshot_path TEXT,
                    total_files INTEGER,
                    total_size INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Phase 6: 소스 비교 결과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparisons (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
                )
            """)

            # Few-shot Learning: 학습 예시 관리 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_examples (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    output_markdown TEXT NOT NULL,
                    category TEXT,
                    quality_score INTEGER DEFAULT 5,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_id
                ON analyses(job_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON analyses(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON analyses(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_id
                ON comparisons(project_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_quality
                ON training_examples(quality_score DESC, is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_category
                ON training_examples(category)
            """)

            conn.commit()

    def create_analysis(
        self,
        analysis_id: str,
        job_id: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        input_text: Optional[str] = None
    ) -> None:
        """분석 레코드 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analyses
                (id, job_id, file_name, file_size, input_text, status, started_at)
                VALUES (?, ?, ?, ?, ?, 'running', ?)
            """, (
                analysis_id,
                job_id,
                file_name,
                file_size,
                input_text[:500] if input_text else None,  # 처음 500자만 저장
                datetime.now()
            ))
            conn.commit()

    def update_analysis_success(
        self,
        analysis_id: str,
        output_file: str
    ) -> None:
        """분석 성공 기록"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("""
                UPDATE analyses
                SET status = 'completed',
                    output_file = ?,
                    completed_at = ?
                WHERE id = ?
            """, (output_file, now, analysis_id))

            # duration 계산
            cursor.execute("""
                SELECT started_at FROM analyses WHERE id = ?
            """, (analysis_id,))
            result = cursor.fetchone()
            if result and result[0]:
                started = datetime.fromisoformat(result[0])
                duration = int((now - started).total_seconds())
                cursor.execute("""
                    UPDATE analyses SET duration_seconds = ? WHERE id = ?
                """, (duration, analysis_id))

            conn.commit()

    def update_analysis_error(
        self,
        analysis_id: str,
        error_message: str
    ) -> None:
        """분석 오류 기록"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE analyses
                SET status = 'failed',
                    error_message = ?,
                    completed_at = ?
                WHERE id = ?
            """, (error_message, datetime.now(), analysis_id))
            conn.commit()

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """분석 정보 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analyses WHERE id = ?
            """, (analysis_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_analyses(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """분석 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT * FROM analyses
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM analyses
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            return [dict(row) for row in cursor.fetchall()]

    def delete_old_analyses(self, retention_days: int = settings.RETENTION_DAYS) -> int:
        """오래된 분석 결과 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 보관 기간이 지난 파일 찾기
            cursor.execute("""
                SELECT output_file FROM analyses
                WHERE created_at < datetime('now', '-' || ? || ' days')
                AND status = 'completed'
            """, (retention_days,))

            files_to_delete = [row[0] for row in cursor.fetchall()]

            # 파일 시스템에서 삭제
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    Path(file_path).unlink()
                    deleted_count += 1
                except (OSError, IOError, FileNotFoundError):
                    # 파일이 없거나 접근 불가능한 경우 무시
                    pass

            # DB에서 삭제
            cursor.execute("""
                DELETE FROM analyses
                WHERE created_at < datetime('now', '-' || ? || ' days')
                AND status = 'completed'
            """, (retention_days,))

            conn.commit()

            return deleted_count

    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 총 분석 수
            cursor.execute("SELECT COUNT(*) FROM analyses")
            total = cursor.fetchone()[0]

            # 성공한 분석
            cursor.execute("SELECT COUNT(*) FROM analyses WHERE status = 'completed'")
            completed = cursor.fetchone()[0]

            # 실패한 분석
            cursor.execute("SELECT COUNT(*) FROM analyses WHERE status = 'failed'")
            failed = cursor.fetchone()[0]

            # 진행 중인 분석
            cursor.execute("SELECT COUNT(*) FROM analyses WHERE status = 'running'")
            running = cursor.fetchone()[0]

            # 평균 분석 시간
            cursor.execute("""
                SELECT AVG(duration_seconds) FROM analyses
                WHERE status = 'completed' AND duration_seconds > 0
            """)
            avg_duration = cursor.fetchone()[0] or 0

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "success_rate": round((completed / total * 100) if total > 0 else 0, 2),
                "avg_duration_seconds": round(avg_duration, 2)
            }

    def save_chat_history(self, analysis_id: str, chat_history: List[Dict[str, str]]) -> None:
        """채팅 히스토리 저장 (JSON 직렬화)"""
        import json
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            history_json = json.dumps(chat_history, ensure_ascii=False)
            cursor.execute("""
                UPDATE analyses
                SET chat_history = ?
                WHERE id = ?
            """, (history_json, analysis_id))
            conn.commit()

    def get_chat_history(self, analysis_id: str) -> List[Dict[str, str]]:
        """채팅 히스토리 조회 (JSON 역직렬화)"""
        import json
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chat_history FROM analyses WHERE id = ?
            """, (analysis_id,))
            result = cursor.fetchone()
            if result and result[0]:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return []
            return []

    # ===================================================================
    # Phase 6: 프로젝트 관리
    # ===================================================================

    def create_project(
        self,
        project_id: str,
        name: str,
        zip_file_path: str,
        snapshot_path: str,
        total_files: int,
        total_size: int,
        description: Optional[str] = None
    ) -> None:
        """프로젝트 레코드 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects
                (id, name, description, zip_file_path, snapshot_path, total_files, total_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, name, description, zip_file_path, snapshot_path, total_files, total_size))
            conn.commit()

    def get_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """프로젝트 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects
                ORDER BY uploaded_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """프로젝트 상세 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def delete_project(self, project_id: str) -> None:
        """프로젝트 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    def create_comparison(
        self,
        comparison_id: str,
        project_id: str,
        analysis_id: str
    ) -> None:
        """비교 작업 레코드 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comparisons
                (id, project_id, analysis_id, status)
                VALUES (?, ?, ?, 'pending')
            """, (comparison_id, project_id, analysis_id))
            conn.commit()

    def update_comparison_result(
        self,
        comparison_id: str,
        status: str,
        result_path: Optional[str] = None
    ) -> None:
        """비교 결과 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if result_path:
                cursor.execute("""
                    UPDATE comparisons
                    SET status = ?, result_path = ?
                    WHERE id = ?
                """, (status, result_path, comparison_id))
            else:
                cursor.execute("""
                    UPDATE comparisons
                    SET status = ?
                    WHERE id = ?
                """, (status, comparison_id))
            conn.commit()

    def get_comparison(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        """비교 결과 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comparisons WHERE id = ?", (comparison_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    # ===================================================================
    # Few-shot Learning: 학습 예시 관리
    # ===================================================================

    def add_training_example(
        self,
        example_id: str,
        title: str,
        input_text: str,
        output_markdown: str,
        category: Optional[str] = None,
        quality_score: int = 5
    ) -> None:
        """학습 예시 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO training_examples
                (id, title, input_text, output_markdown, category, quality_score, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (example_id, title, input_text, output_markdown, category, quality_score))
            conn.commit()

    def get_training_examples(
        self,
        limit: int = 3,
        is_active: int = 1,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """품질 높은 학습 예시 조회 (활성만, 품질순)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if category:
                cursor.execute("""
                    SELECT id, title, input_text, output_markdown, category, quality_score
                    FROM training_examples
                    WHERE is_active = ? AND category = ?
                    ORDER BY quality_score DESC, created_at DESC
                    LIMIT ?
                """, (is_active, category, limit))
            else:
                cursor.execute("""
                    SELECT id, title, input_text, output_markdown, category, quality_score
                    FROM training_examples
                    WHERE is_active = ?
                    ORDER BY quality_score DESC, created_at DESC
                    LIMIT ?
                """, (is_active, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_all_training_examples(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """모든 학습 예시 조회 (관리용)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM training_examples
                ORDER BY quality_score DESC, created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def update_training_example(
        self,
        example_id: str,
        quality_score: Optional[int] = None,
        is_active: Optional[int] = None
    ) -> None:
        """학습 예시 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if quality_score is not None and is_active is not None:
                cursor.execute("""
                    UPDATE training_examples
                    SET quality_score = ?, is_active = ?
                    WHERE id = ?
                """, (quality_score, is_active, example_id))
            elif quality_score is not None:
                cursor.execute("""
                    UPDATE training_examples
                    SET quality_score = ?
                    WHERE id = ?
                """, (quality_score, example_id))
            elif is_active is not None:
                cursor.execute("""
                    UPDATE training_examples
                    SET is_active = ?
                    WHERE id = ?
                """, (is_active, example_id))

            conn.commit()

    def delete_training_example(self, example_id: str) -> None:
        """학습 예시 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM training_examples WHERE id = ?
            """, (example_id,))
            conn.commit()

    def get_training_examples_count(self) -> int:
        """등록된 학습 예시 총 개수"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM training_examples WHERE is_active = 1")
            return cursor.fetchone()[0]


# 전역 DB 인스턴스
db = Database()
