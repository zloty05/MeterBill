# EnergyBill — Frontend (panel zarządcy)

React + Vite + TypeScript + Tailwind. Implementacja designu z [docs/](docs/)
(źródło prawdy wyglądu: `docs/README.md`, `docs/component-map.md`, `docs/design_files/`).

## Status (faza 3 — etap 1)

Zbudowane:
- Scaffold (Vite, TS, Tailwind), design tokeny portowane 1:1 z `docs/design_files/styles.css`
  (`src/styles/tokens.css`), fonty IBM Plex lokalnie (`@fontsource`).
- Auth: logowanie przez Supabase (`supabase-js` **tylko** do zdobycia JWT) — `src/auth/`, `src/screens/Login.tsx`.
- Warstwa API REST: `src/api/` — `client.ts` (Bearer z sesji, 401→wylogowanie),
  `types.ts` (lustro schematów `*Out` backendu), `endpoints.ts`.
- AppShell (Sidebar + Topbar + routing `useState`) — `src/components/layout/`.
- Ekran **Dashboard** (kafelki budynków + StatCards) na realnym API.
- Ekran **Budynki** (lista + szczegóły z zakładkami Liczniki/Najemcy + modal CRUD `POST/PATCH /buildings`).

Poza zakresem tego etapu (placeholdery): Liczniki, Najemcy, Taryfy, Faktury (+ drawer, bulk actions).

## Architektura danych

Frontend **nie** czyta tabel przez `supabase-js`. `supabase-js` służy wyłącznie do logowania;
wszystkie dane idą przez backend REST (`/api/v1`), który działa na `service_role` i filtruje po `org_id`.
Dlatego GRANT-y dla roli `authenticated` nie są potrzebne na tym etapie.

## Uruchomienie (dev)

```bash
cd frontend
cp .env.example .env        # uzupełnij VITE_SUPABASE_URL i VITE_SUPABASE_ANON_KEY
npm install
npm run dev                 # http://localhost:3000 (Vite proxy /api → :8000)
```

Backend musi działać równolegle:

```bash
# z katalogu głównego repo
uvicorn api.main:app --reload          # :8000
python scripts/make_test_token.py      # seed usera demo + profil w public.users
```

Zaloguj się danymi usera demo (z Supabase Auth). Po zalogowaniu Dashboard i Budynki
pobierają realne dane z API.

## Build / typecheck

```bash
npm run build        # tsc + vite build
npm run typecheck    # sam tsc --noEmit
```

## Porównanie z prototypem

```bash
npx serve docs/design_files     # otwórz "EnergyBill Dashboard.html"
```

## Uwagi

- Port dev = **3000** (spójnie z CORS backendu `FRONTEND_URL` i `docker-compose.yml`).
- Agregaty per budynek (liczba liczników/najemców, faktury gotowe/zaległe) liczone na froncie
  z list (`src/lib/aggregates.ts`); pola, których API nie dostarcza (status online/offline,
  kWh/mc) → `—`.
- Dockerfile + nginx dla prod-buildu (`docker-compose` serwis `frontend`) — do dorobienia przy deployu.
