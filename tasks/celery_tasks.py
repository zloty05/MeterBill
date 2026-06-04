"""Celery: scheduler automatycznego generowania faktur.

Realizuje obietnicę produktu — „automatyczne rozliczanie energii". Celery Beat
odpala `generate_all_invoices` w dniu `INVOICE_GENERATION_DAY` (config), za
poprzedni pełny miesiąc, tworząc faktury w statusie 'draft' (bez wysyłki —
zarządca przegląda i wysyła ręcznie, zgodnie z decyzją MVP).

Task to czysta orkiestracja nad istniejącym `generate_invoices_for_building`:
iteruje po wszystkich budynkach wszystkich organizacji. Izolację org wymusza
app-layer (każdy budynek niesie swój `org_id`, service dodatkowo waliduje
przynależność) — backend działa na SERVICE_KEY i omija RLS.
"""
from __future__ import annotations

from datetime import date

from celery import Celery
from celery.schedules import crontab

from api.config import get_settings
from core.billing_period import previous_month_period
from core.invoice_service import generate_invoices_for_building
from core.readings import parse_date
from db.supabase_client import service_client

settings = get_settings()

app = Celery("meterbill")
app.conf.broker_url = settings.redis_url
app.conf.result_backend = settings.redis_url
app.conf.timezone = "Europe/Warsaw"  # crontab day_of_month liczony w czasie lokalnym
app.conf.beat_schedule = {
    "generuj-faktury-miesiecznie": {
        "task": "tasks.celery_tasks.generate_all_invoices",
        # Dzień miesiąca z configu; godzina stała 6:00.
        "schedule": crontab(
            minute=0, hour=6, day_of_month=str(settings.invoice_generation_day)
        ),
    },
}


@app.task(name="tasks.celery_tasks.generate_all_invoices")
def generate_all_invoices(
    period_from: str | None = None, period_to: str | None = None
) -> dict:
    """Generuje faktury (draft) dla wszystkich budynków wszystkich org.

    Domyślnie za poprzedni pełny miesiąc. `period_from`/`period_to` (ISO daty,
    np. "2026-05-01") pozwalają odpalić ręcznie za dowolny okres. Błąd jednego
    budynku nie wstrzymuje pozostałych (ląduje w `summary["errors"]`).

    Zwraca podsumowanie liczbowe — trafia do logów Celery i odpowiedzi result
    backendu, do podglądu z ręcznego wyzwalacza.
    """
    client = service_client()

    if period_from and period_to:
        pf: date = parse_date(period_from)
        pt: date = parse_date(period_to)
    else:
        pf, pt = previous_month_period()

    due_days = settings.invoice_due_days

    buildings = client.table("buildings").select("id, org_id").execute().data or []
    summary: dict = {
        "period_from": pf.isoformat(),
        "period_to": pt.isoformat(),
        "buildings": 0,
        "generated": 0,
        "skipped": 0,
        "errors": [],
    }

    for b in buildings:
        try:
            res = generate_invoices_for_building(
                client,
                org_id=b["org_id"],
                building_id=b["id"],
                period_from=pf,
                period_to=pt,
                due_days=due_days,
            )
            summary["buildings"] += 1
            summary["generated"] += len(res.generated)
            summary["skipped"] += len(res.skipped)
        except Exception as exc:  # jeden budynek nie wywraca całego runu
            summary["errors"].append({"building_id": b["id"], "error": str(exc)})

    return summary
