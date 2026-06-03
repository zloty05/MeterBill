"""Dane organizacji zalogowanego zarządcy."""
from fastapi import APIRouter, Depends

from api.deps import CurrentUser, get_current_user

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me")
def get_my_org(user: CurrentUser = Depends(get_current_user)):
    raise NotImplementedError


@router.patch("/me")
def update_my_org(user: CurrentUser = Depends(get_current_user)):
    raise NotImplementedError
