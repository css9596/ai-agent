"""구조화된 로깅 시스템"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from config import settings


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 추가 정보 추가
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """구조화된 로깅"""

    def __init__(self, name: str = "analysis"):
        self.logger = logging.getLogger(name)
        self._setup_handlers()

    def _setup_handlers(self):
        """로거 핸들러 설정"""
        # 로그 디렉토리 생성
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 파일 핸들러
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 포매터
        if settings.LOG_FORMAT == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    def info(self, message: str, **extra_data):
        """정보 로그"""
        self._log(logging.INFO, message, extra_data)

    def error(self, message: str, **extra_data):
        """에러 로그"""
        self._log(logging.ERROR, message, extra_data)

    def warning(self, message: str, **extra_data):
        """경고 로그"""
        self._log(logging.WARNING, message, extra_data)

    def debug(self, message: str, **extra_data):
        """디버그 로그"""
        self._log(logging.DEBUG, message, extra_data)

    def _log(self, level: int, message: str, extra_data: Dict[str, Any]):
        """로그 기록"""
        # LogRecord에 extra_data 추가
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.extra_data = extra_data
        self.logger.handle(record)

    def analysis_start(self, analysis_id: str, file_name: str = None):
        """분석 시작 로그"""
        self.info("분석 시작", analysis_id=analysis_id, file_name=file_name)

    def analysis_complete(self, analysis_id: str, duration_seconds: float):
        """분석 완료 로그"""
        self.info(
            "분석 완료",
            analysis_id=analysis_id,
            duration_seconds=round(duration_seconds, 2)
        )

    def analysis_error(self, analysis_id: str, error: str):
        """분석 실패 로그"""
        self.error("분석 실패", analysis_id=analysis_id, error=error)

    def file_upload(self, file_name: str, file_size: int):
        """파일 업로드 로그"""
        self.info("파일 업로드", file_name=file_name, file_size_bytes=file_size)

    def llm_request(self, model: str, tokens: int = None):
        """LLM API 요청 로그"""
        self.debug("LLM 요청", model=model, tokens=tokens)

    def llm_error(self, model: str, error: str):
        """LLM 에러 로그"""
        self.error("LLM 에러", model=model, error=error)


# 전역 로거 인스턴스
logger = StructuredLogger()
