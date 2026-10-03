from fastapi import FastAPI

from app.Apis.routers import (
    chat,
    documents,
    drive,
    search,
)
from app.schemas.oauth import router as oauth_router


app = FastAPI(
    title="Drive Service",
    version="1.0",
)


# Google Drive OAuth routes
app.include_router(oauth_router)


# Application API routes
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(drive.router)
app.include_router(search.router)