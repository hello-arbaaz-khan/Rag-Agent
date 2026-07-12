from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"success": True, "status": "ok", "service": "drive_service"}
