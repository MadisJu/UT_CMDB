import logging
from fastapi import FastAPI
from .routes import jira, jobs, sync, discovery, inventory
from dotenv import load_dotenv
from src.core.database import create_db_and_tables
from src.api.middleware.logging_middleware import APILoggingMiddleware

# Laeb .env faili muutujad
load_dotenv()

app = FastAPI(
    title="CMDB API"
)

app.add_middleware(APILoggingMiddleware)

logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    try:
        create_db_and_tables()
    except Exception as exc:
        logger.warning("Database initialisation skipped: %s", exc, exc_info=True)

# Registreerime ruuterid
api_prefix = "/api/v1"
app.include_router(inventory.router, prefix=api_prefix)
app.include_router(discovery.router, prefix=api_prefix)
app.include_router(jira.router, prefix=api_prefix)
app.include_router(jobs.router, prefix=api_prefix)
app.include_router(sync.router, prefix=api_prefix)

@app.get("/")
def read_root():
    return {"message": "Welcome to CMDB API"}
