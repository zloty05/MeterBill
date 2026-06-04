"""Taryfy (szablony) i ich składniki."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.deps import get_current_org
from api.ownership import assert_tariff_in_org
from api.schemas.tariffs import (
    ComponentCreate,
    ComponentOut,
    TariffCreate,
    TariffOut,
    TariffUpdate,
)
from db.supabase_client import service_client

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


def _components(client, tariff_id: str) -> list[ComponentOut]:
    res = (
        client.table("tariff_components")
        .select("*")
        .eq("tariff_id", tariff_id)
        .order("sort_order")
        .execute()
    )
    return [ComponentOut(**c) for c in (res.data or [])]


@router.get("", response_model=list[TariffOut])
def list_tariffs(org_id: str = Depends(get_current_org)):
    """Lista taryf organizacji wraz ze składnikami."""
    client = service_client()
    res = client.table("tariff_templates").select("*").eq("org_id", org_id).execute()
    return [
        TariffOut(**row, components=_components(client, row["id"]))
        for row in (res.data or [])
    ]


@router.post("", response_model=TariffOut, status_code=http_status.HTTP_201_CREATED)
def create_tariff(body: TariffCreate, org_id: str = Depends(get_current_org)):
    """Tworzy taryfę (bez składników — dodawane przez POST /{id}/components)."""
    row = {**body.model_dump(mode="json"), "org_id": org_id}
    res = service_client().table("tariff_templates").insert(row).execute()
    return TariffOut(**(res.data or [row])[0])


@router.get("/{tariff_id}", response_model=TariffOut)
def get_tariff(tariff_id: str, org_id: str = Depends(get_current_org)):
    """Szczegóły taryfy ze składnikami."""
    client = service_client()
    res = (
        client.table("tariff_templates")
        .select("*")
        .eq("id", tariff_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono taryfy"
        )
    return TariffOut(**rows[0], components=_components(client, tariff_id))


@router.patch("/{tariff_id}", response_model=TariffOut)
def update_tariff(
    body: TariffUpdate, tariff_id: str, org_id: str = Depends(get_current_org)
):
    """Aktualizuje taryfę (tylko przekazane pola)."""
    patch = body.model_dump(exclude_unset=True, mode="json")
    if not patch:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Brak pól do aktualizacji",
        )
    client = service_client()
    res = (
        client.table("tariff_templates")
        .update(patch)
        .eq("id", tariff_id)
        .eq("org_id", org_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono taryfy"
        )
    return TariffOut(**rows[0], components=_components(client, tariff_id))


@router.post(
    "/{tariff_id}/components",
    response_model=ComponentOut,
    status_code=http_status.HTTP_201_CREATED,
)
def add_component(
    body: ComponentCreate, tariff_id: str, org_id: str = Depends(get_current_org)
):
    """Dodaje składnik do taryfy należącej do organizacji."""
    client = service_client()
    assert_tariff_in_org(client, tariff_id, org_id)
    row = {**body.model_dump(mode="json"), "tariff_id": tariff_id}
    res = client.table("tariff_components").insert(row).execute()
    return ComponentOut(**(res.data or [row])[0])
