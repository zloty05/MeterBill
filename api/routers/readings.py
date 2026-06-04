"""Odczyty liczników. POST używany przez gateway agenta (X-API-Key)."""
from fastapi import APIRouter, Depends, status

from api.deps import get_api_key_org, get_current_org
from api.ownership import get_meter_in_org
from api.schemas.readings import ReadingOut
from db.supabase_client import service_client

router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reading(org_id: str = Depends(get_api_key_org)):
    """Przyjmuje odczyt z gateway. Idempotentny po (meter_id, read_at).

    STUB — implementacja w kroku gateway agenta (przyjmowanie odczytów z M-Bus).
    """
    raise NotImplementedError


@router.get("/{meter_id}", response_model=list[ReadingOut])
def list_readings(meter_id: str, org_id: str = Depends(get_current_org)):
    """Historia odczytów licznika (panel zarządcy), najnowsze pierwsze."""
    client = service_client()
    get_meter_in_org(client, meter_id, org_id)
    res = (
        client.table("readings")
        .select("*")
        .eq("meter_id", meter_id)
        .order("read_at", desc=True)
        .execute()
    )
    return [ReadingOut(**row) for row in (res.data or [])]
