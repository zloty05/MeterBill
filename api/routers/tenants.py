"""Najemcy."""
from fastapi import APIRouter, Depends

from api.deps import get_current_org

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("")
def list_tenants(building_id: str | None = None, org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("")
def create_tenant(org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.patch("/{tenant_id}")
def update_tenant(tenant_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError
