import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.jira import JiraAsset, JiraAQLResponse

router = APIRouter(
    prefix="/jira",
    tags=["Jira Integration"]
)

# Loeb turvaliselt .env failist võetud seaded
def get_jira_config():
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_API_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_user, jira_token]):
        raise HTTPException(
            status_code=500, 
            detail="Jira seadistus .env on puudulik."
        )
    return {"url": jira_url, "user": jira_user, "token": jira_token}

@router.get("/assets", response_model=List[JiraAsset])
def get_jira_assets(
    aql_query: str = "ObjectType = Host",
    config: dict = Depends(get_jira_config)
):
    """Hangib varad Jira Asset Managerist kasutades AQL päringut."""
    api_endpoint = f"{config['url']}/rest/assets/1.0/aql/objects"

    headers = {"Accept": "application/json"}
    auth = (config['user'], config['token'])
    payload = {"aql": aql_query, "resultsPerPage": 50}

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, auth=auth)
        response.raise_for_status()
        data = JiraAQLResponse(**response.json())
        return data.entries
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Viga Jira API päringus: {e.response.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Jira API-ga ei saanud ühendust: {e}"
        )