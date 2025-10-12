from fastapi import FastAPI
from .routes import jira, assets, jobs, sync, discovery
from dotenv import load_dotenv
from .middleware import add_process_time_header

# Laeb .env faili muutujad
load_dotenv()

app = FastAPI(
    title="CMDB API"
)

# Aktiveerib middleware (jookseb iga päringu puhul)
app.middleware("http")(add_process_time_header)

# Registreerime ruuterid
app.include_router(jira.router)
app.include_router(assets.router)
app.include_router(jobs.router)
app.include_router(sync.router)
app.include_router(discovery.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CMDB API"}