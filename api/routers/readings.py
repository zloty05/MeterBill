"""Odczyty liczników. POST używany przez gateway (PLC) przez X-API-Key."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status

from api.deps import get_api_key_org, get_current_org
from api.ownership import get_meter_in_org
from api.schemas.readings import ReadingCreate, ReadingOut
from db.supabase_client import service_client

router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", response_model=ReadingOut, status_code=status.HTTP_201_CREATED)
def create_reading(
    body: ReadingCreate,
    response: Response,
    org_id: str = Depends(get_api_key_org),
):
    """Przyjmuje odczyt z gateway (PLC). Idempotentny po (meter_id, read_at).

    - Autoryzacja: X-API-Key → org_id (gateway).
    - Izolacja: licznik musi należeć do organizacji klucza (przez building → org).
    - read_at: gdy gateway go nie poda, czas nadaje serwer (now UTC).
    - Idempotencja: retry tego samego (meter_id, read_at) zwraca istniejący
      odczyt z 200 (nie tworzy duplikatu) — zgodnie z UNIQUE(meter_id, read_at).
    """
    client = service_client()
    meter_id = str(body.meter_id)
    get_meter_in_org(client, meter_id, org_id)  # 404, jeśli spoza org / nie istnieje

    read_at = (body.read_at or datetime.now(timezone.utc)).isoformat()

    existing = (
        client.table("readings")
        .select("*")
        .eq("meter_id", meter_id)
        .eq("read_at", read_at)
        .limit(1)
        .execute()
    ).data or []
    if existing:
        response.status_code = status.HTTP_200_OK
        return ReadingOut(**existing[0])

    row = {
        "meter_id": meter_id,
        "read_at": read_at,
        "read_type": body.read_type,
        "value_kwh": str(body.value_kwh),
        "power_kw": None if body.power_kw is None else str(body.power_kw),
        "is_estimated": body.is_estimated,
        "source": body.source or "plc",
    }
    res = client.table("readings").insert(row).execute()
    return ReadingOut(**(res.data or [row])[0])


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
