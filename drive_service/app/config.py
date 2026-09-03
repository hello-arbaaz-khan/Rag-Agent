from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"
    google_drive_scopes: list[str] = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]
    google_api_timeout_seconds: int = 60
    google_api_prefer_ipv4: bool = True

    django_base_url: str
    database_url: str
    secret_key: str
    google_client_id: str
    google_client_secret: str
    fernet_key: str
    state_signing_secret: str
    redis_url: str = "redis://redis:6379/0"
    drive_service_base_url: str = "http://localhost:8001"
    frontend_base_url: str

settings = Settings()