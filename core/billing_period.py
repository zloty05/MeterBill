"""Liczenie okresów rozliczeniowych — czyste funkcje, bez I/O.

Używane przez scheduler (tasks/celery_tasks.py) do ustalenia, za jaki okres
wygenerować faktury w dniu automatycznego uruchomienia.
"""
from __future__ import annotations

from datetime import date, timedelta


def previous_month_period(today: date | None = None) -> tuple[date, date]:
    """(pierwszy, ostatni) dzień miesiąca poprzedzającego `today` (domyślnie dziś).

    Przykład: dla 2026-06-04 zwraca (2026-05-01, 2026-05-31).
    Na granicy roku (np. 2026-01-15) → (2025-12-01, 2025-12-31).
    """
    today = today or date.today()
    first_of_this = today.replace(day=1)
    period_to = first_of_this - timedelta(days=1)  # ostatni dzień poprzedniego miesiąca
    period_from = period_to.replace(day=1)
    return period_from, period_to
