from fastapi import APIRouter, status
import uuid

router = APIRouter(
    prefix="/sync",
    tags=["Sync"]
)

# See käivitaks pikaajalise protsessi, mis sünkroniseerib kõik varad Jirasse.
@router.post("/to-jira", status_code=status.HTTP_202_ACCEPTED)
def sync_all_assets_to_jira():
    """
    Käivitab kõikide varade sünkroniseerimise Jira Asset Manageri.
    
    See on pikaajaline operatsioon, mis käivitatakse taustal.
    API tagastab koheselt vastuse koos töö ID-ga.
    """
    # Genereerime tööle unikaalse ID, et saaks selle staatust hiljem kontrollida.
    job_id = str(uuid.uuid4())
    
    # TULEVIKUS: Siin antaks see töö üle Celery workerile.
    # Näiteks: sync_to_jira_task.delay()
    
    # Hetkel tagastame staatilise vastuse, mis kinnitab, et töö on vastu võetud.
    return {"message": "Sync to Jira has been initiated.", "job_id": job_id}