# Handoff: EnergyBill SaaS — Panel zarządcy nieruchomości

## Overview

EnergyBill to B2B SaaS dla zarządców nieruchomości umożliwiający:
- monitoring podliczników M-Bus (odczyt co 15 min przez gateway WAGO PFC300),
- zarządzanie budynkami, licznikami i najemcami,
- definiowanie taryf energetycznych (składniki per kWh + stałe miesięczne),
- generowanie i wysyłanie faktur/rachunków e-mailem.

**Target stack:** React + Vite + Tailwind CSS  
**Rozdzielczość bazowa:** desktop-first; breakpoint 1180 px.

---

## O plikach w tym bundle

Pliki w folderze `design_files/` to **prototypy HTML** obrazujące zamierzony wygląd i zachowanie aplikacji.  
Nie są to pliki produkcyjne do bezpośredniego wdrożenia. Zadaniem dewelopera jest **odtworzenie tych ekranów w docelowym środowisku React + Vite + Tailwind**, zachowując układ, kolory, typografię i interakcje opisane w tym dokumencie.

**Fidelity: High-fidelity.** Kolory, fonty, spacing, etykiety, stany hover/active/disabled — wszystko jest finalne. Implementuj pixel-perfect w istniejącym stack'u.

---

## Design Tokens

### Kolory (CSS custom properties → Tailwind `extend`)

```css
/* Core palette */
--ink:         #1d2826   /* podstawowy tekst */
--ink-soft:    #5a6a65   /* tekst drugorzędny */
--ink-faint:   #93a09b   /* placeholder, subtext */
--paper:       #ffffff   /* powierzchnia kart */
--line:        #e6eae8   /* border domyślny */
--line-strong: #d6dcda   /* border wyróżniony */
--fill:        #f1f5f3   /* tło hover, inputs */
--fill-2:      #e8edeb   /* badge tła */
--fill-3:      #f8faf9   /* tło wierszy tabel */

/* Accent — teal/green */
--accent:      oklch(0.65 0.14 160)   /* #2fa87e przybliżone */
--accent-deep: oklch(0.5  0.13 162)   /* ciemny akcent, aktywne elementy */
--accent-soft: oklch(0.965 0.028 165) /* bardzo jasne tło akcentowe */
--accent-line: oklch(0.86 0.06 165)   /* border akcentowy */

/* Semantic */
--warn:        oklch(0.72 0.13 70)    /* bursztynowy ostrzeżenie */
--warn-soft:   oklch(0.96 0.04 78)
--warn-ink:    oklch(0.46 0.10 68)
--danger:      oklch(0.6  0.16 25)    /* czerwony błąd/zaległość */
--danger-soft: oklch(0.965 0.03 28)

/* Background strony */
background: #f3f6f5
```

**Tailwind `tailwind.config.js` extend:**
```js
colors: {
  ink:        '#1d2826',
  'ink-soft': '#5a6a65',
  'ink-faint':'#93a09b',
  paper:      '#ffffff',
  line:       '#e6eae8',
  'line-s':   '#d6dcda',
  fill:       '#f1f5f3',
  accent:     'oklch(0.65 0.14 160)',
  'accent-d': 'oklch(0.5 0.13 162)',
  'accent-s': 'oklch(0.965 0.028 165)',
  warn:       'oklch(0.72 0.13 70)',
  'warn-ink': 'oklch(0.46 0.10 68)',
  danger:     'oklch(0.6 0.16 25)',
}
```

### Sidebar themes
Sidebar przełącza się między dwoma motywami via `data-sidebar` na `<body>`:

| Token           | Light (`data-sidebar="light"`) | Dark (`data-sidebar="dark"`) |
|-----------------|-------------------------------|------------------------------|
| `--sb-bg`       | `#ffffff`                     | `#18211e`                    |
| `--sb-ink`      | `#1d2826`                     | `#e9efec`                    |
| `--sb-ink-soft` | `#6a7a74`                     | `#8ba099`                    |
| `--sb-line`     | `#e6eae8`                     | `#2a3733`                    |
| `--sb-active-bg`| `var(--accent-soft)`          | `oklch(0.34 0.07 162)`       |
| `--sb-active-ink`| `var(--accent-deep)`         | `#eafff5`                    |

### Density (gęstość)
Aplikacja obsługuje dwa tryby poprzez `data-density` na `<body>`:

| Token        | `comfortable` (default) | `compact`   |
|--------------|------------------------|-------------|
| `--pad`      | `22px`                 | `14px`      |
| `--gap`      | `18px`                 | `11px`      |
| `--row-pad`  | `13px`                 | `8px`       |
| `--fs`       | `14.5px`               | `13.5px`    |
| `--r`        | `12px`                 | `10px`      |

### Typografia

| Zmienna  | Wartość                                         | Zastosowanie               |
|----------|-------------------------------------------------|----------------------------|
| `--sans` | `"IBM Plex Sans"`, system-ui, sans-serif        | cały interfejs             |
| `--mono` | `"IBM Plex Mono"`, ui-monospace, SF Mono, Menlo | nr seryjne, kwoty, kody    |

**Skala typograficzna:**

| Rola              | Size         | Weight | Letter-spacing |
|-------------------|-------------|--------|----------------|
| Page heading      | 23px (20px compact) | 700 | -0.02em   |
| Card heading      | 15.5px      | 600    | -0.01em        |
| Modal heading     | 17px        | 700    | -0.01em        |
| Nav item          | 14px        | 500    | —              |
| Body / table row  | 14.5px (13.5px compact) | 400 | -0.005em |
| Label uppercase   | 11px        | 600    | 0.04em         |
| Subtext / helper  | 12–13px     | 400    | —              |
| Mono numeric      | 13px        | 600    | —              |
| Stat big number   | 34px (27px compact) | 700 | -0.03em  |

### Spacing

| Token      | Comfortable | Compact  | Użycie                      |
|------------|-------------|----------|-----------------------------|
| `--pad`    | 22px        | 14px     | padding kontenerów, topbar  |
| `--gap`    | 18px        | 11px     | gap między kartami          |
| `--row-pad`| 13px        | 8px      | padding wierszy tabel       |
| `--r`      | 12px        | 10px     | border-radius kart/modali   |
| `--r-sm`   | 9px         | 9px      | border-radius przycisków    |
| `--r-pill` | 999px       | 999px    | pill/badge                  |

### Shadows

```css
--shadow:      0 1px 2px rgba(20,40,35,.04), 0 1px 3px rgba(20,40,35,.06);
--shadow-card: 0 1px 2px rgba(20,40,35,.05), 0 2px 8px rgba(20,40,35,.05);
```

---

## Struktura aplikacji

```
App
├── Sidebar (nawigacja, 232px, sticky, full-height)
└── .main
    ├── Topbar (sticky, backdrop-filter: blur 6px)
    └── Screen Content (scrollable)
```

**Routing:** client-side, bez URL — `useState` przechowuje aktywny ekran. Sidebar `onClick` przełącza widok.

---

## Ekrany

### 1. Dashboard (`/dashboard`)

**Dwa warianty układu** — przełączane segmentowanym kontrolką (`.seg`) nad treścią:

#### Wariant A — „Co wymaga uwagi dziś"
```
LayoutAction
├── page-h: "Dzień dobry, M. · 4 budynki · 32 liczniki · maj 2026"
├── AttentionStrip (3 karty akcji: do wysłania / zaległe / offline)
├── StatCards (4 kafelki: budynki, liczniki online, faktury, zaległe)
├── InvoiceQueue (tabela faktur + bulk bar)
└── ReadingsTable (ostatnie 6 odczytów z gateway, limit=6)
```

**AttentionStrip:**
- Kontener: `border: 1px solid --accent-line`, `background: linear-gradient(180deg, --accent-soft, #fff 70%)`, `border-radius: --r`
- Nagłówek: ikona `bell` + tekst, kolor `--accent-deep`, font-weight 600
- Siatka 3 kart: `grid-template-columns: repeat(3, 1fr)`, gap 12px
- Każda karta: `background: white`, padding 15px, `border-radius: --r`, `--shadow`
  - `.send` → liczba w kolorze `--accent-deep`, przycisk `.btn.primary.sm`
  - `.overdue` → liczba w kolorze `--danger`, przycisk `.btn.sm`
  - `.estimate` → liczba w kolorze `--warn-ink`, przycisk `.btn.sm`

**StatCards (4 karty):**
- Grid: `repeat(4, 1fr)`, gap `--gap`
- Każda karta: `.sketch` (border + shadow), padding `--pad`
- Ikona w rogu (top-right): 20px, kolor `--ink-faint`, opacity 0.6
- Etykieta: 13px, weight 500, `--ink-soft`
- Liczba: 34px (27px compact), weight 700, letter-spacing -0.03em, `font-variant-numeric: tabular-nums`
- Subtext: 12px, `--ink-faint`
- Modyfikatory: `.accent` → liczba w `--accent-deep`, `.danger` → liczba w `--danger`

#### Wariant B — „Kafelki per budynek" (**domyślny**)
```
LayoutBuildings
├── page-h: "Budynki · kliknij budynek aby rozwinąć liczniki i najemców"
├── StatCards (identyczne jak wariant A)
└── .bld-grid (2 kolumny, gap --gap)
    └── BuildingTile × 4
```

**BuildingTile:**
- `.bld-head`: nazwa (16px, weight 600), adres + taryfa (12.5px, `--ink-soft`), status pill (ok/draft)
- `.bld-mini`: 4-kolumnowy grid z separatorami `border-right: 1px solid --line`
  - Liczby 21px weight 700; `.green` = `--accent-deep`, `.red` = `--danger`
  - Etykiety 11px, `--ink-soft`, margin-top 5px
  - Dane: `online/total`, `toSend`, `overdue`, `kWh/mc`
- Wiersze odczytów (`.bld-readrow`): do 3 ostatnich odczytów, flex row z separatorem
- `.bld-foot`: `background: --fill-3`, dwa przyciski: `ghost sm` „Generuj" + `primary sm` „Wyślij N"

---

### 2. Budynki (`/buildings`)

**Dwa stany: lista i szczegóły budynku.**

#### Lista budynków
```
page-h + btn primary "Dodaj budynek"
card.sketch
└── table.wf
    ├── th: Budynek | Taryfa | Liczniki | Najemcy | Do wysłania | Zaległe | akcje
    └── tbody
        └── tr.clickrow × N  ← klik otwiera szczegóły
            ├── Nazwa (cell-strong) + adres + PPE (cell-sub)
            ├── pill.ok "G11"
            ├── num-cell centered: online/total
            ├── num-cell centered: najemcy
            ├── num-cell centered: toSend
            ├── num-cell danger|sub: overdue lub "—"
            └── btn.sm.ghost "Edytuj" (stopPropagation) + chevron
```

**Interakcje:**
- Klik na wiersz → przejście do widoku szczegółów
- Klik „Edytuj" → modal `ModalBudynek` w trybie edycji (stopPropagation)
- Klik „Dodaj budynek" → modal `ModalBudynek` (nowy)
- Hover wiersza: `background: --fill-3`

#### Szczegóły budynku
```
backlink "← Wszystkie budynki"  +  btn.sm.ghost "Edytuj budynek"
page-h: nazwa budynku + adres (small)
card.sketch
├── meta-strip (6 pól: Taryfa, PPE główne, Liczniki online, Najemcy, Do wysłania, Zużycie/mc)
├── tabs: [Liczniki badge | Najemcy badge | Historia]  +  btn.sm "Dodaj licznik/najemcę"
└── panel aktywnej zakładki
```

**meta-strip:** `display: flex; flex-wrap: wrap; gap: 22px; padding: 14px --pad; border-bottom: 1px solid --line; background: --fill-3`  
Każde pole `.mi`: etykieta uppercase 11px `--ink-faint`, wartość 14px weight 600. `.green` = `--accent-deep`.

**Tab: Liczniki** — tabela: `Lokal | Licznik/SN | Ostatni odczyt | Kiedy | Status | Trend 10 mc | Edytuj`
- Trend: Sparkline SVG (84×26px) + delta `▲/▼N%` w `--accent-deep` lub `--danger`, font mono 11.5px

**Tab: Najemcy** — tabela: `Lokal | Najemca | Typ | E-mail | NIP | Licznik | Status | Edytuj`
- Typ: pill.draft „firma · VAT" lub „os. fizyczna"
- Status: pill.online / pill.offline

**Tab: Historia** — oś czasu (`.tl`):
- `.tl-dot`: 9px circle; domyślnie `--accent` (zielony), `.gray` = `--ink-faint`, `.red` = `--danger`
- Każdy wpis: event name (weight 500) + detail (12px `--ink-soft`) + timestamp (mono 12px)

---

### 3. Liczniki (`/meters`)

```
page-h + btn.primary "Dodaj licznik"
card.sketch
├── filterbar
│   ├── label "Budynek:" + select (wszystkie / per budynek)
│   └── right: pill.online "N online" + pill.offline "N offline"
└── table.wf
    ├── th: Lokal | Budynek | Nr seryjny M-Bus | Ostatni odczyt | Kiedy | Status | Trend 10 mc | akcje
    └── tbody
        └── tr × 32
            ├── lokal (cell-strong)
            ├── budynek (cell-sub)
            ├── serial (mono) + "meterName · adr N" (cell-sub)
            ├── kwh num-cell right + "kWh" (cell-sub)
            ├── when (cell-sub)
            ├── Pill status: online / offline / est (szacowany)
            ├── SparkCell (sparkline + delta)
            └── btn.sm.ghost "Edytuj"
```

**Status pills:**
- `online` (ok) — zielony
- `offline` — czerwony
- `est` (szacowany) — bursztynowy; odczyt szacowany, brak danych z gateway

**Interakcje:**
- Zmiana select `Budynek` → filtruje tabele live (React state)
- „Edytuj" → modal `ModalLicznik` z wypełnionymi polami
- „Dodaj licznik" → modal `ModalLicznik` (nowy)

---

### 4. Najemcy (`/tenants`)

```
page-h + btn.primary "Dodaj najemcę"
card.sketch
├── filterbar: label "Budynek:" + select
└── table.wf
    ├── th: Najemca | Budynek/lokal | Typ | E-mail | Ostatnia faktura | Płatność | akcje
    └── tbody
        └── tr × N
            ├── name (cell-strong)
            ├── building · lokal (cell-sub)
            ├── Pill: "firma · VAT" lub "os. fizyczna" (klasa draft)
            ├── email (cell-sub)
            ├── lastInvoice (mono)
            ├── Pill: paid | overdue
            └── btn.sm.ghost "Edytuj"
```

**Interakcje:**
- Select filtruje po budynku
- „Edytuj" → `ModalNajemca` z danymi
- NIP w formularzu → hint dynamiczny: z NIP = „✓ Faktura VAT" (kolor `--accent-deep`), bez NIP = „Brak NIP → rachunek" (kolor `--warn-ink`)

---

### 5. Taryfy (`/tariffs`)

```
page-h
card.sketch
├── card-head: nazwa taryfy + pill.ok "aktywna" + btn.primary.sm "Dodaj taryfę" + btn.ghost.sm "Źródło: FV/..."
├── meta-strip (6 pól: Grupa taryfowa, VAT domyślny, Marża zarządcy, Obowiązuje od, Suma zmienna, Suma stała)
└── editable table
    ├── th: Nazwa składnika | Typ | Cena netto | VAT % | Cena brutto | del
    └── tbody — każdy wiersz to in-place editable inputs
        ├── input.tin.txt (nazwa) — pełna szerokość
        ├── select.tin.sel (per_kwh / monthly_fixed)
        ├── input.tin (cena) max-width 96px + unit label
        ├── input.tin (VAT %) max-width 56px
        ├── num-cell read-only (brutto obliczone)
        └── btn.row-del (trash icon)
└── btn "Dodaj składnik"
```

**`.tin` — edytowalne pole w tabeli:**
```css
font-family: --mono; font-size: 13px;
border: 1px solid transparent; border-radius: 6px; padding: 5px 8px;
background: --fill-3; text-align: right;
hover: border-color: --line-strong;
focus: border-color: --accent; background: #fff; box-shadow: 0 0 0 3px --accent-soft;
```

**`.row-del`:**
```css
default: color --ink-faint; background: none; border: none;
hover: color --danger; background: --danger-soft;
```

**Suma zmienna / stała** obliczana live z tablicy składników — wyświetlana w meta-strip.

**Interakcje:**
- Każda zmiana in-place → live recalculation brutto i sum
- „Dodaj składnik" → dopisuje wiersz z wartościami domyślnymi
- Trash → usuwa wiersz
- „Dodaj taryfę" → modal `ModalTaryfa` (lg, 860px) z klonem z istniejącej

---

### 6. Faktury (`/invoices`)

**Kluczowy ekran — obsługa masowych akcji.**

```
page-h "Faktury · N dokumentów · okres bieżący i archiwum"
card.sketch
├── filterbar (chip group)
│   └── chips: Wszystkie(N) | Szkice | Gotowe | Wysłane | Opłacone | Po terminie
├── bulk-bar  ← zawsze widoczny
│   ├── Cbx (select-all dla aktualnego filtra)
│   ├── "Zaznaczono N"
│   ├── btn.sm disabled jeśli 0 szkiców  "Generuj zaznaczone (N)"
│   └── btn.primary.sm disabled jeśli 0 gotowych  "Wyślij zaznaczone (N)"
└── table.wf
    ├── th: ☐ | Nr faktury | Najemca | Lokal | Okres | kWh | Brutto | Status | Termin
    └── tr.clickrow × N — klik otwiera InvoiceDrawer
        ├── td: Cbx (stopPropagation na td)
        ├── mono: nr faktury
        ├── cell-strong: najemca
        ├── cell-sub: lokal
        ├── cell-sub: okres "01–31.05.2026"
        ├── num-cell right: kWh
        ├── num-cell right: brutto zł (WF.money)
        ├── Pill status
        └── cell-sub: termin płatności
```

#### Status pills dla faktur
| Klucz     | Kolor tła        | Kolor tekstu      | Etykieta       |
|-----------|------------------|-------------------|----------------|
| `ready`   | `--accent-soft`  | `--accent-deep`   | gotowa         |
| `draft`   | `--fill`         | `--ink-soft`      | szkic          |
| `sent`    | `#eef4fb`        | `#2b5d96`         | wysłana        |
| `paid`    | `--accent-soft`  | `--accent-deep`   | opłacona       |
| `overdue` | `--danger-soft`  | `--danger`        | po terminie    |

#### Bulk-bar — zachowanie akcji masowych

```
Stan: sel = Set<invoiceId>
```

1. **Checkbox select-all** (lewy w bulk-bar):
   - `allOn = rows.every(r => sel.has(r.id))` gdzie `rows` = przefiltrowana lista
   - Klik gdy `allOn` → odznacz wszystkie z bieżącego filtra
   - Klik gdy `!allOn` → zaznacz wszystkie z bieżącego filtra
   - Zaznaczenia **trwają** po zmianie filtra (Set nie jest czyszczony)

2. **Licznik „Zaznaczono N"** — total ze wszystkich filtrów (nie tylko bieżącego)

3. **„Generuj zaznaczone (N)"** — `disabled` gdy `draftSel === 0`, gdzie `draftSel = selRows.filter(i => i.status === 'draft').length`

4. **„Wyślij zaznaczone (N)"** — `disabled` gdy `readySel === 0`, gdzie `readySel = selRows.filter(i => i.status === 'ready').length`

5. **Checkbox per-wiersz** (`td` z `stopPropagation`) — nie otwiera drawera

#### InvoiceDrawer (panel boczny)
- Position: `fixed; right: 0; top: 0; height: 100vh; width: 480px; max-width: 94vw`
- Slide-in: `transform: translateX(100%)` → `translateX(0)`, transition `0.26s cubic-bezier(.4,0,.2,1)`
- Overlay: `fixed; inset: 0; background: rgba(20,30,28,0.34)`, fade in/out `0.2s`
- Klik overlay zamyka drawer
- Klik wiersza tabeli → `setOpen(invoice)` → drawer się otwiera

**Zawartość drawera:**
```
drawer-head
├── nr faktury (mono) + nazwa najemcy (18px bold) + Pill status
└── X button

drawer-body (flex col gap-16, overflow-y: auto)
├── party-grid (2 kolumny): Sprzedawca | Nabywca
├── kv: Okres rozliczeniowy, Zużycie energii, Termin płatności
├── table.wf — pozycje faktury (z WF.tariff.components)
│   └── th: Pozycja | Ilość | Cena | Netto
├── sumrow: Razem netto / VAT 23% / Razem brutto (total: 17px bold)
└── party box "Do zapłaty" (accent-soft background): kwota + nr konta + tytuł

drawer-foot (border-top)
├── btn.ghost "Podgląd PDF"
└── btn.primary: "Generuj fakturę" (draft) LUB "Wyślij e-mailem" (ready/sent)
```

---

## Modale (formularze)

### Wspólna skorupka `ModalShell`
- Overlay: `fixed; inset: 0; background: rgba(20,30,28,0.40); z-index: 50`
- Pojawienie: `opacity: 0 → 1` (0.18s), `translateY(8px) scale(0.99) → none` (0.2s)
- Klik poza modal → zamknięcie
- Szerokość domyślna: `560px`; `.lg` = `860px` (modal Taryfy)
- Max-height: `calc(100vh - 112px)`, `overflow-y: auto` na `modal-body`
- `modal-head`: title 17px bold + optional subtitle 12.5px `--ink-faint` + X button
- `modal-foot`: Anuluj (ghost) + spacer + Zapisz (primary)

### Modal 1: Budynek
**Pola** (2-col grid):
| Pole | Typ | Placeholder | Span |
|------|-----|-------------|------|
| Nazwa budynku | text | np. Kamienica Rynek 12 | full |
| Adres | text | ul. Rynek 12, 33-100 Tarnów | full |
| Kod PPE | text.mono | PL0037… | half |
| Taryfa | select | opcje z systemu | half |

### Modal 2: Licznik
**Pola** (2-col grid):
| Pole | Typ | Uwagi |
|------|-----|-------|
| Etykieta lokalu | text | np. U1, M3, B2 |
| Nr seryjny | text.mono | 8-cyfrowy |
| Adres M-Bus | text.mono | hex np. 0x05 |
| Protokół | segmented (M-Bus / Modbus / ręczny) | |
| Przypisany najemca | select | filtrowany po buildingId |
| Taryfa | select | |

### Modal 3: Najemca
**Pola** + dynamiczny hint NIP:
| Pole | Typ | Uwagi |
|------|-----|-------|
| Imię/nazwa firmy | text | pełna szerokość |
| E-mail | email | |
| NIP (opcjonalny) | text.mono | hint pod polem zmienia się live |
| Nr lokalu | text | np. U1, M3 |
| Przypisany licznik | select | filtrowany po buildingId |

**NIP hint logic:**
```jsx
const hasNip = f.nip.trim().length > 0;
// hasNip=true  → "✓ Faktura VAT" kolor --accent-deep (klasa .fhint.vat)
// hasNip=false → "Brak NIP → zostanie wystawiony rachunek" kolor --warn-ink (klasa .fhint.rachunek)
```

### Modal 4: Taryfa (lg = 860px)
**Meta pola** (2-col grid): Nazwa taryfy (full), Grupa taryfowa (select: G11/G12/C11/C12a/B), Obowiązuje od (date), Marża %, btn „Klonuj z istniejącej" (kopiuje składniki z aktywnej taryfy)

**Tabela składników** — identyczna z ekranem Taryfy:  
inline editable rows + „Dodaj składnik" + trash per wiersz

**Footer:** brutto suma live po lewej + „Zapisz taryfę"

---

## Komponenty współdzielone

### `<Sidebar>`
- Szerokość: `232px`, `flex: 0 0 232px`, sticky full-height
- Logo: `logo-mark` (34×34px, border-radius 9px, accent BG, bolt icon), `logo-name` (18px bold), `logo-sub` (11px)
- Nav items: padding 9px 12px, border-radius `--r-sm`, ikona 18px + label 14px weight 500
  - default: color `--sb-ink-soft`
  - hover: `background rgba(125,140,135,.12)`, color `--sb-ink`
  - active: `background --sb-active-bg`, color `--sb-active-ink`, weight 600
- Footer: wersja + status gateway

### `<Topbar>`
- `position: sticky; top: 0; z-index: 5; backdrop-filter: blur(6px)`
- Breadcrumb: 14px, `--ink-soft`; bold część w `--ink`
- Search input: `flex: 1; max-width: 380px; background: --fill-3`
- Alerty button: `.btn.ghost.sm`
- Org chip: user name + avatar (33px circle, accent BG, initials)

### `<Pill status>`
Mapa statusów → klasy CSS → kolory (patrz tabela wyżej w sekcji Faktury + sekcja Liczniki).

### `<Cbx on onClick>`
- 18×18px, border-radius 5px
- unchecked: `border: 1.5px solid --line-strong; background: #fff`
- checked: `background: --accent; border-color: --accent`; biały checkmark SVG (strokeWidth 3)
- Transition: `background .1s, border-color .1s`

### `<Sparkline data w h color>`
SVG sparkline 84×26px. `color="auto"` → zielony gdy trend rosnący, czerwony gdy malejący.  
Zawiera wypełnioną kropkę na ostatnim punkcie.

### `<SparkCell data>`
Sparkline + `▲/▼N%` delta. Kolor zielony/czerwony. Font mono 11.5px weight 600.

### Przyciski `.btn`

| Wariant | Klasy | Styl |
|---------|-------|------|
| Default | `.btn` | border `--line-strong`, bg `--paper`, hover bg `--fill` |
| Primary | `.btn.primary` | bg `--accent`, border `--accent`, kolor white, hover `--accent-deep` |
| Ghost | `.btn.ghost` | border `--line-strong`, bg transparent, kolor `--ink-soft`, hover bg `--fill` |
| Small | `.btn.sm` | padding 6px 11px, font-size 12.5px |
| Disabled | `disabled` attr | opacity 0.4, cursor not-allowed (Tailwind: `disabled:opacity-40 disabled:cursor-not-allowed`) |

### `.filterbar`
`display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 12px --pad; border-bottom: 1px solid --line`

### `.chips` / `.chip`
- Chip default: border `--line-strong`, bg `--paper`, color `--ink-soft`, border-radius `--r-pill`
- Chip `.on`: bg `--accent`, border `--accent`, color `#fff`
- Licznik `.cnt`: `font-variant-numeric: tabular-nums; opacity: .8` (`.on` → 0.95)

---

## Stany interaktywne — podsumowanie

| Element | hover | active/on | disabled | focus |
|---------|-------|-----------|----------|-------|
| Nav item | rgba overlay + ink | sb-active-bg + sb-active-ink | — | — |
| Btn default | bg --fill | — | opacity .4 | ring |
| Btn primary | bg --accent-deep | — | opacity .4 | ring |
| Table row | bg --fill-3 | — | — | — |
| Chip | bg --fill | bg --accent, white | — | — |
| Tab | color --ink | border-bottom --accent, color --accent-deep | — | — |
| `.tin` input | border --line-strong | — | — | border --accent + box-shadow 0 0 0 3px --accent-soft |
| `.fin` input | — | — | — | border --accent + box-shadow 0 0 0 3px --accent-soft |
| `.row-del` | color --danger + bg --danger-soft | — | — | — |
| Cbx | — | bg --accent | — | — |
| Drawer X, Modal X | bg --fill | — | — | — |
| icon-btn | color --accent-deep + border --accent-line + bg --accent-soft | — | — | — |

---

## Responsywność (desktop-first)

Breakpoint: `@media (max-width: 1180px)`

| Element | Desktop (≥1180px) | Mobile (<1180px) |
|---------|-------------------|-----------------|
| StatCards | `grid-template-columns: repeat(4, 1fr)` | `repeat(2, 1fr)` |
| AttentionStrip grid | `repeat(3, 1fr)` | `1fr` (kolumna) |
| BuildingTile grid | `repeat(2, 1fr)` | `1fr` |
| Two-col layout | `1.45fr 1fr` | `1fr` |
| Sidebar | zawsze widoczny, 232px | wymaga hamburger menu (nie zaprojektowany) |

> **Uwaga:** mobilna nawigacja (hamburger/drawer sidebar) nie jest zaprojektowana w tym prototypie. Na breakpoincie <768px UI nie jest zoptymalizowany.

---

## Dane / API shape (z `data.js`)

```typescript
// Budynek
interface Building {
  id: string;          // "b1" .. "b4"
  name: string;
  addr: string;
  meters: number;      // total liczników
  online: number;      // aktywnych
  tenants: number;
  toSend: number;      // faktury gotowe do wysłania
  overdue: number;
  kwh: string;         // "9 420" (formatted)
  ppe: string;         // "PL0037..1204"
}

// Licznik
interface Meter {
  id: string;
  bid: string;         // building id
  building: string;    // short name
  lokal: string;       // "M3 · II p."
  meterName: string;   // "M-Bus 05"
  serial: string;      // "48201577"
  mbus: string;        // "05" (hex address)
  kwh: string;         // "1 234,567" (3 dec, pl-PL)
  when: string;        // "6 min temu"
  status: "ok" | "offline" | "est";
  spark: number[];     // 10 wartości
  tenant: string;      // imię/nazwa
}

// Najemca
interface Tenant {
  id: string;
  bid: string;
  building: string;
  name: string;
  type: "os" | "firma";
  email: string;
  nip: string;         // "" jeśli brak
  lokal: string;       // "M3"
  meter: string;       // "M-Bus 05"
  active: boolean;
  lastInvoice: string; // "FV/041/05/2026"
  paid: boolean;
}

// Faktura
interface Invoice {
  id: string;
  no: string;          // "FV/041/05/2026" lub "— szkic —"
  tenant: string;
  lokal: string;
  kwh: number;
  kwhStr: string;      // "177,0"
  status: "draft" | "ready" | "sent" | "paid" | "overdue";
  due: string;         // "2026-06-14"
  period: string;      // "01–31.05.2026"
  net: number;
  vat: number;
  gross: number;
  lines: InvoiceLine[];
}

// Składnik taryfy → pozycja na fakturze
interface InvoiceLine {
  label: string;
  qty: number;         // kWh albo 1 (stała)
  unit: "kWh" | "mc";
  price: number;       // cena jednostkowa netto
  net: number;         // qty * price
  vat: number;         // 23
}

// Obliczenie faktury
function computeInvoice(kwh: number): { lines, net, vat, gross }
// net = suma lines.net; vat = suma lines.net * 0.23; gross = net + vat
```

---

## Ikony

Używane są minimalne SVG (24×24 viewBox, stroke, nie fill, strokeWidth 1.8):

| Nazwa    | Ścieżka SVG (uproszczona)                    | Użycie                      |
|----------|----------------------------------------------|-----------------------------|
| `grid`   | 4 małe prostokąty 2×2                        | Dashboard nav               |
| `building`| budynek z oknami                            | Budynki nav                 |
| `gauge`  | okrąg + wskazówka                            | Liczniki nav                |
| `users`  | 2 sylwetki                                   | Najemcy nav                 |
| `tag`    | tag / etykieta z kółkiem                     | Taryfy nav                  |
| `doc`    | dokument z linijkami                         | Faktury nav                 |
| `bolt`   | piorun                                       | Logo mark                   |
| `arrow`  | strzałka w prawo                             | CTA send                    |
| `plus`   | krzyżyk +                                    | Add actions                 |
| `x`      | ×                                            | Zamknij modal/drawer        |
| `trash`  | kosz                                         | Usuń wiersz                 |
| `bell`   | dzwonek                                      | Alerty, attention           |
| `check`  | ✓                                            | Zapisz w modal              |

Implementuj jako własne komponenty SVG lub użyj biblioteki (np. Lucide React — ikony `LayoutGrid`, `Building2`, `Gauge`, `Users`, `Tag`, `FileText`, `Zap`, `ArrowRight`, `Plus`, `X`, `Trash2`, `Bell`, `Check`).

---

## Pliki w tym bundle

| Plik | Opis |
|------|------|
| `design_files/EnergyBill Dashboard.html` | Główny prototyp — wszystkie 6 ekranów |
| `design_files/styles.css` | Pełny arkusz CSS z tokenami |
| `design_files/components.jsx` | Sidebar, Topbar, Cbx, Pill, StatCards, ReadingsTable, InvoiceQueue, Sparkline |
| `design_files/layouts.jsx` | Dashboard Layout A (Action) i B (Buildings) |
| `design_files/screens.jsx` | ScreenBudynki, ScreenLiczniki, ScreenNajemcy |
| `design_files/screens2.jsx` | ScreenFaktury, ScreenTaryfy, InvoiceDrawer |
| `design_files/modals.jsx` | ModalBudynek, ModalLicznik, ModalNajemca, ModalTaryfa |
| `design_files/data.js` | Sample data + computeInvoice helper |
| `design_files/app.jsx` | App root, routing state, Tweaks panel |
| `component-map.md` | Mapa komponentów per ekran |

---

## Uruchomienie prototypu

```bash
# Prototyp jest statycznym HTML — wystarczy serwer HTTP
npx serve .
# lub
python3 -m http.server 8080
# → otwórz design_files/EnergyBill Dashboard.html
```
