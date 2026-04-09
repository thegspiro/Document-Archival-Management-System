"""Application configuration loaded from environment variables via Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration comes from environment variables. The application refuses
    to start if any required variable is missing."""

    # Database
    MYSQL_HOST: str = "db"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "adms"
    MYSQL_USER: str = "adms"
    MYSQL_PASSWORD: str

    # Application
    SECRET_KEY: str
    STORAGE_ROOT: str = "/data/storage"
    BASE_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LLM (all optional)
    LLM_PROVIDER: str = "none"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    # OCR
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "eng"
    OCR_WORKER_CONCURRENCY: int = 2

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()  # type: ignore[call-arg]
