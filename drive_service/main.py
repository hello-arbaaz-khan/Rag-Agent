from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.Apis.routers import (
    chat,
    documents,
    drive,
    search,
)
from app.config import settings

app = FastAPI(
    title="Drive Service",
    version="1.0",
)


def _cors_origins() -> list[str]:
    origins = [
        settings.frontend_base_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *settings.cors_extra_origins,
    ]
    # De-duplicate while keeping order, and drop trailing slashes.
    return list(dict.fromkeys(o.rstrip("/") for o in origins if o))


# The React frontend normally reaches this service through the Vite dev
# proxy (same origin), but allow direct browser calls as well.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "drive_service"}

# Application API routes
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(drive.router)
app.include_router(search.router)