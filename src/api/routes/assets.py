from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas import asset
from src.core.services.jira_service import JiraService
from src.core.integrations.jira_client import JiraClient

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
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

@router.get("/", response_model=List[asset.Asset])
def get_all_assets(jira_service: JiraService = Depends(get_jira_service)):
    """Get all assets from Jira Asset Manager."""
    try:
        jira_assets = jira_service.get_all_assets()
        
        assets = []
        for jira_asset in jira_assets:
            # Extract basic information from Jira asset
            hostname = jira_asset.label
            ip_address = "Unknown"
            os_version = "Unknown"
            
            # Try to extract IP and OS from attributes
            for attr in jira_asset.attributes:
                if attr.objectTypeAttributeId == "IP Address" or attr.objectTypeAttributeId == "IP":
                    if attr.objectAttributeValues:
                        ip_address = attr.objectAttributeValues[0].get("value", "Unknown")
                elif attr.objectTypeAttributeId == "Operating System" or attr.objectTypeAttributeId == "Distribution":
                    if attr.objectAttributeValues:
                        os_version = attr.objectAttributeValues[0].get("value", "Unknown")
            
            assets.append(asset.Asset(
                id=int(jira_asset.id),
                hostname=hostname,
                ip_address=ip_address,
                os_version=os_version
            ))
        
        return assets
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assets: {str(e)}"
        )