from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"
    google_drive_scopes: list[str] = ["https://www.googleapis.com/auth/drive.readonly"]
    google_api_timeout_seconds: int = 60
    google_api_prefer_ipv4: bool = True

    django_base_url: str = "http://[localhost:8000]"
    

settings = Settings()