"""Pomocnicze odczyty graniczne — współdzielone przez invoice_service i invoice_delivery.

Wydzielone tu, bo i generowanie faktury, i render PDF potrzebują tych samych
„odczytów granicznych" (ostatni odczyt licznika nie później niż dana data) oraz
parsowania dat z bazy (PostgREST zwraca daty jako stringi ISO).
"""
from __future__ import annotations

from datetime import date, datetime


def parse_date(value) -> date:
    """Akceptuje date lub ISO string (z bazy wraca jako string)."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def latest_reading_at_or_before(client, meter_id: str, when: date) -> dict | None:
    """Ostatni odczyt licznika z read_at <= koniec dnia `when`. None jeśli brak.

    `when` to data (granica okresu); porównujemy do read_at (timestamptz) używając
    końca dnia, by złapać odczyt wykonany tego dnia.
    """
    upper = datetime.combine(when, datetime.max.time()).isoformat()
    res = (
        client.table("readings")
        .select("value_kwh, read_at, is_estimated, read_type")
        .eq("meter_id", meter_id)
        .lte("read_at", upper)
        .order("read_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else None
