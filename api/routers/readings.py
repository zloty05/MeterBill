"""Odczyty liczników. POST używany przez gateway agenta (X-API-Key)."""
from fastapi import APIRouter, Depends, status

from api.deps import get_api_key_org, get_current_org

router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reading(org_id: str = Depends(get_api_key_org)):
    """Przyjmuje odczyt z gateway. Idempotentny po (meter_id, read_at)."""
    raise NotImplementedError


@router.get("/{meter_id}")
def list_readings(meter_id: str, org_id: str = Depends(get_current_org)):
    """Historia odczytów licznika (panel zarządcy)."""
    raise NotImplementedError
