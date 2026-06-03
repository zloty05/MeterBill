# EnergyBill — Mapa komponentów per ekran

Legenda:
- `[shared]` — komponent współdzielony, implementuj raz
- `[modal]` — dialog nakładkowy
- `[state]` — lokalny stan React
- `[prop]` — przyjmuje dane przez props

---

## Shell (każdy ekran)

```
<App>                              [state: screen, tweaks]
├── <Sidebar active onNav>         [shared] 232px sticky
│   ├── LogoMark                   bolt icon, accent bg
│   ├── NavItem × 6                grid/building/gauge/users/tag/doc
│   └── SidebarFooter              version + gateway status
├── <Topbar title>                 [shared] sticky blur backdrop
│   ├── Breadcrumb                 title + period
│   ├── SearchInput                max-width 380px
│   ├── AlertButton                btn ghost sm
│   └── OrgChip                    name + avatar
└── <ScreenContent>                scrollable flex col gap --gap
```

---

## 1. Dashboard

```
<Dashboard>                        [state: layout ("action"|"buildings")]
├── LayoutSwitch                   .seg segmented control (2 options)
│
├── [A] <LayoutAction>
│   ├── PageHeading                "Dzień dobry, M."
│   ├── <AttentionStrip>           3 action cards
│   │   ├── AttentionCard.send     btn.primary.sm
│   │   ├── AttentionCard.overdue  btn.sm
│   │   └── AttentionCard.estimate btn.sm
│   ├── <StatCards>                grid 4×1fr
│   │   ├── StatCard (buildings)
│   │   ├── StatCard.accent (meters online)
│   │   ├── StatCard (invoices to send)
│   │   └── StatCard.danger (overdue)
│   ├── <InvoiceQueue rows more>   [state: sel Set<idx>]
│   │   ├── CardHead + btn "Generuj wszystkie"
│   │   ├── BulkBar                Cbx + counter + Generuj + Wyślij
│   │   └── table.wf               Cbx | Najemca | Lokal | kWh | Brutto | Nr/status | action
│   └── <ReadingsTable rows limit=6>
│       ├── CardHead + btn "Wszystkie liczniki"
│       └── table.wf               Licznik | Lokal | Odczyt | Kiedy | Status
│
└── [B] <LayoutBuildings>
    ├── PageHeading                "Budynki"
    ├── <StatCards>                (identyczne)
    └── .bld-grid (2 cols)
        └── <BuildingTile b> × 4   [prop: Building]
            ├── BldHead            name + addr + Pill
            ├── BldMini            4 stats (online, toSend, overdue, kWh)
            ├── ReadingRows × 3    bld-readrow
            └── BldFoot            "N faktur gotowych" + Generuj + Wyślij N
```

---

## 2. Budynki

```
<ScreenBudynki>                    [state: sel, tab, bModal, mModal, nModal]
│
├── [LIST VIEW — sel=null]
│   ├── PageHeading + btn.primary "Dodaj budynek"
│   └── card.sketch
│       └── table.wf (clickrow)
│           └── tr × 4             name+addr+ppe | pill G11 | meters | tenants | toSend | overdue | Edytuj+chevron
│
└── [DETAIL VIEW — sel=buildingId]
    ├── Backlink "← Wszystkie budynki"  + btn.ghost "Edytuj budynek"
    ├── PageHeading                name + addr
    └── card.sketch
        ├── <MetaStrip>            6 pól: Taryfa, PPE, Online, Najemcy, Do wysłania, kWh
        ├── <Tabs active=tab>      Liczniki(N) | Najemcy(N) | Historia  + "Dodaj..." btn
        │
        ├── [tab=liczniki]
        │   └── table.wf
        │       └── tr             Lokal | Licznik/SN | Odczyt | Kiedy | Status | SparkCell | Edytuj
        │
        ├── [tab=najemcy]
        │   └── table.wf
        │       └── tr             Lokal | Najemca | Typ pill | Email | NIP | Licznik | Status | Edytuj
        │
        └── [tab=historia]
            └── .tl (timeline)
                └── TlItem × N    dot(green/gray/red) | event + detail | timestamp

[modals]
├── <ModalBudynek open initial onClose onSave>   [state: form fields]
├── <ModalLicznik open initial buildingId ...>   [state: form fields]
└── <ModalNajemca open initial buildingId ...>   [state: form fields]
```

---

## 3. Liczniki

```
<ScreenLiczniki>                   [state: bid="all", mModal]
├── PageHeading + btn.primary "Dodaj licznik"
└── card.sketch
    ├── <FilterBar>
    │   ├── BuildingSelect         "all" + buildings options
    │   └── StatusPills            pill.online N + pill.offline N
    └── table.wf
        └── tr × 32               Lokal | Budynek | Serial/mbus | kWh | Kiedy | Pill | SparkCell | Edytuj

[modal]
└── <ModalLicznik open initial buildingId ...>
```

---

## 4. Najemcy

```
<ScreenNajemcy>                    [state: bid="all", nModal]
├── PageHeading + btn.primary "Dodaj najemcę"
└── card.sketch
    ├── <FilterBar>
    │   └── BuildingSelect
    └── table.wf
        └── tr × N                 Najemca | Budynek·lokal | Typ pill | Email | Ostatnia FV | Płatność | Edytuj

[modal]
└── <ModalNajemca open initial buildingId ...>
```

---

## 5. Taryfy

```
<ScreenTaryfy>                     [state: rows[], nextId, tModal]
├── PageHeading
└── card.sketch
    ├── CardHead                   nazwa + pill.ok "aktywna" + btn.primary "Dodaj taryfę" + btn.ghost "Źródło"
    ├── <MetaStrip>                6 pól + sumy obliczane live
    └── EditableTable              [state: rows[]]
        ├── thead                  Nazwa | Typ | Cena netto | VAT% | Cena brutto | del
        └── tbody
            └── EditableRow × N    [state: per-row via upd()]
                ├── input.tin.txt  nazwa
                ├── select.tin.sel typ (per_kwh / monthly_fixed)
                ├── input.tin      cena + unit label
                ├── input.tin      VAT%
                ├── NumCell        brutto (read-only, computed)
                └── RowDelBtn      trash → del(id)
        + btn "Dodaj składnik"

[modal]
└── <ModalTaryfa open onClose onSave>   size="lg" (860px)
    ├── MetaGrid                   Nazwa(full) | Grupa | Od | Marża | Klonuj
    └── EditableTable              (identyczna struktura jak wyżej)
```

---

## 6. Faktury

```
<ScreenFaktury>                    [state: filter="all", sel Set<id>, open=null|Invoice]
├── PageHeading
└── card.sketch
    ├── <FilterBar>
    │   └── ChipGroup              Wszystkie | Szkice | Gotowe | Wysłane | Opłacone | Po terminie
    ├── <BulkBar>                  [computed: allOn, draftSel, readySel]
    │   ├── Cbx (select-all)       zakres = bieżący filtr
    │   ├── Counter "Zaznaczono N" zakres = wszystkie statusy
    │   ├── btn "Generuj (N)"      disabled gdy draftSel===0
    │   └── btn.primary "Wyślij (N)" disabled gdy readySel===0
    └── table.wf (clickrow → drawer)
        └── tr × N
            ├── td (stopPropagation): Cbx
            ├── mono: nr faktury
            ├── cell-strong: najemca
            ├── cell-sub: lokal
            ├── cell-sub: okres
            ├── num-cell right: kWh
            ├── num-cell right: brutto zł
            ├── Pill status
            └── cell-sub: termin

<InvoiceDrawer inv onClose>        [shared, fixed panel]
├── Overlay                        fade in/out
└── Drawer                         slide in/out 480px
    ├── DrawerHead                 nr (mono) + najemca (18px bold) + Pill + X
    ├── DrawerBody (overflow-y: auto)
    │   ├── PartyGrid              Sprzedawca | Nabywca
    │   ├── KVList                 Okres | Zużycie | Termin
    │   ├── table.wf               Pozycja | Ilość | Cena | Netto
    │   ├── SumRows                netto / VAT / brutto (total 17px bold)
    │   └── PaymentBox             "Do zapłaty" accent-soft bg
    └── DrawerFoot
        ├── btn.ghost "Podgląd PDF"
        └── btn.primary            "Generuj fakturę" (draft) | "Wyślij e-mailem" (ready/sent)
```

---

## Komponenty atomowe (shared)

| Komponent | Props | Plik źródłowy |
|-----------|-------|---------------|
| `Icon` | `name, size=18` | components.jsx |
| `Pill` | `status` | components.jsx |
| `Cbx` | `on, onClick` | components.jsx |
| `Sparkline` | `data, w, h, color` | components.jsx |
| `SparkCell` | `data` | screens.jsx |
| `StatCards` | — (dane z WF) | components.jsx |
| `ReadingsTable` | `rows, title, limit` | components.jsx |
| `InvoiceQueue` | `rows, more` | components.jsx |

## Modale (shared)

| Komponent | Props | Plik źródłowy |
|-----------|-------|---------------|
| `ModalShell` | `open, onClose, title, subtitle, size, children, footer` | modals.jsx |
| `ModalBudynek` | `open, initial, onClose, onSave` | modals.jsx |
| `ModalLicznik` | `open, initial, buildingId, onClose, onSave` | modals.jsx |
| `ModalNajemca` | `open, initial, buildingId, onClose, onSave` | modals.jsx |
| `ModalTaryfa` | `open, onClose, onSave` | modals.jsx |

---

## Zalecana struktura katalogów (React + Vite)

```
src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Topbar.tsx
│   │   └── AppShell.tsx
│   ├── shared/
│   │   ├── Icon.tsx
│   │   ├── Pill.tsx
│   │   ├── Cbx.tsx
│   │   ├── Sparkline.tsx
│   │   ├── SparkCell.tsx
│   │   ├── StatCards.tsx
│   │   ├── ReadingsTable.tsx
│   │   └── InvoiceQueue.tsx
│   ├── modals/
│   │   ├── ModalShell.tsx
│   │   ├── ModalBudynek.tsx
│   │   ├── ModalLicznik.tsx
│   │   ├── ModalNajemca.tsx
│   │   └── ModalTaryfa.tsx
│   └── dashboard/
│       ├── AttentionStrip.tsx
│       ├── BuildingTile.tsx
│       ├── LayoutAction.tsx
│       └── LayoutBuildings.tsx
├── screens/
│   ├── Dashboard.tsx
│   ├── Budynki.tsx
│   ├── Liczniki.tsx
│   ├── Najemcy.tsx
│   ├── Taryfy.tsx
│   └── Faktury.tsx
│       └── InvoiceDrawer.tsx
├── types/
│   └── index.ts        (Building, Meter, Tenant, Invoice, etc.)
├── data/
│   └── sample.ts       (port z data.js)
└── styles/
    └── tokens.css      (port z styles.css :root)
```
