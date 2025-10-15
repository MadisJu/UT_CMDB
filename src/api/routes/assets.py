from fastapi import APIRouter
from typing import List
from ..schemas import asset

# Loome ruuteri, mis grupeerib kõik varadega seotud API lõpp-punktid.
# 'prefix' lisab iga siin defineeritud URLi ette "/assets".
# 'tags' grupeerib need API dokumentatsioonis "Assets" sildi alla.
router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

# Hiljem tuleb siin ära asendada päris andmete vastu
FAKE_ASSETS_DB = [
    {"id": 1, "hostname": "server01.local", "ip_address": "192.168.1.10", "os_version": "Ubuntu 22.04"},
    {"id": 2, "hostname": "server02.local", "ip_address": "192.168.1.11", "os_version": "CentOS 9"}
]

@router.get("/", response_model=List[asset.Asset])
def get_all_assets():
    # tuleb siin ka hiljem päris andmete vastu vahetada
    return FAKE_ASSETS_DB