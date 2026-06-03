"""Lekki in-memory fake klienta Supabase (PostgREST) do testów bez sieci.

Obsługuje podzbiór fluent API używany przez core/invoice_service:
  table(name).select(...).eq().lte().order().limit().execute()
  table(name).insert(row|rows).execute()
  rpc("next_invoice_no", params).execute()

Dane trzymane jako dict[table_name] -> list[dict]. Filtry eq/lte aplikowane przy
execute(). insert() dokleja wiersze (z auto-id) i zwraca je w .data.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class _Result:
    data: object


class _Query:
    def __init__(self, db: "FakeSupabase", table: str):
        self._db = db
        self._table = table
        self._filters: list[tuple] = []   # (op, col, val)
        self._order = None
        self._desc = False
        self._limit = None
        self._insert_payload = None

    # --- selektory/filtry (zwracają self dla łańcuchowania) ---
    def select(self, *_args, **_kwargs):
        return self

    def eq(self, col, val):
        self._filters.append(("eq", col, val))
        return self

    def lte(self, col, val):
        self._filters.append(("lte", col, val))
        return self

    def order(self, col, desc=False):
        self._order = col
        self._desc = desc
        return self

    def limit(self, n):
        self._limit = n
        return self

    # --- terminalne ---
    def execute(self):
        if self._insert_payload is not None:
            return self._do_insert()
        rows = list(self._db.data.get(self._table, []))
        for op, col, val in self._filters:
            if op == "eq":
                rows = [r for r in rows if str(r.get(col)) == str(val)]
            elif op == "lte":
                rows = [r for r in rows if str(r.get(col)) <= str(val)]
        if self._order is not None:
            rows.sort(key=lambda r: str(r.get(self._order) or ""), reverse=self._desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(data=rows)

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def _do_insert(self):
        payload = self._insert_payload
        rows = payload if isinstance(payload, list) else [payload]
        saved = []
        for row in rows:
            new = dict(row)
            new.setdefault("id", str(uuid.uuid4()))
            self._db.data.setdefault(self._table, []).append(new)
            saved.append(new)
        return _Result(data=saved)


class _Rpc:
    def __init__(self, db: "FakeSupabase", name, params):
        self._db = db
        self._name = name
        self._params = params

    def execute(self):
        if self._name == "next_invoice_no":
            p = self._params
            key = (p["p_org_id"], p["p_year"], p["p_month"])
            self._db.sequences[key] = self._db.sequences.get(key, 0) + 1
            return _Result(data=self._db.sequences[key])
        raise NotImplementedError(f"Fake RPC: {self._name}")


class FakeSupabase:
    """Fake klient: data[table] = list[dict]; sequences dla numeracji."""

    def __init__(self, data: dict | None = None):
        self.data = data or {}
        self.sequences: dict = {}

    def table(self, name):
        return _Query(self, name)

    def rpc(self, name, params):
        return _Rpc(self, name, params)
