from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "WithBot"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "withbot-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////tmp/withbot.db"

    # Google OAuth (strip으로 환경변수 끝 공백/줄바꿈 제거)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    @property
    def google_client_id(self) -> str:
        return self.GOOGLE_CLIENT_ID.strip()

    @property
    def google_client_secret(self) -> str:
        return self.GOOGLE_CLIENT_SECRET.strip()

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB

    # AI 포스팅 제한
    DEFAULT_MAX_POSTS_PER_DAY: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# uploads 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
