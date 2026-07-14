from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"
    google_drive_scopes: list[str] = ["https://www.googleapis.com/auth/drive.readonly"]

    django_base_url: str = "http://[localhost:8000]"
    
    class config:
        env_file = ".env"

settings = Settings()