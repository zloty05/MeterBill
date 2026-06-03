/* global React, Icon, StatCards, ReadingsTable, InvoiceQueue, Pill, Cbx */

/* ---------- Attention strip (Layout A hero) ---------- */
function AttentionStrip() {
  return (
    <div className="attn-wrap">
      <div className="attn-head"><Icon name="bell" size={20} /> Co wymaga uwagi dziś</div>
      <div className="attn-grid">
        {WF.attention.map((a, i) => (
          <div key={i} className={"attn-card sketch-soft " + a.kind}>
            <div className="big">
              <span className="n">{a.count}</span>
              <span className="t">{a.title}</span>
            </div>
            <div className="note">{a.note}</div>
            <div style={{ marginTop: "auto", paddingTop: 6 }}>
              <button className={"btn sm " + (a.kind === "send" ? "primary" : "")}>{a.cta} <Icon name="arrow" size={13} /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===== Layout A: action-oriented ===== */
function LayoutAction() {
  return (
    <div className="content">
      <div className="page-h hand-title">Dzień dobry, M. <small>· 4 budynki · 32 liczniki · maj 2026</small></div>
      <AttentionStrip />
      <StatCards />
      <InvoiceQueue rows={WF.invoices.filter((i) => i.status === "draft" || i.status === "ready")} more={WF.invoicesMore} />
      <ReadingsTable rows={WF.readings} limit={6} />
    </div>
  );
}

/* ---------- Building tile (Layout B) ---------- */
function BuildingTile({ b }) {
  const rows = WF.readings.filter((r) => r.bld === b.name.replace(/^(Kamienica|Biurowiec|Lokale)\s/, "")).slice(0, 3);
  const fallback = WF.readings.filter((r) => b.name.includes(r.bld)).slice(0, 3);
  const reads = (fallback.length ? fallback : rows).slice(0, 3);
  return (
    <div className={"card sketch bld-tile"}>
      <div className="bld-head">
        <div>
          <div className="ttl">{b.name}</div>
          <div className="addr">{b.addr} · taryfa G11</div>
        </div>
        <div className="spacer" />
        {b.overdue > 0 ? <Pill status="draft" /> : <Pill status="ok" />}
      </div>
      <div className="bld-mini">
        <div><div className="m-num green">{b.online}/{b.meters}</div><div className="m-lbl">online</div></div>
        <div><div className="m-num">{b.toSend}</div><div className="m-lbl">do wysłania</div></div>
        <div><div className={"m-num" + (b.overdue ? " red" : "")}>{b.overdue}</div><div className="m-lbl">zaległe</div></div>
        <div><div className="m-num">{b.kwh}</div><div className="m-lbl">kWh / mc</div></div>
      </div>
      <div style={{ padding: "6px 0" }}>
        {reads.map((r, i) => (
          <div key={i} className="bld-readrow">
            <span className="cell-strong" style={{ minWidth: 78 }}>{r.meter}</span>
            <span className="cell-sub">{r.lokal}</span>
            <div className="spacer" />
            <span className="num-cell">{r.kwh} <span className="cell-sub">kWh</span></span>
            <Pill status={r.status} />
          </div>
        ))}
      </div>
      <div className="bld-foot">
        <span className="cell-sub" style={{ fontFamily: "var(--hand)", fontSize: 14, color: "var(--ink-soft)" }}>
          {b.toSend} faktur gotowych
        </span>
        <div className="spacer" />
        <button className="btn sm ghost"><Icon name="plus" size={13} /> Generuj</button>
        <button className="btn sm primary"><Icon name="arrow" size={13} /> Wyślij {b.toSend}</button>
      </div>
    </div>
  );
}

/* ===== Layout B: per-building tiles ===== */
function LayoutBuildings() {
  return (
    <div className="content">
      <div className="page-h hand-title">Budynki <small>· kliknij budynek aby rozwinąć liczniki i najemców</small></div>
      <StatCards />
      <div className="bld-grid">
        {WF.buildings.map((b) => <BuildingTile key={b.id} b={b} />)}
      </div>
    </div>
  );
}

Object.assign(window, { AttentionStrip, LayoutAction, BuildingTile, LayoutBuildings });
