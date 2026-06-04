"""Dane organizacji zalogowanego zarządcy."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.deps import CurrentUser, get_current_user
from api.schemas.organizations import OrgOut, OrgUpdate
from db.supabase_client import service_client

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=OrgOut)
def get_my_org(user: CurrentUser = Depends(get_current_user)):
    """Dane organizacji zalogowanego usera (sprzedawca na fakturze)."""
    res = (
        service_client()
        .table("organizations")
        .select("*")
        .eq("id", user.org_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono organizacji",
        )
    return OrgOut(**rows[0])


@router.patch("/me", response_model=OrgOut)
def update_my_org(body: OrgUpdate, user: CurrentUser = Depends(get_current_user)):
    """Aktualizuje dane organizacji (tylko przekazane pola)."""
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Brak pól do aktualizacji",
        )
    res = (
        service_client()
        .table("organizations")
        .update(patch)
        .eq("id", user.org_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono organizacji",
        )
    return OrgOut(**rows[0])
