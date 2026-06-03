"""Liczniki (podliczniki M-Bus)."""
from fastapi import APIRouter, Depends

from api.deps import get_current_org

router = APIRouter(prefix="/meters", tags=["meters"])


@router.get("")
def list_meters(building_id: str | None = None, org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("")
def create_meter(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.get("/{meter_id}/readings")
def meter_readings(meter_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError
