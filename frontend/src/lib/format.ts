// Formatery liczb w pl-PL — odpowiedniki WF.money / WF.fmt z mockupów.

/** Kwota PLN: "1 234,56" (2 miejsca). Przyjmuje number lub string (Decimal z API). */
export function money(value: number | string): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Odczyt kWh: "1 234,567" (3 miejsca). */
export function kwh(value: number | string): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("pl-PL", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
}

/** Inicjały z nazwy ("M. Wójcik" → "MW", "Zarządca Tarnów" → "ZT"). */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const take = parts.slice(0, 2).map((p) => p.replace(/[^\p{L}]/gu, "").charAt(0).toUpperCase());
  return take.join("") || "?";
}
