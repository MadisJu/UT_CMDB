import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.jira import JiraAsset, JiraAQLResponse

router = APIRouter(
    prefix="/jira",
    tags=["Jira Integration"]
)

# Loeb .env failist võetud seaded
def get_jira_config():
    config_vars = {
        "url": os.getenv("JIRA_URL"),
        "user": os.getenv("JIRA_API_USER"),
        "token": os.getenv("JIRA_API_TOKEN"),
        "workspaceId": os.getenv("JIRA_WORKSPACE_ID"),
        "cloudId": os.getenv("JIRA_CLOUD_ID")
    }
    if not all(config_vars.values()):
        raise HTTPException(
            status_code=500,
            detail="Jira seadistus .env on puudulik. Kontrolli kõiki 5 JIRA muutujat."
        )
    return config_vars

@router.get("/assets", response_model=List[JiraAsset])
def get_jira_assets(
    aql_query: str = "ObjectType = \"Servers\"",
    config: dict = Depends(get_jira_config)
):
    """Hangib varad Jira Asset Managerist kasutades AQL päringut."""

    api_endpoint = f"https://api.atlassian.com/ex/jira/{config['cloudId']}/jsm/assets/workspace/{config['workspaceId']}/v1/aql/objects"

    headers = {"Accept": "application/json"}
    auth = (config['user'], config['token'])
    params = {"qlQuery": aql_query, "resultsPerPage": 50}

    try:
        response = requests.get(api_endpoint, headers=headers, params=params, auth=auth)
        response.raise_for_status()

        data = JiraAQLResponse(**response.json())
        return data.objectEntries

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Viga Jira API päringus: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tekkis ootamatu viga andmete valideerimisel: {e}"
        )


#Test for seeing all the schemas
@router.get("/test-schemas", tags=["Jira Integration (Debug)"])
def get_jira_schemas(config: dict = Depends(get_jira_config)):
    """
    [TESTIMISEKS] Proovib kätte saada kõik Asset skeemid uue API kaudu.
    """

    api_endpoint = f"https://api.atlassian.com/ex/jira/{config['cloudId']}/jsm/assets/workspace/{config['workspaceId']}/v1/objectschema/list"
    headers = {"Accept": "application/json"}
    auth = (config['user'], config['token'])

    try:
        response = requests.get(api_endpoint, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()
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