from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "Aashiyana API"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://aashiyana:aashiyana@localhost:5432/aashiyana"
    cors_origins: str = "http://localhost:3000"
    firebase_project_id: str = "aashiyana"
    firebase_service_account_json: str | None = None
    dev_auth_bypass: bool = False
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    max_upload_mb: int = 8
    google_maps_server_key: str | None = None
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_smtp_user: str | None = None
    email_smtp_password: str | None = None
    email_from: str | None = None
    contact_email: str | None = None
    rate_limit_enabled: bool = True
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
