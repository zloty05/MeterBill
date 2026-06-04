"""Testy schedulera (tasks/celery_tasks) i liczenia okresu (core/billing_period).

Bez sieci i bez Redisa — task wołany bezpośrednio jako funkcja (eager), klient
Supabase podmieniony na in-memory FakeSupabase.
"""
from datetime import date

import pytest

import tasks.celery_tasks as ct
from core.billing_period import previous_month_period
from tests.fake_supabase import FakeSupabase
from tests.test_invoice_service import ZAEL_COMPONENTS

# ---------------------------------------------------------------------------
# previous_month_period — czysta funkcja
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "today,expected_from,expected_to",
    [
        (date(2026, 6, 4), date(2026, 5, 1), date(2026, 5, 31)),   # środek roku
        (date(2026, 1, 15), date(2025, 12, 1), date(2025, 12, 31)),  # granica roku
        (date(2026, 3, 1), date(2026, 2, 1), date(2026, 2, 28)),   # 1. dnia miesiąca, luty
        (date(2024, 3, 10), date(2024, 2, 1), date(2024, 2, 29)),  # rok przestępny
    ],
)
def test_previous_month_period(today, expected_from, expected_to):
    assert previous_month_period(today) == (expected_from, expected_to)


def test_previous_month_period_defaults_to_today(monkeypatch):
    # Bez argumentu bierze date.today(); sprawdzamy że w ogóle liczy poprzedni miesiąc.
    pf, pt = previous_month_period()
    assert pf.day == 1
    assert pf < pt


# ---------------------------------------------------------------------------
# generate_all_invoices — iteracja po budynkach/org
# ---------------------------------------------------------------------------


def _building_db(building_id, org_id):
    """Komplet danych jednego budynku gotowy do wygenerowania 1 faktury (ZAEL)."""
    tariff = f"tar-{building_id}"
    meter = f"mtr-{building_id}"
    tenant = f"ten-{building_id}"
    return {
        "buildings": [{"id": building_id, "org_id": org_id}],
        "tenants": [
            {"id": tenant, "name": f"Najemca {building_id}", "building_id": building_id, "active": True}
        ],
        "meters": [{"id": meter, "building_id": building_id, "tariff_id": tariff}],
        "meter_assignments": [
            {"id": f"a-{building_id}", "tenant_id": tenant, "meter_id": meter, "valid_from": "2026-01-01", "valid_to": None}
        ],
        "tariff_templates": [
            {"id": tariff, "org_id": org_id, "name": "G11 – ZAEL 2026", "margin_pct": "0", "vat_rate": "23"}
        ],
        "tariff_components": [dict(c, tariff_id=tariff) for c in ZAEL_COMPONENTS],
        "readings": [
            {"id": f"r1-{building_id}", "meter_id": meter, "read_at": "2026-05-01T00:00:00", "value_kwh": "1000.000", "is_estimated": False},
            {"id": f"r2-{building_id}", "meter_id": meter, "read_at": "2026-05-31T23:00:00", "value_kwh": "1177.000", "is_estimated": False},
        ],
    }


def _merge(*dbs):
    """Skleja kilka słowników danych w jedną bazę FakeSupabase."""
    merged: dict = {"invoices": [], "invoice_lines": []}
    for db in dbs:
        for table, rows in db.items():
            merged.setdefault(table, []).extend(rows)
    return merged


def test_generate_all_invoices_iterates_all_buildings_and_orgs(monkeypatch):
    # 2 budynki w 2 różnych organizacjach.
    db = _merge(_building_db("bld-1", "org-1"), _building_db("bld-2", "org-2"))
    fake = FakeSupabase(db)
    monkeypatch.setattr(ct, "service_client", lambda: fake)

    summary = ct.generate_all_invoices("2026-05-01", "2026-05-31")

    assert summary["buildings"] == 2
    assert summary["generated"] == 2
    assert summary["skipped"] == 0
    assert summary["errors"] == []
    assert summary["period_from"] == "2026-05-01"
    assert summary["period_to"] == "2026-05-31"
    # Faktycznie zapisane w bazie.
    assert len(fake.data["invoices"]) == 2
    orgs = {inv["org_id"] for inv in fake.data["invoices"]}
    assert orgs == {"org-1", "org-2"}


def test_generate_all_invoices_default_period(monkeypatch):
    # Bez argumentów → poprzedni pełny miesiąc. Ustawiamy "dziś" na czerwiec 2026,
    # więc okres = maj 2026 (pod który skrojone są odczyty).
    monkeypatch.setattr(ct, "previous_month_period", lambda today=None: (date(2026, 5, 1), date(2026, 5, 31)))
    fake = FakeSupabase(_building_db("bld-1", "org-1"))
    monkeypatch.setattr(ct, "service_client", lambda: fake)

    summary = ct.generate_all_invoices()

    assert summary["generated"] == 1
    assert summary["period_from"] == "2026-05-01"


def test_one_building_error_does_not_abort_run(monkeypatch):
    # Budynek "bld-bad" wywoła PermissionError (inny org_id w wierszu niż w bazie),
    # ale to budynek dobry powinien się przeliczyć mimo to.
    good = _building_db("bld-ok", "org-1")
    fake = FakeSupabase(good)
    monkeypatch.setattr(ct, "service_client", lambda: fake)

    real_generate = ct.generate_invoices_for_building

    def flaky(client, *, org_id, building_id, period_from, period_to, due_days):
        if building_id == "bld-bad":
            raise RuntimeError("symulowany błąd budynku")
        return real_generate(
            client, org_id=org_id, building_id=building_id,
            period_from=period_from, period_to=period_to, due_days=due_days,
        )

    monkeypatch.setattr(ct, "generate_invoices_for_building", flaky)
    # Dorzucamy wadliwy budynek do listy zwracanej przez .table("buildings").
    fake.data["buildings"].append({"id": "bld-bad", "org_id": "org-1"})

    summary = ct.generate_all_invoices("2026-05-01", "2026-05-31")

    assert summary["buildings"] == 1  # tylko dobry policzony
    assert summary["generated"] == 1
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["building_id"] == "bld-bad"
    assert "symulowany" in summary["errors"][0]["error"]
