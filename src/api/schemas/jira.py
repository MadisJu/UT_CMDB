from pydantic import BaseModel
from typing import List

class JiraAssetAttribute(BaseModel):
    objectTypeAttributeId: str
    objectAttributeValues: List[dict]

class JiraAsset(BaseModel):
    id: str
    objectKey: str
    label: str
    attributes: List[JiraAssetAttribute]

class JiraAQLResponse(BaseModel):
    objectEntries: List[JiraAsset]