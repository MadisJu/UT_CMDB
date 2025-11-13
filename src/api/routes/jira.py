from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.jira import JiraAsset, JiraAQLResponse, JiraSchema
from src.core.services.jira_service import JiraService
from src.core.integrations.jira_client import JiraClient
from ..schemas import asset

router = APIRouter(
    prefix="/jira",
    tags=["Jira Integration"]
)

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
    """Tagastab kõik assetid Jirast"""
    try:
        raw_assets = jira_service.get_all_assets(aql_query)

        simplified_assets = []
        for raw_asset in raw_assets:
            asset_data = {
                "id": raw_asset.id,
                "name": next((attr.value for attr in raw_asset.attributes if attr.name == "Name"), None),
                "ip_address": next((attr.value for attr in raw_asset.attributes if attr.name == "IP Address"), None),


                    # siia peaks lisama ülejäänud väljad
                }
            simplified_assets.append(asset.Asset(**asset_data))
        
        return simplified_assets

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assets from Jira: {str(e)}"
        )



@router.get("/schemas", response_model=List[JiraSchema])
def get_jira_schemas(jira_service: JiraService = Depends(get_jira_service)):
    """
    Tagastab kõik schemad Jirast.
    """
    try:
        paginated_response = jira_service.get_asset_schemas()
        return paginated_response['values']
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get asset schemas from Jira: {str(e)}"
        )