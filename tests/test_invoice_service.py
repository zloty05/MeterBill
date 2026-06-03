"""Testy orkiestracji generowania faktur (core/invoice_service) na fake kliencie."""
from datetime import date
from decimal import Decimal

import pytest

from core.invoice_service import generate_invoices_for_building
from tests.fake_supabase import FakeSupabase

ORG = "org-1"
BUILDING = "bld-1"
TARIFF = "tar-1"
METER = "mtr-u1"
TENANT = "ten-u1"

# Składniki taryfy G11 ZAEL 2026 (jak w test_billing_engine).
ZAEL_COMPONENTS = [
    {"id": "c1", "tariff_id": TARIFF, "name": "Opłata obrotowa (energia)", "component_type": "per_kwh", "unit_price": "0.51760", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 1},
    {"id": "c2", "tariff_id": TARIFF, "name": "Opłata zmienna sieciowa", "component_type": "per_kwh", "unit_price": "0.25660", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 2},
    {"id": "c3", "tariff_id": TARIFF, "name": "Opłata jakościowa", "component_type": "per_kwh", "unit_price": "0.03320", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 3},
    {"id": "c4", "tariff_id": TARIFF, "name": "Opłata OZE", "component_type": "per_kwh", "unit_price": "0.00730", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 4},
    {"id": "c5", "tariff_id": TARIFF, "name": "Opłata kogeneracyjna", "component_type": "per_kwh", "unit_price": "0.00300", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 5},
    {"id": "c6", "tariff_id": TARIFF, "name": "Opłata mocowa", "component_type": "monthly_fixed", "unit_price": "17.18", "unit": "zł/mc", "vat_rate": "23", "sort_order": 6},
    {"id": "c7", "tariff_id": TARIFF, "name": "Abonament", "component_type": "monthly_fixed", "unit_price": "5.00", "unit": "zł/mc", "vat_rate": "23", "sort_order": 7},
    {"id": "c8", "tariff_id": TARIFF, "name": "Opłata stała sieciowa", "component_type": "monthly_fixed", "unit_price": "5.25", "unit": "zł/mc", "vat_rate": "23", "sort_order": 8},
]


def base_db(**overrides):
    """Baza z 1 budynkiem, 1 najemcą, 1 licznikiem, taryfą ZAEL i 2 odczytami
    (start 1000, end 1177 → 177 kWh w kwietniu)."""
    data = {
        "buildings": [{"id": BUILDING, "org_id": ORG}],
        "tenants": [{"id": TENANT, "name": "Najemca U1", "building_id": BUILDING, "active": True}],
        "meters": [{"id": METER, "building_id": BUILDING, "tariff_id": TARIFF}],
        "meter_assignments": [
            {"id": "a1", "tenant_id": TENANT, "meter_id": METER, "valid_from": "2026-01-01", "valid_to": None}
        ],
        "tariff_templates": [
            {"id": TARIFF, "org_id": ORG, "name": "G11 – ZAEL 2026", "margin_pct": "0", "vat_rate": "23"}
        ],
        "tariff_components": list(ZAEL_COMPONENTS),
        "readings": [
            {"id": "r1", "meter_id": METER, "read_at": "2026-04-01T00:00:00", "value_kwh": "1000.000", "is_estimated": False},
            {"id": "r2", "meter_id": METER, "read_at": "2026-04-30T23:00:00", "value_kwh": "1177.000", "is_estimated": False},
        ],
        "invoices": [],
        "invoice_lines": [],
    }
    data.update(overrides)
    return data


def run(db):
    return generate_invoices_for_building(
        FakeSupabase(db), ORG, BUILDING, date(2026, 4, 1), date(2026, 4, 30)
    )


# ---------------------------------------------------------------------------
# Happy path — scenariusz ZAEL end-to-end
# ---------------------------------------------------------------------------
def test_happy_path_zael_totals():
    result = run(base_db())

    assert len(result.generated) == 1
    assert result.skipped == []

    inv = result.generated[0].invoice
    assert inv["kwh_consumed"] == "177.000"
    assert inv["net_amount"] == "172.17"
    assert inv["vat_amount"] == "39.60"
    assert inv["gross_amount"] == "211.77"
    assert inv["status"] == "draft"
    assert inv["is_estimated"] is False
    assert inv["invoice_no"] == "FV/001/04/2026"
    assert inv["due_date"] == "2026-05-14"  # period_to + 14 dni


def test_happy_path_lines_saved():
    result = run(base_db())
    lines = result.generated[0].lines
    assert len(lines) == 8
    assert all(l["invoice_id"] == result.generated[0].invoice["id"] for l in lines)


# ---------------------------------------------------------------------------
# Skipped — brak odczytów
# ---------------------------------------------------------------------------
def test_single_reading_before_period_gives_zero_kwh():
    # Tylko jeden odczyt, sprzed okresu. Start i end wskażą ten sam odczyt
    # (oba <= odpowiedniej granicy) → zużycie 0 kWh, faktura z samymi opłatami stałymi.
    db = base_db(readings=[
        {"id": "r1", "meter_id": METER, "read_at": "2026-03-15T00:00:00", "value_kwh": "1000.000", "is_estimated": False},
    ])
    result = run(db)
    assert len(result.generated) == 1
    assert result.generated[0].invoice["kwh_consumed"] == "0.000"
    # netto = same opłaty stałe 27.43
    assert result.generated[0].invoice["net_amount"] == "27.43"


def test_skip_when_no_reading_at_all():
    db = base_db(readings=[])
    result = run(db)
    assert result.generated == []
    assert len(result.skipped) == 1
    assert "odczytu" in result.skipped[0].reason.lower()


def test_skip_when_no_assignment():
    db = base_db(meter_assignments=[])
    result = run(db)
    assert result.generated == []
    assert len(result.skipped) == 1
    assert "licznik" in result.skipped[0].reason.lower()


def test_skip_when_no_components():
    db = base_db(tariff_components=[])
    result = run(db)
    assert result.generated == []
    assert len(result.skipped) == 1
    assert "skład" in result.skipped[0].reason.lower()


# ---------------------------------------------------------------------------
# Duplikat
# ---------------------------------------------------------------------------
def test_skip_when_duplicate_invoice_exists():
    db = base_db(invoices=[
        {"id": "existing", "tenant_id": TENANT, "org_id": ORG,
         "period_from": "2026-04-01", "period_to": "2026-04-30"}
    ])
    result = run(db)
    assert result.generated == []
    assert len(result.skipped) == 1
    assert "już" in result.skipped[0].reason.lower()


# ---------------------------------------------------------------------------
# Niepełny miesiąc — proporcja dni dla opłat stałych
# ---------------------------------------------------------------------------
def test_partial_month_prorates_fixed_fees():
    # Najemca wszedł 16.04 → przypisanie od 2026-04-16, okres 16..30 = 15 dni z 30.
    db = base_db(meter_assignments=[
        {"id": "a1", "tenant_id": TENANT, "meter_id": METER, "valid_from": "2026-04-16", "valid_to": None}
    ])
    result = run(db)
    assert len(result.generated) == 1
    lines = {l["label"]: l for l in result.generated[0].lines}
    # Opłata mocowa 17.18 * 15/30 = 8.59
    assert lines["Opłata mocowa"]["net_amount"] == "8.59"
    # per_kwh bez zmian
    assert lines["Opłata obrotowa (energia)"]["net_amount"] == "91.62"


# ---------------------------------------------------------------------------
# Odczyt szacowany → flaga na fakturze
# ---------------------------------------------------------------------------
def test_estimated_reading_marks_invoice():
    db = base_db(readings=[
        {"id": "r1", "meter_id": METER, "read_at": "2026-04-01T00:00:00", "value_kwh": "1000.000", "is_estimated": False},
        {"id": "r2", "meter_id": METER, "read_at": "2026-04-30T23:00:00", "value_kwh": "1177.000", "is_estimated": True},
    ])
    result = run(db)
    assert result.generated[0].invoice["is_estimated"] is True


# ---------------------------------------------------------------------------
# Walidacja przynależności budynku
# ---------------------------------------------------------------------------
def test_building_from_other_org_raises():
    db = base_db(buildings=[{"id": BUILDING, "org_id": "inna-org"}])
    with pytest.raises(PermissionError):
        run(db)


# ---------------------------------------------------------------------------
# monthly_allocated — alokacja wg udziału kWh budynku
# ---------------------------------------------------------------------------
def test_monthly_allocated_uses_building_total():
    # Dwa liczniki w budynku po 177 kWh → total 354. Składnik alokowany 100 zł.
    db = base_db()
    db["meters"].append({"id": "mtr-u2", "building_id": BUILDING, "tariff_id": TARIFF})
    db["readings"] += [
        {"id": "r3", "meter_id": "mtr-u2", "read_at": "2026-04-01T00:00:00", "value_kwh": "0.000", "is_estimated": False},
        {"id": "r4", "meter_id": "mtr-u2", "read_at": "2026-04-30T23:00:00", "value_kwh": "177.000", "is_estimated": False},
    ]
    db["tariff_components"] = [
        {"id": "c1", "tariff_id": TARIFF, "name": "Energia", "component_type": "per_kwh", "unit_price": "0.50000", "unit": "zł/kWh", "vat_rate": "23", "sort_order": 1},
        {"id": "c2", "tariff_id": TARIFF, "name": "Mocowa budynku", "component_type": "monthly_allocated", "unit_price": "100.00", "unit": "zł/mc", "vat_rate": "23", "sort_order": 2},
    ]
    result = run(db)
    lines = {l["label"]: l for l in result.generated[0].lines}
    # udział U1 = 177/354 = 0.5 → 100 * 0.5 = 50.00
    assert lines["Mocowa budynku"]["net_amount"] == "50.00"
