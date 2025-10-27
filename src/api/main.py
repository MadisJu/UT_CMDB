import logging
from fastapi import FastAPI
from .routes import jira, assets, jobs, sync, discovery, inventory
from dotenv import load_dotenv
from .middleware import add_process_time_header
from src.core.database import create_db_and_tables

# Laeb .env faili muutujad
load_dotenv()

app = FastAPI(
    title="CMDB API"
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    try:
        create_db_and_tables()
    except Exception as exc:
        logger.warning("Database initialisation skipped: %s", exc, exc_info=True)

# Aktiveerib middleware (jookseb iga päringu puhul)
app.middleware("http")(add_process_time_header)

# Registreerime ruuterid
app.include_router(jira.router, prefix="/api/v1/jira", tags=["Jira"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sync"])
app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["Discovery"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])

@app.get("/")
def read_root():
    return {"message": "Welcome to CMDB API"}
