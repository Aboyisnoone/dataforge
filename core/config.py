from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./dataforge.db"
    
    # Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "dataforge"
    
    # AI / LLM
    GEMINI_API_KEY: Optional[str] = None
    
    # Authentication & Security
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:5180"
    AUTH_DISABLED: bool = True
    JWT_JWKS_URL: Optional[str] = None
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 1024 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
