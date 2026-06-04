"""Seeduje komplet danych demonstracyjnych do Supabase (1 faktura end-to-end).

Wstawia organizację, budynek, najemcę, taryfę G11 – ZAEL 2026 (8 składników), licznik,
przypisanie i 2 odczyty graniczne (1000 → 1177 kWh w kwietniu 2026 = 177 kWh). Na tym
komplecie `generate_invoices_for_building` wygeneruje fakturę FV/001/04/2026 (brutto 211,77 zł).

Idempotentny: organizację rozpoznaje po nazwie (DEMO_ORG_NAME). Jeśli już istnieje, nie
duplikuje niczego — zwraca istniejące org_id/building_id. Dzięki temu można uruchamiać
wielokrotnie (np. po `docker compose run`) bez śmiecenia bazy.

Działa na SERVICE_KEY (omija RLS). Po wstawieniu wypisuje org_id i building_id — przydają się
skryptowi generate_demo_invoice.py.

Użycie (host lub kontener):
  python scripts/seed_demo_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.supabase_client import service_client

DEMO_ORG_NAME = "Demo Zarządca Sp. z o.o."
DEMO_TENANT_EMAIL = "zloty05@gmail.com"  # zweryfikowany w Resend → /send zadziała

# Taryfa G11 – ZAEL 2026, identyczna jak w tests/test_invoice_service.py::ZAEL_COMPONENTS.
ZAEL_COMPONENTS = [
    {"name": "Opłata obrotowa (energia)", "component_type": "per_kwh", "unit_price": "0.51760", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 1},
    {"name": "Opłata zmienna sieciowa", "component_type": "per_kwh", "unit_price": "0.25660", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 2},
    {"name": "Opłata jakościowa", "component_type": "per_kwh", "unit_price": "0.03320", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 3},
    {"name": "Opłata OZE", "component_type": "per_kwh", "unit_price": "0.00730", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 4},
    {"name": "Opłata kogeneracyjna", "component_type": "per_kwh", "unit_price": "0.00300", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 5},
    {"name": "Opłata mocowa", "component_type": "monthly_fixed", "unit_price": "17.18", "unit": "zł/mc", "vat_rate": "23", "sort_order": 6},
    {"name": "Abonament", "component_type": "monthly_fixed", "unit_price": "5.00", "unit": "zł/mc", "vat_rate": "23", "sort_order": 7},
    {"name": "Opłata stała sieciowa", "component_type": "monthly_fixed", "unit_price": "5.25", "unit": "zł/mc", "vat_rate": "23", "sort_order": 8},
]


def _insert_one(client, table: str, row: dict) -> dict:
    """Wstawia jeden wiersz i zwraca go (z nadanym przez bazę id)."""
    res = client.table(table).insert(row).execute()
    return (res.data or [row])[0]


def seed(client) -> tuple[str, str]:
    """Wstawia komplet danych (idempotentnie). Zwraca (org_id, building_id)."""
    # Idempotencja: jeśli organizacja demo już jest, nic nie wstawiamy.
    existing = (
        client.table("organizations")
        .select("id")
        .eq("name", DEMO_ORG_NAME)
        .limit(1)
        .execute()
    ).data or []
    if existing:
        org_id = existing[0]["id"]
        bld = (
            client.table("buildings")
            .select("id")
            .eq("org_id", org_id)
            .limit(1)
            .execute()
        ).data or [{}]
        print(f"Dane demo już istnieją (org_id={org_id}) — pomijam seed.")
        return org_id, bld[0].get("id")

    org = _insert_one(client, "organizations", {
        "name": DEMO_ORG_NAME,
        "nip": "1234567890",
        "address": "ul. Rynek 12, 00-001 Miasto",
        "bank_account": "PL00 1234 5678 9012 3456 7890 1234",
    })
    org_id = org["id"]

    building = _insert_one(client, "buildings", {
        "org_id": org_id,
        "name": "Budynek demonstracyjny",
        "address": "ul. Przykładowa 10, 00-001 Miasto",
    })
    building_id = building["id"]

    tenant = _insert_one(client, "tenants", {
        "building_id": building_id,
        "name": "Najemca U1",
        "email": DEMO_TENANT_EMAIL,
        "unit_no": "U1",
        "active": True,
    })

    tariff = _insert_one(client, "tariff_templates", {
        "org_id": org_id,
        "name": "G11 – ZAEL 2026",
        "tariff_group": "G11",
        "margin_pct": "0",
        "vat_rate": "23",
        "source_doc": "Faktura ZAEL 04/2026 (demo)",
        "valid_from": "2026-01-01",
    })
    tariff_id = tariff["id"]

    client.table("tariff_components").insert(
        [{**c, "tariff_id": tariff_id} for c in ZAEL_COMPONENTS]
    ).execute()

    meter = _insert_one(client, "meters", {
        "building_id": building_id,
        "tariff_id": tariff_id,
        "serial_no": "MB-0001",
        "label": "Lokal U1 – parter",
    })
    meter_id = meter["id"]

    client.table("meter_assignments").insert({
        "tenant_id": tenant["id"],
        "meter_id": meter_id,
        "valid_from": "2026-01-01",
        "valid_to": None,
    }).execute()

    client.table("readings").insert([
        {"meter_id": meter_id, "read_at": "2026-04-01T00:00:00+00:00",
         "value_kwh": "1000.000", "read_type": "remote", "is_estimated": False, "source": "demo"},
        {"meter_id": meter_id, "read_at": "2026-04-30T23:00:00+00:00",
         "value_kwh": "1177.000", "read_type": "remote", "is_estimated": False, "source": "demo"},
    ]).execute()

    print(f"Zaseedowano dane demo: org_id={org_id}, building_id={building_id}")
    print(f"  Najemca: Najemca U1 <{DEMO_TENANT_EMAIL}>, licznik MB-0001, taryfa G11 – ZAEL 2026")
    print(f"  Odczyty: 1000 → 1177 kWh (kwiecień 2026 = 177 kWh)")
    return org_id, building_id


def main() -> int:
    seed(service_client())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
