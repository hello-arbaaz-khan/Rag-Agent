from app.db.session import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, func


class GoogleDriveAccount(Base):
    __tablename__ = "google_drive_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    google_email = Column(String(255), nullable=False)
    google_account_id = Column(String(255), nullable=False)

    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=False)
    token_expiry = Column(DateTime(timezone=True), nullable=False)
    scopes = Column(Text, nullable=False)

    key_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())