"""시스템 설정 관리"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 서버
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    MOCK_MODE: bool = False

    # LLM
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "llama3.3:70b"
    LLM_API_KEY: str = "ollama"
    ANTHROPIC_API_KEY: str = ""  # .env에서 로드 (사용하지 않음)

    # 파일 처리
    MAX_FILE_SIZE_MB: int = 50  # 최대 파일 크기 (MB)
    MAX_DOCUMENT_TOKENS: int = 100000  # 최대 문서 토큰 수
    TEMP_UPLOAD_DIR: str = "temp_uploads"  # 임시 업로드 디렉토리

    # 분석 관리
    MAX_CONCURRENT_ANALYSES: int = 3  # 동시 분석 최대 개수
    ANALYSIS_TIMEOUT_MINUTES: int = 30  # 분석 타임아웃 (분)
    RETENTION_DAYS: int = 30  # 분석 결과 보관 기간 (일)

    # 데이터베이스
    DATABASE_PATH: str = "analysis_history.db"

    # 로깅
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/analysis.log"
    LOG_FORMAT: str = "json"  # json or text

    # 출력
    OUTPUT_DIR: str = "output"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 객체
settings = Settings()
