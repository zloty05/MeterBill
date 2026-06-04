"""Budynki zarządcy."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.deps import get_current_org
from api.schemas.buildings import BuildingCreate, BuildingOut, BuildingUpdate
from db.supabase_client import service_client

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingOut])
def list_buildings(org_id: str = Depends(get_current_org)):
    """Lista budynków organizacji."""
    res = (
        service_client()
        .table("buildings")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at")
        .execute()
    )
    return [BuildingOut(**row) for row in (res.data or [])]


@router.post("", response_model=BuildingOut, status_code=http_status.HTTP_201_CREATED)
def create_building(body: BuildingCreate, org_id: str = Depends(get_current_org)):
    """Tworzy nowy budynek w organizacji."""
    row = {**body.model_dump(), "org_id": org_id}
    res = service_client().table("buildings").insert(row).execute()
    return BuildingOut(**(res.data or [row])[0])


@router.get("/{building_id}", response_model=BuildingOut)
def get_building(building_id: str, org_id: str = Depends(get_current_org)):
    """Szczegóły budynku."""
    res = (
        service_client()
        .table("buildings")
        .select("*")
        .eq("id", building_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono budynku",
        )
    return BuildingOut(**rows[0])


@router.patch("/{building_id}", response_model=BuildingOut)
def update_building(
    body: BuildingUpdate, building_id: str, org_id: str = Depends(get_current_org)
):
    """Aktualizuje budynek (tylko przekazane pola)."""
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Brak pól do aktualizacji",
        )
    res = (
        service_client()
        .table("buildings")
        .update(patch)
        .eq("id", building_id)
        .eq("org_id", org_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono budynku",
        )
    return BuildingOut(**rows[0])
