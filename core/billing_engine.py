"""Silnik taryfowy — czysta logika obliczania faktury z odczytów i taryfy.

Projekt: funkcja `generate_invoice` nie wykonuje I/O. Wszystkie dane wejściowe
(odczyty, taryfa, składniki, kontekst budynku) dostaje jako struktury, a zwraca
`InvoiceResult` (nagłówek faktury + pozycje). Dzięki temu silnik jest w pełni
testowalny bez bazy. Pobieranie danych z Supabase i zapis żyją w warstwie
routera/serwisu (poza tym modułem).

Pieniądze liczymy na `Decimal` (zgodność z NUMERIC w Postgres, brak błędów
groszowych float). Zaokrąglenie: ROUND_HALF_UP do 0,01 zł — jak na fakturze.

Składniki taryfy (component_type, ze schematu supabase/migrations/..._initial.sql):
  - per_kwh            → ilość = zużycie kWh, cena = unit_price (zł/kWh)
  - monthly_fixed      → stała kwota per lokal; przy niepełnym miesiącu naliczana
                         proporcjonalnie do liczby dni rozliczanych
  - monthly_allocated  → kwota budynku alokowana proporcjonalnie do udziału kWh
                         najemcy w całym budynku

Edge-case'y (ENERGYBILL_MVP_PROMPT.md l. 600-614):
  - niepełny miesiąc: opłaty stałe × (dni_rozliczane / dni_w_miesiącu)
  - brak total_kwh budynku: udział = 0 (bez dzielenia przez zero)
  - odczyt szacowany: flaga is_estimated przenoszona na fakturę
  - marża zarządcy: doliczana jako osobna pozycja od sumy netto pozostałych
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# Typy składników — odpowiadają ENUM component_type w migracji.
PER_KWH = "per_kwh"
MONTHLY_FIXED = "monthly_fixed"
MONTHLY_ALLOCATED = "monthly_allocated"

_CENT = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    """Zaokrągla kwotę do groszy (ROUND_HALF_UP)."""
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _d(value) -> Decimal:
    """Konwersja na Decimal odporna na float (przez str)."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


# ----------------------------------------------------------------------------
# Struktury wejściowe (mapują wiersze z bazy, ale bez zależności od Supabase)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class TariffComponent:
    """Składnik taryfy (wiersz tariff_components)."""

    name: str
    component_type: str          # per_kwh | monthly_fixed | monthly_allocated
    unit_price: Decimal
    unit: str = "zł/kWh"
    vat_rate: Decimal = Decimal("23")
    component_id: str | None = None
    sort_order: int = 0


@dataclass(frozen=True)
class Tariff:
    """Szablon taryfowy (wiersz tariff_templates) wraz ze składnikami."""

    name: str
    components: list[TariffComponent]
    margin_pct: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("23")     # stawka dla pozycji marży


@dataclass(frozen=True)
class BillingContext:
    """Dane rozliczanego najemcy/licznika w danym okresie.

    kwh_consumed     — zużycie najemcy (reading_end - reading_start)
    building_total_kwh — suma zużycia całego budynku (dla monthly_allocated)
    billed_days      — liczba dni rozliczanych (proporcja niepełnego miesiąca)
    period_from / period_to — granice okresu faktury (do nagłówka i dni miesiąca)
    is_estimated     — czy oparto na odczycie szacowanym
    """

    tenant_id: str
    kwh_consumed: Decimal
    period_from: date
    period_to: date
    building_total_kwh: Decimal = Decimal("0")
    billed_days: int | None = None        # None = pełny miesiąc
    is_estimated: bool = False


# ----------------------------------------------------------------------------
# Struktury wyjściowe
# ----------------------------------------------------------------------------
@dataclass
class InvoiceLine:
    """Pozycja faktury (wiersz invoice_lines)."""

    label: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    net_amount: Decimal
    vat_rate: Decimal
    component_id: str | None = None
    sort_order: int = 0

    @property
    def vat_amount(self) -> Decimal:
        return _money(self.net_amount * self.vat_rate / Decimal("100"))

    @property
    def gross_amount(self) -> Decimal:
        return self.net_amount + self.vat_amount


@dataclass
class InvoiceResult:
    """Wynik silnika: nagłówek faktury + pozycje (bez invoice_no/PDF/zapisu)."""

    tenant_id: str
    period_from: date
    period_to: date
    kwh_consumed: Decimal
    net_amount: Decimal
    vat_amount: Decimal
    gross_amount: Decimal
    is_estimated: bool
    lines: list[InvoiceLine] = field(default_factory=list)


# ----------------------------------------------------------------------------
# Silnik
# ----------------------------------------------------------------------------
def days_in_month(d: date) -> int:
    """Liczba dni w miesiącu danej daty."""
    return calendar.monthrange(d.year, d.month)[1]


def generate_invoice(tariff: Tariff, ctx: BillingContext) -> InvoiceResult:
    """Liczy fakturę dla jednego najemcy na podstawie taryfy i kontekstu okresu.

    Zwraca InvoiceResult z listą pozycji i sumami. Nie nadaje numeru faktury
    ani nie zapisuje do bazy — to robi warstwa wyżej.
    """
    kwh = _d(ctx.kwh_consumed)
    if kwh < 0:
        raise ValueError(f"Zużycie kWh nie może być ujemne: {kwh}")

    building_total = _d(ctx.building_total_kwh)

    # Proporcja niepełnego miesiąca: dni_rozliczane / dni_w_miesiącu.
    total_days = days_in_month(ctx.period_from)
    if ctx.billed_days is None:
        day_share = Decimal("1")
    else:
        if ctx.billed_days < 0:
            raise ValueError(f"billed_days nie może być ujemne: {ctx.billed_days}")
        day_share = _d(ctx.billed_days) / _d(total_days)

    lines: list[InvoiceLine] = []

    for comp in sorted(tariff.components, key=lambda c: c.sort_order):
        price = _d(comp.unit_price)
        vat = _d(comp.vat_rate)

        if comp.component_type == PER_KWH:
            net = _money(kwh * price)
            lines.append(InvoiceLine(
                label=comp.name,
                quantity=kwh,
                unit="kWh",
                unit_price=price,
                net_amount=net,
                vat_rate=vat,
                component_id=comp.component_id,
                sort_order=comp.sort_order,
            ))

        elif comp.component_type == MONTHLY_FIXED:
            # Stała kwota per lokal, proporcjonalna do dni przy niepełnym miesiącu.
            net = _money(price * day_share)
            lines.append(InvoiceLine(
                label=comp.name,
                quantity=Decimal("1"),
                unit="mc",
                unit_price=net,
                net_amount=net,
                vat_rate=vat,
                component_id=comp.component_id,
                sort_order=comp.sort_order,
            ))

        elif comp.component_type == MONTHLY_ALLOCATED:
            # Kwota budynku dzielona wg udziału kWh najemcy.
            share = kwh / building_total if building_total > 0 else Decimal("0")
            net = _money(price * share)
            lines.append(InvoiceLine(
                label=comp.name,
                quantity=Decimal("1"),
                unit="mc",
                unit_price=net,
                net_amount=net,
                vat_rate=vat,
                component_id=comp.component_id,
                sort_order=comp.sort_order,
            ))

        else:
            raise ValueError(f"Nieznany component_type: {comp.component_type!r}")

    # Marża zarządcy — osobna pozycja od sumy netto pozostałych.
    margin_pct = _d(tariff.margin_pct)
    if margin_pct > 0:
        subtotal = sum((l.net_amount for l in lines), Decimal("0"))
        margin_net = _money(subtotal * margin_pct / Decimal("100"))
        if margin_net != 0:
            lines.append(InvoiceLine(
                label="Opłata za obsługę",
                quantity=Decimal("1"),
                unit="mc",
                unit_price=margin_net,
                net_amount=margin_net,
                vat_rate=_d(tariff.vat_rate),
                sort_order=9999,
            ))

    net_total = sum((l.net_amount for l in lines), Decimal("0"))
    # VAT liczony per stawka (suma netto w obrębie stawki × stawka), nie per
    # pozycja — deterministyczne i zgodne z praktyką fakturową.
    vat_total = _vat_by_rate(lines)
    gross_total = net_total + vat_total

    return InvoiceResult(
        tenant_id=ctx.tenant_id,
        period_from=ctx.period_from,
        period_to=ctx.period_to,
        kwh_consumed=kwh,
        net_amount=_money(net_total),
        vat_amount=_money(vat_total),
        gross_amount=_money(gross_total),
        is_estimated=ctx.is_estimated,
        lines=lines,
    )


def _vat_by_rate(lines: list[InvoiceLine]) -> Decimal:
    """Sumuje VAT grupując netto po stawce (poprawne podatkowo zaokrąglenie)."""
    by_rate: dict[Decimal, Decimal] = {}
    for l in lines:
        by_rate[l.vat_rate] = by_rate.get(l.vat_rate, Decimal("0")) + l.net_amount
    total = Decimal("0")
    for rate, net in by_rate.items():
        total += _money(net * rate / Decimal("100"))
    return total
