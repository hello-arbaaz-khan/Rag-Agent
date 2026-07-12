from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DocuMind Drive Service"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    google_credentials_file: str = "credentials.json"
    google_drive_folder_id: str | None = None
    allowed_mime_types: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/msword,"
        "text/plain"
    )

    @property
    def mime_type_list(self) -> list[str]:
        return [mime.strip() for mime in self.allowed_mime_types.split(",") if mime.strip()]


settings = Settings()
