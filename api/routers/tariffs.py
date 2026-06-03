"""Taryfy i ich składniki."""
from fastapi import APIRouter, Depends

from api.deps import get_current_org

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get("")
def list_tariffs(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("")
def create_tariff(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("/{tariff_id}/components")
def add_component(tariff_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError
