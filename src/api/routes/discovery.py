from fastapi import APIRouter, status
import uuid
from pydantic import BaseModel


router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"]
)

class DiscoveryResult(BaseModel):
    assets: dict  
    job_id: str

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


@router.post("/results", status_code=status.HTTP_200_OK)
def receive_discovery_results(data: DiscoveryResult):
    """
    Saab workerilt ansible taski data kujul ({"assets": [...], "job_id": "..."}).
    """
    print(f"Received discovery results for job {data.job_id}: {data.assets}")
    
    
    return {"message": "Discovery results received successfully", "job_id": data.job_id}