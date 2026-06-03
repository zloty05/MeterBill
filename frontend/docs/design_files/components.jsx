/* global React */
const { useState } = React;

/* ---------- tiny sketch icons (simple line shapes) ---------- */
function Icon({ name, size = 18 }) {
  const s = { width: size, height: size, fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    grid:     <g><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></g>,
    building: <g><path d="M4 21V5l8-2v18"/><path d="M12 21V9l6 2v10"/><path d="M3 21h18"/><path d="M7 8h1M7 12h1M7 16h1"/></g>,
    gauge:    <g><circle cx="12" cy="13" r="8"/><path d="M12 13l4-3"/><path d="M12 5V3"/></g>,
    users:    <g><circle cx="9" cy="8" r="3.2"/><path d="M3.5 20c0-3.3 2.5-5.5 5.5-5.5s5.5 2.2 5.5 5.5"/><path d="M16 5.2a3 3 0 0 1 0 5.6M21 20c0-2.6-1.4-4.5-3.5-5.2"/></g>,
    tag:      <g><path d="M3 12V5a2 2 0 0 1 2-2h7l8 8-9 9z"/><circle cx="8" cy="8" r="1.4"/></g>,
    doc:      <g><path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5"/><path d="M9 13h7M9 17h7"/></g>,
    bolt:     <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>,
    check:    <path d="M4 12l5 5L20 6"/>,
    arrow:    <path d="M5 12h14M13 6l6 6-6 6"/>,
    bell:     <g><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6"/><path d="M10 20a2 2 0 0 0 4 0"/></g>,
    plus:     <path d="M12 5v14M5 12h14"/>,
    x:        <path d="M6 6l12 12M18 6L6 18"/>,
    trash:    <g><path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M6.5 7l1 13h9l1-13"/></g>,
  };
  return <svg viewBox="0 0 24 24" style={s} className="ico">{paths[name] || null}</svg>;
}

/* ---------- Sidebar ---------- */
function Sidebar({ active, onNav }) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark"><Icon name="bolt" size={18} /></div>
        <div>
          <div className="logo-name">EnergyBill</div>
          <div className="logo-sub">{WF.org.name}</div>
        </div>
      </div>
      {WF.nav.map((n) => (
        <div key={n.id} className={"nav-item" + (active === n.id ? " active" : "")} onClick={() => onNav(n.id)}>
          <Icon name={n.icon} />
          <span>{n.label}</span>
        </div>
      ))}
      <div className="nav-spacer" />
      <div className="sb-foot">v0.1 · plan PRO<br/>Gateway: WAGO PFC300 ✓ online</div>
    </aside>
  );
}

/* ---------- Topbar ---------- */
function Topbar({ title = "Dashboard" }) {
  return (
    <div className="topbar">
      <div className="crumb"><b>{title}</b> · maj 2026</div>
      <div className="search">Szukaj licznika, najemcy, faktury…</div>
      <div className="spacer" />
      <button className="btn ghost sm"><Icon name="bell" size={15} /> Alerty</button>
      <div className="org-chip">
        <span>{WF.org.user}</span>
        <div className="avatar">{WF.org.initials}</div>
      </div>
    </div>
  );
}

/* ---------- Checkbox ---------- */
function Cbx({ on, onClick }) {
  return (
    <div className={"cbx" + (on ? " on" : "")} onClick={onClick} role="checkbox" aria-checked={on}>
      <svg viewBox="0 0 24 24" width="13" height="13" style={{ fill: "none", stroke: "#fff", strokeWidth: 3, strokeLinecap: "round", strokeLinejoin: "round" }}><path d="M4 12l5 5L20 6" /></svg>
    </div>
  );
}

/* ---------- Status pill ---------- */
function Pill({ status }) {
  const map = {
    ok:      ["ok", "online"],
    online:  ["online", "online"],
    offline: ["offline", "offline"],
    est:     ["est", "szacowany"],
    ready:   ["ready", "gotowa"],
    draft:   ["draft", "szkic"],
    sent:    ["sent", "wysłana"],
    paid:    ["paid", "opłacona"],
    overdue: ["overdue", "po terminie"],
  };
  const [cls, label] = map[status] || ["draft", status];
  return <span className={"pill " + cls}><span className="dot" />{label}</span>;
}

/* ---------- Stat cards ---------- */
function StatCards() {
  const s = WF.stats;
  const cards = [
    { tone: "", label: "Aktywne budynki", num: s.buildings, sub: "wszystkie monitorowane", icon: "building" },
    { tone: "accent", label: "Liczniki online", num: s.metersOnline, sub: "M-Bus · odczyt co 15 min", icon: "gauge" },
    { tone: "", label: "Faktury do wysłania", num: s.invoicesToSend, sub: "okres maj 2026", icon: "doc" },
    { tone: "danger", label: "Zaległe płatności", num: s.overdue, sub: "po terminie 14 dni", icon: "bell" },
  ];
  return (
    <div className="stat-row">
      {cards.map((c, i) => (
        <div key={i} className={"stat sketch " + (i % 2 ? "sketch-2 " : "") + c.tone}>
          <div className="corner"><Icon name={c.icon} size={20} /></div>
          <div className="label">{c.label}</div>
          <div className="num">{c.num}</div>
          <div className="sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

/* ---------- Readings table ---------- */
function ReadingsTable({ rows, title = "Ostatnie odczyty", limit }) {
  const data = limit ? rows.slice(0, limit) : rows;
  return (
    <div className="card sketch">
      <div className="card-head">
        <h3>{title}</h3>
        <span className="cell-sub">aktualizacja na żywo z gateway</span>
        <div className="spacer" />
        <button className="btn sm ghost">Wszystkie liczniki <Icon name="arrow" size={14} /></button>
      </div>
      <div className="card-body" style={{ paddingTop: 0 }}>
        <table className="wf">
          <thead>
            <tr><th>Licznik</th><th>Lokal</th><th style={{ textAlign: "right" }}>Ostatni odczyt</th><th>Kiedy</th><th>Status</th></tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr key={i}>
                <td><div className="cell-strong">{r.meter}</div><div className="mono">SN {r.serial} · {r.bld}</div></td>
                <td>{r.lokal}</td>
                <td className="num-cell" style={{ textAlign: "right" }}>{r.kwh} <span className="cell-sub">kWh</span></td>
                <td className="cell-sub">{r.when}</td>
                <td><Pill status={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------- Invoice queue (bulk) ---------- */
function InvoiceQueue({ rows, more = 0 }) {
  const [sel, setSel] = useState(() => new Set(rows.map((_, i) => i)));
  const allOn = sel.size === rows.length;
  const toggle = (i) => { const n = new Set(sel); n.has(i) ? n.delete(i) : n.add(i); setSel(n); };
  const toggleAll = () => setSel(allOn ? new Set() : new Set(rows.map((_, i) => i)));
  const readyCount = rows.filter((r, i) => sel.has(i) && r.status === "ready").length;
  const draftCount = rows.filter((r, i) => sel.has(i) && r.status === "draft").length;

  return (
    <div className="card sketch sketch-2">
      <div className="card-head">
        <h3>Faktury do wysłania w tym miesiącu</h3>
        <div className="spacer" />
        <button className="btn sm ghost"><Icon name="plus" size={14} /> Generuj wszystkie</button>
      </div>
      <div className="bulk-bar">
        <Cbx on={allOn} onClick={toggleAll} />
        <span>Zaznaczono <b>{sel.size}</b> z {rows.length}{more ? ` (+${more} dalszych)` : ""}</span>
        <div className="spacer" />
        {draftCount > 0 && <button className="btn sm">Generuj ({draftCount})</button>}
        <button className="btn primary sm"><Icon name="arrow" size={14} /> Wyślij zaznaczone ({readyCount})</button>
      </div>
      <div className="card-body" style={{ paddingTop: 0 }}>
        <table className="wf">
          <thead>
            <tr><th style={{ width: 28 }}></th><th>Najemca</th><th>Lokal</th><th style={{ textAlign: "right" }}>Zużycie</th><th style={{ textAlign: "right" }}>Brutto</th><th>Nr / status</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td><Cbx on={sel.has(i)} onClick={() => toggle(i)} /></td>
                <td className="cell-strong">{r.tenant}</td>
                <td className="cell-sub" style={{ fontSize: 13 }}>{r.lokal}</td>
                <td className="num-cell" style={{ textAlign: "right" }}>{r.kwhStr || r.kwh} <span className="cell-sub">kWh</span></td>
                <td className="num-cell" style={{ textAlign: "right" }}>{typeof r.gross === "number" ? WF.money(r.gross) : r.gross} zł</td>
                <td><div className="mono">{r.no}</div><Pill status={r.status} /></td>
                <td style={{ textAlign: "right" }}>
                  {r.status === "draft"
                    ? <button className="btn sm">Generuj</button>
                    : <button className="btn primary sm">Wyślij</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {more > 0 && <div style={{ textAlign: "center", padding: "12px 0 2px" }}><button className="btn sm ghost">Pokaż {more} pozostałych faktur</button></div>}
      </div>
    </div>
  );
}

/* ---------- Sparkline ---------- */
function Sparkline({ data, w = 84, h = 26, color = "var(--accent)" }) {
  if (!data || !data.length) return null;
  const min = Math.min(...data), max = Math.max(...data), span = max - min || 1;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * (w - 4) + 2, h - 3 - ((v - min) / span) * (h - 6)]);
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const last = pts[pts.length - 1];
  const up = data[data.length - 1] >= data[0];
  const stroke = color === "auto" ? (up ? "var(--accent)" : "var(--danger)") : color;
  return (
    <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
      <path d={d} fill="none" stroke={stroke} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={last[0]} cy={last[1]} r="2.4" fill={stroke} />
    </svg>
  );
}

Object.assign(window, { Icon, Sidebar, Topbar, Cbx, Pill, StatCards, ReadingsTable, InvoiceQueue, Sparkline });
