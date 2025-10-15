from fastapi import APIRouter
from typing import List
from ..schemas import job
import datetime

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/", response_model=List[job.Job])
def get_all_jobs():
    # Hetkel tagastab nimekirja näidistöödest. Tuleb ära asendada hiljem
    return [
        {"id": "discover-123", "status": "completed", "created_at": datetime.datetime.now()},
        {"id": "sync-456", "status": "running", "created_at": datetime.datetime.now()}
    ]