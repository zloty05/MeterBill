"""Orkiestracja generowania faktur: pobranie danych z Supabase + silnik + zapis.

Warstwa między routerem a silnikiem taryfowym. Cała logika obliczeń żyje w
core/billing_engine.py — tu zajmujemy się tylko I/O (zapytania, mapowanie,
zapis) i decyzjami "który najemca pominąć".

Decyzje (zatwierdzone, ENERGYBILL_MVP_PROMPT.md + plan kroku 5):
  - odczyty graniczne: ostatni odczyt z read_at <= period_from / <= period_to;
  - brak odczytu start/end / przypisania / taryfy → najemca pomijany (skipped),
    pozostali rozliczani normalnie; nie szacujemy;
  - duplikat (faktura na ten sam okres już istnieje) → skipped;
  - faktura zapisywana ze statusem 'draft'.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from core.billing_engine import (
    BillingContext,
    Tariff,
    TariffComponent,
    generate_invoice,
)
from core.invoice_numbering import next_invoice_no
from core.readings import latest_reading_at_or_before as _latest_reading_at_or_before
from core.readings import parse_date as _parse_date


@dataclass
class GeneratedInvoice:
    """Zapisana faktura + jej pozycje (surowe dicty z bazy)."""

    invoice: dict
    lines: list[dict]


@dataclass
class Skipped:
    tenant_id: str
    tenant_name: str
    reason: str


@dataclass
class GenerationResult:
    generated: list[GeneratedInvoice]
    skipped: list[Skipped]


def _overlap_days(
    period_from: date, period_to: date, valid_from: date, valid_to: date | None
) -> int:
    """Liczba dni części wspólnej okresu faktury i przedziału przypisania (włącznie)."""
    start = max(period_from, valid_from)
    end = period_to if valid_to is None else min(period_to, valid_to)
    if end < start:
        return 0
    return (end - start).days + 1


def _full_month_days(period_from: date) -> int:
    return calendar.monthrange(period_from.year, period_from.month)[1]


def _map_tariff(template: dict, components: list[dict]) -> Tariff:
    comps = [
        TariffComponent(
            name=c["name"],
            component_type=c["component_type"],
            unit_price=Decimal(str(c["unit_price"])),
            unit=c.get("unit", "zł/kWh"),
            vat_rate=Decimal(str(c.get("vat_rate", 23))),
            component_id=c.get("id"),
            sort_order=c.get("sort_order", 0),
        )
        for c in components
    ]
    return Tariff(
        name=template["name"],
        components=comps,
        margin_pct=Decimal(str(template.get("margin_pct", 0))),
        vat_rate=Decimal(str(template.get("vat_rate", 23))),
    )


def _building_total_kwh(
    client, building_id: str, period_from: date, period_to: date
) -> Decimal:
    """Suma zużycia wszystkich liczników budynku w okresie (dla monthly_allocated)."""
    res = client.table("meters").select("id").eq("building_id", building_id).execute()
    total = Decimal("0")
    for m in res.data or []:
        start = _latest_reading_at_or_before(client, m["id"], period_from)
        end = _latest_reading_at_or_before(client, m["id"], period_to)
        if start is None or end is None:
            continue
        delta = Decimal(str(end["value_kwh"])) - Decimal(str(start["value_kwh"]))
        if delta > 0:
            total += delta
    return total


def generate_invoices_for_building(
    client,
    org_id: str,
    building_id: str,
    period_from: date,
    period_to: date,
    due_days: int = 14,
) -> GenerationResult:
    """Generuje faktury dla wszystkich aktywnych najemców budynku w okresie.

    `client` — klient Supabase (service_client). Izolację org wymusza app-layer:
    najpierw potwierdzamy, że budynek należy do org_id.
    """
    # 1. Walidacja przynależności budynku do organizacji.
    b = (
        client.table("buildings")
        .select("id, org_id")
        .eq("id", building_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    if not (b.data or []):
        raise PermissionError("Budynek nie istnieje lub nie należy do organizacji")

    generated: list[GeneratedInvoice] = []
    skipped: list[Skipped] = []

    # Suma kWh budynku — potrzebna tylko dla monthly_allocated; liczona raz.
    building_total = _building_total_kwh(client, building_id, period_from, period_to)

    # 2. Aktywni najemcy budynku.
    tenants_res = (
        client.table("tenants")
        .select("id, name")
        .eq("building_id", building_id)
        .eq("active", True)
        .execute()
    )

    for tenant in tenants_res.data or []:
        tenant_id = tenant["id"]
        tenant_name = tenant.get("name", "")

        try:
            result = _generate_for_tenant(
                client,
                org_id,
                tenant_id,
                tenant_name,
                period_from,
                period_to,
                building_total,
                due_days,
            )
        except _SkipTenant as skip:
            skipped.append(Skipped(tenant_id, tenant_name, skip.reason))
            continue

        generated.append(result)

    return GenerationResult(generated=generated, skipped=skipped)


class _SkipTenant(Exception):
    """Sygnał wewnętrzny: pomiń tego najemcę z podanym powodem."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _generate_for_tenant(
    client,
    org_id: str,
    tenant_id: str,
    tenant_name: str,
    period_from: date,
    period_to: date,
    building_total: Decimal,
    due_days: int,
) -> GeneratedInvoice:
    # Duplikat: faktura na ten sam okres już istnieje.
    dup = (
        client.table("invoices")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("period_from", period_from.isoformat())
        .eq("period_to", period_to.isoformat())
        .limit(1)
        .execute()
    )
    if dup.data or []:
        raise _SkipTenant("Faktura na ten okres już wygenerowana")

    # Aktywne przypisanie licznika w okresie.
    asg = (
        client.table("meter_assignments")
        .select("meter_id, valid_from, valid_to")
        .eq("tenant_id", tenant_id)
        .lte("valid_from", period_to.isoformat())
        .execute()
    )
    assignment = None
    for a in asg.data or []:
        valid_to = a.get("valid_to")
        if valid_to is None or _parse_date(valid_to) >= period_from:
            assignment = a
            break
    if assignment is None:
        raise _SkipTenant("Brak przypisanego licznika w okresie")

    meter_id = assignment["meter_id"]
    valid_from = _parse_date(assignment["valid_from"])
    valid_to = assignment.get("valid_to")
    valid_to = _parse_date(valid_to) if valid_to is not None else None

    # Odczyty graniczne.
    r_start = _latest_reading_at_or_before(client, meter_id, period_from)
    r_end = _latest_reading_at_or_before(client, meter_id, period_to)
    if r_start is None:
        raise _SkipTenant("Brak odczytu początkowego")
    if r_end is None:
        raise _SkipTenant("Brak odczytu końcowego")

    kwh = Decimal(str(r_end["value_kwh"])) - Decimal(str(r_start["value_kwh"]))
    if kwh < 0:
        raise _SkipTenant("Odczyt końcowy mniejszy od początkowego")

    # Taryfa licznika.
    meter_res = (
        client.table("meters").select("tariff_id").eq("id", meter_id).limit(1).execute()
    )
    meter_rows = meter_res.data or []
    tariff_id = meter_rows[0].get("tariff_id") if meter_rows else None
    if not tariff_id:
        raise _SkipTenant("Licznik bez przypisanej taryfy")

    tpl_res = (
        client.table("tariff_templates")
        .select("id, name, margin_pct, vat_rate")
        .eq("id", tariff_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    tpl_rows = tpl_res.data or []
    if not tpl_rows:
        raise _SkipTenant("Taryfa nie należy do organizacji")
    template = tpl_rows[0]

    comp_res = (
        client.table("tariff_components")
        .select("id, name, component_type, unit_price, unit, vat_rate, sort_order")
        .eq("tariff_id", tariff_id)
        .execute()
    )
    components = comp_res.data or []
    if not components:
        raise _SkipTenant("Taryfa bez składników")

    tariff = _map_tariff(template, components)

    # Proporcja dni: część wspólna okresu i przedziału przypisania.
    overlap = _overlap_days(period_from, period_to, valid_from, valid_to)
    full_days = _full_month_days(period_from)
    # billed_days=None oznacza "pełny miesiąc" dla silnika; ustawiamy gdy < pełny.
    billed_days = None if overlap >= full_days else overlap

    is_estimated = bool(r_start.get("is_estimated") or r_end.get("is_estimated"))

    ctx = BillingContext(
        tenant_id=tenant_id,
        kwh_consumed=kwh,
        period_from=period_from,
        period_to=period_to,
        building_total_kwh=building_total,
        billed_days=billed_days,
        is_estimated=is_estimated,
    )

    invoice_result = generate_invoice(tariff, ctx)

    # Numer faktury (atomowy RPC).
    invoice_no = next_invoice_no(client, org_id, period_from)
    due_date = period_to + timedelta(days=due_days)

    invoice_row = {
        "org_id": org_id,
        "tenant_id": tenant_id,
        "invoice_no": invoice_no,
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "kwh_consumed": str(invoice_result.kwh_consumed),
        "net_amount": str(invoice_result.net_amount),
        "vat_amount": str(invoice_result.vat_amount),
        "gross_amount": str(invoice_result.gross_amount),
        "status": "draft",
        "due_date": due_date.isoformat(),
        "is_estimated": invoice_result.is_estimated,
    }

    ins = client.table("invoices").insert(invoice_row).execute()
    saved_invoice = (ins.data or [invoice_row])[0]
    invoice_id = saved_invoice["id"]

    line_rows = [
        {
            "invoice_id": invoice_id,
            "component_id": l.component_id,
            "label": l.label,
            "quantity": str(l.quantity),
            "unit": l.unit,
            "unit_price": str(l.unit_price),
            "net_amount": str(l.net_amount),
            "vat_rate": str(l.vat_rate),
            "sort_order": l.sort_order,
        }
        for l in invoice_result.lines
    ]
    lines_ins = client.table("invoice_lines").insert(line_rows).execute()
    saved_lines = lines_ins.data or line_rows

    return GeneratedInvoice(invoice=saved_invoice, lines=saved_lines)
