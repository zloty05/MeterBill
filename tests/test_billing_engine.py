"""Testy silnika taryfowego (core/billing_engine).

Test referencyjny: faktura ZAEL G11, kwiecień 2026, 177 kWh → 172,17 zł netto /
211,77 zł brutto (ENERGYBILL_MVP_PROMPT.md l. 443-455).
"""
from datetime import date
from decimal import Decimal

import pytest

from core.billing_engine import (
    BillingContext,
    Tariff,
    TariffComponent,
    days_in_month,
    generate_invoice,
)


def zael_g11_tariff(margin_pct: str = "0") -> Tariff:
    """Składniki taryfy G11 ZAEL 2026 w kolejności jak na fakturze."""
    return Tariff(
        name="G11 – ZAEL 2026",
        margin_pct=Decimal(margin_pct),
        components=[
            TariffComponent("Opłata obrotowa (energia)", "per_kwh", Decimal("0.51760"), "zł/kWh", sort_order=1),
            TariffComponent("Opłata zmienna sieciowa", "per_kwh", Decimal("0.25660"), "zł/kWh", sort_order=2),
            TariffComponent("Opłata jakościowa", "per_kwh", Decimal("0.03320"), "zł/kWh", sort_order=3),
            TariffComponent("Opłata OZE", "per_kwh", Decimal("0.00730"), "zł/kWh", sort_order=4),
            TariffComponent("Opłata kogeneracyjna", "per_kwh", Decimal("0.00300"), "zł/kWh", sort_order=5),
            TariffComponent("Opłata mocowa", "monthly_fixed", Decimal("17.18"), "zł/mc", sort_order=6),
            TariffComponent("Abonament", "monthly_fixed", Decimal("5.00"), "zł/mc", sort_order=7),
            TariffComponent("Opłata stała sieciowa", "monthly_fixed", Decimal("5.25"), "zł/mc", sort_order=8),
        ],
    )


def april_ctx(**overrides) -> BillingContext:
    base = dict(
        tenant_id="tenant-u1",
        kwh_consumed=Decimal("177"),
        period_from=date(2026, 4, 1),
        period_to=date(2026, 4, 30),
    )
    base.update(overrides)
    return BillingContext(**base)


# ---------------------------------------------------------------------------
# Test referencyjny (złoty)
# ---------------------------------------------------------------------------
def test_zael_reference_invoice_totals():
    result = generate_invoice(zael_g11_tariff(), april_ctx())

    assert result.kwh_consumed == Decimal("177")
    assert result.net_amount == Decimal("172.17")
    assert result.vat_amount == Decimal("39.60")
    assert result.gross_amount == Decimal("211.77")
    assert result.is_estimated is False
    assert len(result.lines) == 8


def test_zael_reference_line_breakdown():
    result = generate_invoice(zael_g11_tariff(), april_ctx())
    by_label = {l.label: l for l in result.lines}

    assert by_label["Opłata obrotowa (energia)"].net_amount == Decimal("91.62")
    assert by_label["Opłata zmienna sieciowa"].net_amount == Decimal("45.42")
    assert by_label["Opłata jakościowa"].net_amount == Decimal("5.88")
    assert by_label["Opłata OZE"].net_amount == Decimal("1.29")
    assert by_label["Opłata kogeneracyjna"].net_amount == Decimal("0.53")
    # Opłaty stałe — pełna kwota per lokal (pełny miesiąc)
    assert by_label["Opłata mocowa"].net_amount == Decimal("17.18")
    assert by_label["Abonament"].net_amount == Decimal("5.00")
    assert by_label["Opłata stała sieciowa"].net_amount == Decimal("5.25")


def test_per_kwh_line_has_quantity_and_unit():
    result = generate_invoice(zael_g11_tariff(), april_ctx())
    line = next(l for l in result.lines if l.label == "Opłata obrotowa (energia)")
    assert line.quantity == Decimal("177")
    assert line.unit == "kWh"
    assert line.unit_price == Decimal("0.51760")
    assert line.vat_amount == Decimal("21.07")  # 91.62 * 23%


# ---------------------------------------------------------------------------
# Niepełny miesiąc — proporcja dni dla opłat stałych
# ---------------------------------------------------------------------------
def test_partial_month_prorates_fixed_only():
    # Najemca rozliczany przez 15 z 30 dni kwietnia → opłaty stałe / 2.
    result = generate_invoice(zael_g11_tariff(), april_ctx(billed_days=15))
    by_label = {l.label: l for l in result.lines}

    # per_kwh nie skalowane proporcją dni
    assert by_label["Opłata obrotowa (energia)"].net_amount == Decimal("91.62")
    # 17.18 * 15/30 = 8.59
    assert by_label["Opłata mocowa"].net_amount == Decimal("8.59")
    assert by_label["Abonament"].net_amount == Decimal("2.50")
    assert by_label["Opłata stała sieciowa"].net_amount == Decimal("2.63")  # 5.25/2=2.625→2.63


def test_full_month_when_billed_days_equals_days_in_month():
    result = generate_invoice(zael_g11_tariff(), april_ctx(billed_days=30))
    by_label = {l.label: l for l in result.lines}
    assert by_label["Opłata mocowa"].net_amount == Decimal("17.18")


def test_days_in_month_helper():
    assert days_in_month(date(2026, 4, 10)) == 30
    assert days_in_month(date(2026, 2, 1)) == 28
    assert days_in_month(date(2024, 2, 1)) == 29  # rok przestępny


# ---------------------------------------------------------------------------
# monthly_allocated — alokacja proporcjonalna do udziału kWh
# ---------------------------------------------------------------------------
def test_monthly_allocated_proportional_share():
    tariff = Tariff(
        name="alloc",
        components=[
            TariffComponent("Energia", "per_kwh", Decimal("0.50000"), sort_order=1),
            TariffComponent("Opłata mocowa budynku", "monthly_allocated", Decimal("100.00"), "zł/mc", sort_order=2),
        ],
    )
    # Najemca zużył 177 z 590 kWh budynku → udział 0.3 → 100 * 0.3 = 30.00
    ctx = april_ctx(kwh_consumed=Decimal("177"), building_total_kwh=Decimal("590"))
    result = generate_invoice(tariff, ctx)
    alloc = next(l for l in result.lines if l.label == "Opłata mocowa budynku")
    assert alloc.net_amount == Decimal("30.00")


def test_monthly_allocated_zero_building_total_is_zero():
    # Brak danych o zużyciu budynku → udział 0, bez dzielenia przez zero.
    tariff = Tariff(
        name="alloc",
        components=[
            TariffComponent("Opłata mocowa budynku", "monthly_allocated", Decimal("100.00"), "zł/mc"),
        ],
    )
    ctx = april_ctx(kwh_consumed=Decimal("177"), building_total_kwh=Decimal("0"))
    result = generate_invoice(tariff, ctx)
    assert result.lines[0].net_amount == Decimal("0.00")
    assert result.net_amount == Decimal("0.00")


# ---------------------------------------------------------------------------
# Marża zarządcy
# ---------------------------------------------------------------------------
def test_margin_added_as_separate_line():
    result = generate_invoice(zael_g11_tariff(margin_pct="10"), april_ctx())
    margin = next(l for l in result.lines if l.label == "Opłata za obsługę")
    # 10% z 172.17 = 17.217 → 17.22
    assert margin.net_amount == Decimal("17.22")
    assert result.net_amount == Decimal("172.17") + Decimal("17.22")
    assert len(result.lines) == 9


def test_no_margin_line_when_pct_zero():
    result = generate_invoice(zael_g11_tariff(margin_pct="0"), april_ctx())
    assert all(l.label != "Opłata za obsługę" for l in result.lines)


# ---------------------------------------------------------------------------
# Pozostałe edge-case'y
# ---------------------------------------------------------------------------
def test_zero_consumption_only_fixed_fees():
    result = generate_invoice(zael_g11_tariff(), april_ctx(kwh_consumed=Decimal("0")))
    by_label = {l.label: l for l in result.lines}
    assert by_label["Opłata obrotowa (energia)"].net_amount == Decimal("0.00")
    # Opłaty stałe nadal naliczone
    assert by_label["Opłata mocowa"].net_amount == Decimal("17.18")
    # netto = same opłaty stałe = 27.43
    assert result.net_amount == Decimal("27.43")


def test_estimated_reading_flag_propagated():
    result = generate_invoice(zael_g11_tariff(), april_ctx(is_estimated=True))
    assert result.is_estimated is True


def test_negative_consumption_raises():
    with pytest.raises(ValueError, match="ujemne"):
        generate_invoice(zael_g11_tariff(), april_ctx(kwh_consumed=Decimal("-5")))


def test_unknown_component_type_raises():
    tariff = Tariff(
        name="bad",
        components=[TariffComponent("X", "weird_type", Decimal("1"))],
    )
    with pytest.raises(ValueError, match="Nieznany component_type"):
        generate_invoice(tariff, april_ctx())


def test_lines_ordered_by_sort_order():
    result = generate_invoice(zael_g11_tariff(margin_pct="5"), april_ctx())
    orders = [l.sort_order for l in result.lines]
    assert orders == sorted(orders)
    # marża zawsze na końcu
    assert result.lines[-1].label == "Opłata za obsługę"


def test_float_inputs_handled_via_decimal():
    # Silnik akceptuje float w unit_price/kwh i konwertuje bezpiecznie przez str.
    tariff = Tariff(
        name="f",
        components=[TariffComponent("Energia", "per_kwh", 0.5176)],  # type: ignore[arg-type]
    )
    ctx = april_ctx(kwh_consumed=177)  # type: ignore[arg-type]
    result = generate_invoice(tariff, ctx)
    assert result.lines[0].net_amount == Decimal("91.62")
