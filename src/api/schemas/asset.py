from pydantic import BaseModel
from typing import Optional

# See on põhiskeem, mis defineerib vara põhiomadused. Seda kasutatakse näiteks uue vara loomisel.
class AssetBase(BaseModel):
    hostname: str
    ip_address: str
    os_version: Optional[str] = None

# See skeem esindab vara sellisena, nagu see andmebaasist tuleb. See pärib kõik AssetBase'i väljad ja lisab 'id', mille annab andmebaas.
class Asset(AssetBase):
    id: int

    # See konfiguratsioon lubab Pydanticu mudelil lugeda andmeid otse teistelt objektidelt (nt andmebaasi ORM mudelitelt).
    class Config:
        from_attributes = True