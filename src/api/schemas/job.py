from pydantic import BaseModel
import datetime

# See skeem defineerib, millistest andmetest koosneb üks job.
class Job(BaseModel):
    id: str 
    status: str 
    created_at: datetime.datetime 