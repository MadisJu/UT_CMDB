from pydantic import BaseModel
from typing import List, Optional

class JiraAssetAttribute(BaseModel):
    objectTypeAttributeId: str
    objectAttributeValues: List[dict]

class JiraAsset(BaseModel):
    id: str
    objectKey: str
    label: str
    attributes: Optional[List[JiraAssetAttribute]] = None

class JiraAQLResponse(BaseModel):
    objectEntries: List[JiraAsset]

class JiraSchema(BaseModel):
    id: str
    name: str
    objectCount: int
    objectSchemaKey: str