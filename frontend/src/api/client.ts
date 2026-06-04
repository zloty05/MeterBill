import { supabase } from "../lib/supabase";

// W devie VITE_API_BASE_URL jest puste → korzystamy z Vite proxy (/api → :8000).
// Na prod ustaw pełny origin backendu.
const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const PREFIX = "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

type Options = {
  method?: string;
  body?: unknown;
  // query params; undefined/null pomijane
  params?: Record<string, string | number | boolean | undefined | null>;
};

function buildUrl(path: string, params?: Options["params"]): string {
  const url = `${BASE}${PREFIX}${path}`;
  if (!params) return url;
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) qs.append(k, String(v));
  }
  const s = qs.toString();
  return s ? `${url}?${s}` : url;
}

/**
 * Wywołanie REST API z JWT z aktualnej sesji Supabase.
 * Token pobierany świeżo per request (auto-refresh w supabase-js).
 * 401 → wylogowanie (token wygasł / nieważny).
 */
export async function apiFetch<T>(path: string, opts: Options = {}): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(buildUrl(path, opts.params), {
    method: opts.method ?? "GET",
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  if (res.status === 401) {
    await supabase.auth.signOut();
    throw new ApiError(401, "Sesja wygasła — zaloguj się ponownie");
  }

  if (!res.ok) {
    let detail = `Błąd ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* odpowiedź bez JSON — zostaw domyślny komunikat */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
