"""Render faktury do PDF (WeasyPrint z szablonu Jinja2) — czysta warstwa bez I/O sieciowego.

Wejście to `InvoicePdfData` (dicty pobrane wcześniej z bazy przez warstwę I/O —
core/invoice_delivery). Wyjście to bajty PDF. Dzięki temu render jest testowalny
bez Supabase i Resend.

Pieniądze liczymy/formatujemy na Decimal (spójnie z billing_engine i schematem
NUMERIC). VAT grupujemy per stawka — ta sama zasada co _vat_by_rate w silniku.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_CENT = Decimal("0.01")

_MIESIACE = [
    "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]


def _d(value) -> Decimal:
    """Konwersja na Decimal odporna na float (przez str). None → 0."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


# ----------------------------------------------------------------------------
# Struktury wejściowe (agregat danych do renderu; bez zależności od Supabase)
# ----------------------------------------------------------------------------
@dataclass
class InvoicePdfData:
    """Komplet danych do wyrenderowania jednej faktury PDF."""

    invoice: dict                 # wiersz invoices
    lines: list[dict]             # wiersze invoice_lines
    organization: dict            # sprzedawca
    tenant: dict                  # nabywca
    reading_start: dict | None = None   # odczyt początkowy (value_kwh, read_at, read_type)
    reading_end: dict | None = None     # odczyt końcowy
    meter: dict | None = None           # licznik (serial_no, label) — opcjonalnie
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Pomocnicze: kwota słownie, formatowanie, podsumowanie VAT
# ----------------------------------------------------------------------------
_JEDNOSTKI = ["", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem",
              "osiem", "dziewięć"]
_NASCIE = ["dziesięć", "jedenaście", "dwanaście", "trzynaście", "czternaście",
           "piętnaście", "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście"]
_DZIESIATKI = ["", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt",
               "sześćdziesiąt", "siedemdziesiąt", "osiemdziesiąt", "dziewięćdziesiąt"]
_SETKI = ["", "sto", "dwieście", "trzysta", "czterysta", "pięćset", "sześćset",
          "siedemset", "osiemset", "dziewięćset"]
# formy: [mianownik lp, mianownik lm (2-4), dopełniacz lm (5+, 0)]
_GRUPY = [
    ("", "", ""),
    ("tysiąc", "tysiące", "tysięcy"),
    ("milion", "miliony", "milionów"),
    ("miliard", "miliardy", "miliardów"),
]


def _odmiana(n: int, formy: tuple[str, str, str]) -> str:
    """Wybiera formę gramatyczną rzeczownika dla liczby n (PL)."""
    if n == 1:
        return formy[0]
    ostatnie = n % 10
    przedostatnie = (n // 10) % 10
    if przedostatnie != 1 and 2 <= ostatnie <= 4:
        return formy[1]
    return formy[2]


def _trojka_slownie(n: int) -> str:
    """Liczba 0–999 słownie (bez nazwy grupy)."""
    setki = n // 100
    reszta = n % 100
    dziesiatki = reszta // 10
    jednosci = reszta % 10
    czesci = []
    if setki:
        czesci.append(_SETKI[setki])
    if dziesiatki == 1:
        czesci.append(_NASCIE[jednosci])
    else:
        if dziesiatki:
            czesci.append(_DZIESIATKI[dziesiatki])
        if jednosci:
            czesci.append(_JEDNOSTKI[jednosci])
    return " ".join(czesci)


def _liczba_slownie(n: int) -> str:
    """Liczba całkowita >= 0 słownie po polsku."""
    if n == 0:
        return "zero"
    grupy = []
    idx = 0
    while n > 0:
        trojka = n % 1000
        if trojka:
            slowo = _trojka_slownie(trojka)
            nazwa = _odmiana(trojka, _GRUPY[idx]) if idx > 0 else ""
            grupy.append((slowo + " " + nazwa).strip())
        n //= 1000
        idx += 1
    return " ".join(reversed(grupy))


def amount_in_words(value) -> str:
    """Kwota słownie po polsku, np. 211,77 → "dwieście jedenaście zł 77/100".

    Grosze podajemy liczbowo (praktyka fakturowa). Zaokrąglamy do groszy.
    """
    amount = _money(_d(value))
    zlote = int(amount)
    grosze = int((amount - zlote) * 100)
    return f"{_liczba_slownie(zlote)} zł {grosze:02d}/100"


def format_money(value) -> str:
    """Formatuje kwotę jak na fakturze: 1 234,56 (spacja co tysiąc, przecinek)."""
    amount = _money(_d(value))
    s = f"{amount:,.2f}"  # 1,234.56
    s = s.replace(",", " ").replace(".", ",")
    return s


def format_qty(value) -> str:
    """Ilość: do 3 miejsc, przecinek dziesiętny, bez zbędnych zer."""
    q = _d(value)
    s = f"{q:.3f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def format_price(value) -> str:
    """Cena jednostkowa: do 5 miejsc, przecinek."""
    p = _d(value)
    s = f"{p:.5f}".rstrip("0").rstrip(".")
    if "." not in s and "," not in s:
        s += ",00"
    return s.replace(".", ",")


def line_vat_amount(net, vat_rate) -> Decimal:
    return _money(_d(net) * _d(vat_rate) / Decimal("100"))


def line_gross_amount(net, vat_rate) -> Decimal:
    return _d(net) + line_vat_amount(net, vat_rate)


def vat_summary(lines: list[dict]) -> list[dict]:
    """Grupuje pozycje po stawce VAT i zwraca podsumowanie netto/VAT/brutto.

    VAT liczony od sumy netto w obrębie stawki (jak _vat_by_rate w billing_engine),
    nie sumowaniem zaokrąglonych pozycji — deterministyczne i zgodne podatkowo.
    """
    by_rate: dict[Decimal, Decimal] = {}
    for l in lines:
        rate = _d(l.get("vat_rate"))
        by_rate[rate] = by_rate.get(rate, Decimal("0")) + _d(l.get("net_amount"))
    rows = []
    for rate in sorted(by_rate):
        net = _money(by_rate[rate])
        vat = _money(net * rate / Decimal("100"))
        rows.append({
            "vat_rate": rate,
            "net_amount": net,
            "vat_amount": vat,
            "gross_amount": net + vat,
        })
    return rows


def totals(lines: list[dict]) -> dict:
    """Sumy faktury: netto, VAT (per stawka), brutto."""
    summary = vat_summary(lines)
    net = sum((r["net_amount"] for r in summary), Decimal("0"))
    vat = sum((r["vat_amount"] for r in summary), Decimal("0"))
    return {"net_amount": net, "vat_amount": vat, "gross_amount": net + vat}


# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["money"] = format_money
    env.filters["qty"] = format_qty
    env.filters["price"] = format_price
    return env


def render_invoice_html(data: InvoicePdfData) -> str:
    """Renderuje szablon faktury do HTML (przydatne do debugu i testów)."""
    env = _build_env()
    template = env.get_template("invoice.html")

    summary = vat_summary(data.lines)
    sums = totals(data.lines)
    # wzbogać pozycje o brutto do tabeli
    rendered_lines = []
    for l in sorted(data.lines, key=lambda r: r.get("sort_order", 0)):
        rendered_lines.append({
            **l,
            "gross_amount": line_gross_amount(l.get("net_amount"), l.get("vat_rate")),
        })

    period_from = str(data.invoice.get("period_from", ""))[:10]
    sale_month = ""
    if len(period_from) == 10:
        y, m, _ = period_from.split("-")
        sale_month = f"{_MIESIACE[int(m)]} {y}"

    return template.render(
        inv=data.invoice,
        org=data.organization,
        tenant=data.tenant,
        lines=rendered_lines,
        vat_rows=summary,
        sums=sums,
        amount_words=amount_in_words(sums["gross_amount"]),
        reading_start=data.reading_start,
        reading_end=data.reading_end,
        meter=data.meter,
        sale_month=sale_month,
    )


def render_invoice_pdf(data: InvoicePdfData) -> bytes:
    """Renderuje fakturę do PDF (bajty). Import WeasyPrint leniwy — biblioteka
    ciągnie natywne zależności (cairo/pango), niepotrzebne dla samego HTML/testów."""
    from weasyprint import HTML  # import leniwy

    html = render_invoice_html(data)
    return HTML(string=html).write_pdf()
