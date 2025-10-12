from pydantic import BaseModel
from typing import List

class JiraAssetAttribute(BaseModel):
    objectTypeAttributeId: str
    objectAttributeValues: List[dict]

class JiraAsset(BaseModel):
    id: int
    objectKey: str
    label: str
    attributes: List[JiraAssetAttribute]

class JiraAQLResponse(BaseModel):
    totalFilterCount: int
    entries: List[JiraAsset]