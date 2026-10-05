from fastapi import FastAPI

from app.Apis.routers import (
    chat,
    documents,
    drive,
    search,
)

app = FastAPI(
    title="Drive Service",
    version="1.0",
)


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "drive_service"}

# Application API routes
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(drive.router)
app.include_router(search.router)
