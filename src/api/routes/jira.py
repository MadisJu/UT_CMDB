from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.jira import JiraAsset, JiraAQLResponse
from src.core.services.jira_service import JiraService
from src.core.integrations.jira_client import JiraClient

router = APIRouter(
    prefix="/jira",
    tags=["Jira Integration"]
)

# Dependency to get Jira service
def get_jira_service():
    try:
        jira_client = JiraClient()
        return JiraService(jira_client)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Jira configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Jira service: {str(e)}"
        )

@router.get("/assets", response_model=List[JiraAsset])
def get_jira_assets(
    aql_query: str = "ObjectType = \"Servers\"",
    jira_service: JiraService = Depends(get_jira_service)
):
    """Get assets from Jira Asset Manager using AQL query."""
    try:
        return jira_service.get_all_assets(aql_query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assets from Jira: {str(e)}"
        )


@router.get("/schemas", tags=["Jira Integration (Debug)"])
def get_jira_schemas(jira_service: JiraService = Depends(get_jira_service)):
    """
    Get all asset schemas from Jira.
    """
    try:
        return jira_service.get_asset_schemas()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get asset schemas from Jira: {str(e)}"
        )