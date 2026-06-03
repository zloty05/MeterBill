"""Budynki zarządcy."""
from fastapi import APIRouter, Depends

from api.deps import get_current_org

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("")
def list_buildings(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("")
def create_building(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.get("/{building_id}")
def get_building(building_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.patch("/{building_id}")
def update_building(building_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError
