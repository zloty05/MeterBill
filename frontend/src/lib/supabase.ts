import { createClient } from "@supabase/supabase-js";

// supabase-js służy WYŁĄCZNIE do logowania (zdobycie JWT). Dane lecą przez
// backend REST (/api/v1), nie bezpośrednio z tego klienta.
const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  // Czytelny błąd zamiast cichego "Invalid URL" z supabase-js.
  console.error(
    "Brak VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — skopiuj frontend/.env.example do frontend/.env i uzupełnij."
  );
}

export const supabase = createClient(url ?? "", anonKey ?? "", {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});
