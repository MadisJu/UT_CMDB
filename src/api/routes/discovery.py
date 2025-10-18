from fastapi import APIRouter, status
import uuid

router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"]
)

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def start_discovery_job():
    """
    Algatab uue varade avastamise töö.

    See on pikaajaline operatsioon, mis käivitatakse taustal.
    API tagastab koheselt vastuse koos töö ID-ga, et selle staatust saaks jälgida.
    """
    # Genereerime tööle unikaalse ID.
    job_id = str(uuid.uuid4())
    
    # TULEVIKUS: Siin antaks see töö üle Celery workerile.
    # Näiteks: run_discovery_task.delay()
    
    # Hetkel tagastame staatilise vastuse, mis kinnitab, et töö on vastu võetud.
    return {"message": "Asset discovery job has been started.", "job_id": job_id}