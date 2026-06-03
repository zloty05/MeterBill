/* global React, Icon */
const { useState: useMSt, useEffect: useMEff } = React;

/* ─── ModalShell ─── */
function ModalShell({ open, onClose, title, subtitle, size, children, footer }) {
  return (
    <div
      className={"modal-overlay" + (open ? " open" : "")}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className={"modal" + (size ? " " + size : "")}>
        <div className="modal-head">
          <div>
            <h3>{title}</h3>
            {subtitle && <div className="sub">{subtitle}</div>}
          </div>
          <button className="x" onClick={onClose}><Icon name="x" size={16} /></button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

/* ─── 1. Budynek ─── */
function ModalBudynek({ open, initial, onClose, onSave }) {
  const [f, setF] = useMSt({ name: "", addr: "", ppe: "", tariff: "" });
  useMEff(() => {
    if (open) setF({
      name: initial && initial.name || "",
      addr: initial && initial.addr || "",
      ppe:  initial && initial.ppe  || "",
      tariff: initial && initial.tariff || WF.tariff.name,
    });
  }, [open]);
  const s = (k, v) => setF((p) => ({ ...p, [k]: v }));

  return (
    <ModalShell
      open={open} onClose={onClose}
      title={initial ? "Edytuj budynek" : "Dodaj budynek"}
      subtitle={initial ? initial.name : "Nowy obiekt w systemie"}
      footer={
        <>
          <button className="btn ghost" onClick={onClose}>Anuluj</button>
          <div className="spacer" />
          <button className="btn primary" onClick={() => { onSave(f); onClose(); }}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {initial ? " Zapisz zmiany" : " Dodaj budynek"}
          </button>
        </>
      }
    >
      <div className="form-grid">
        <div className="fr full">
          <label>Nazwa budynku</label>
          <input className="fin" value={f.name} onChange={(e) => s("name", e.target.value)} placeholder="np. Kamienica Rynek 12" />
        </div>
        <div className="fr full">
          <label>Adres</label>
          <input className="fin" value={f.addr} onChange={(e) => s("addr", e.target.value)} placeholder="ul. Rynek 12, 33-100 Tarnów" />
        </div>
        <div className="fr">
          <label>Kod PPE licznika głównego <span className="opt">(opcjonalny)</span></label>
          <input className="fin mono" value={f.ppe} onChange={(e) => s("ppe", e.target.value)} placeholder="PL0037…" />
        </div>
        <div className="fr">
          <label>Przypisana taryfa</label>
          <select className="fin" value={f.tariff} onChange={(e) => s("tariff", e.target.value)}>
            <option value={WF.tariff.name}>{WF.tariff.name}</option>
            <option value="">— bez taryfy —</option>
          </select>
        </div>
      </div>
    </ModalShell>
  );
}

/* ─── 2. Licznik ─── */
const PROTOCOLS = ["M-Bus", "Modbus", "ręczny"];

function ModalLicznik({ open, initial, buildingId, onClose, onSave }) {
  const [f, setF] = useMSt({ lokal: "", serial: "", mbus: "", protocol: "M-Bus", tenant: "", tariff: "" });
  useMEff(() => {
    if (open) setF({
      lokal:    initial && initial.lokal    || "",
      serial:   initial && initial.serial   || "",
      mbus:     initial && initial.mbus     || "",
      protocol: initial && initial.protocol || "M-Bus",
      tenant:   "",
      tariff:   WF.tariff.name,
    });
  }, [open]);
  const s = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const tenantList = buildingId ? WF.tenants.filter((t) => t.bid === buildingId) : WF.tenants;

  return (
    <ModalShell
      open={open} onClose={onClose}
      title={initial ? "Edytuj licznik" : "Dodaj licznik"}
      subtitle={initial ? `${initial.lokal} · SN ${initial.serial}` : "Nowy podlicznik w systemie"}
      footer={
        <>
          <button className="btn ghost" onClick={onClose}>Anuluj</button>
          <div className="spacer" />
          <button className="btn primary" onClick={() => { onSave(f); onClose(); }}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {initial ? " Zapisz zmiany" : " Dodaj licznik"}
          </button>
        </>
      }
    >
      <div className="form-grid">
        <div className="fr">
          <label>Etykieta lokalu</label>
          <input className="fin" value={f.lokal} onChange={(e) => s("lokal", e.target.value)} placeholder="np. U1, M3, B2" />
        </div>
        <div className="fr">
          <label>Nr seryjny</label>
          <input className="fin mono" value={f.serial} onChange={(e) => s("serial", e.target.value)} placeholder="48201577" />
        </div>
        <div className="fr">
          <label>Adres M-Bus <span className="opt">(hex)</span></label>
          <input className="fin mono" value={f.mbus} onChange={(e) => s("mbus", e.target.value)} placeholder="0x05" />
        </div>
        <div className="fr">
          <label>Protokół</label>
          <div className="fseg" style={{ display: "flex", width: "100%" }}>
            {PROTOCOLS.map((p) => (
              <button key={p} className={f.protocol === p ? "on" : ""} onClick={() => s("protocol", p)}>{p}</button>
            ))}
          </div>
        </div>
        <div className="fr">
          <label>Przypisany najemca <span className="opt">(opcjonalny)</span></label>
          <select className="fin" value={f.tenant} onChange={(e) => s("tenant", e.target.value)}>
            <option value="">— brak —</option>
            {tenantList.map((t) => (
              <option key={t.id} value={t.id}>{t.name} · {t.lokal}</option>
            ))}
          </select>
        </div>
        <div className="fr">
          <label>Taryfa</label>
          <select className="fin" value={f.tariff} onChange={(e) => s("tariff", e.target.value)}>
            <option value={WF.tariff.name}>{WF.tariff.name}</option>
            <option value="">— bez taryfy —</option>
          </select>
        </div>
      </div>
    </ModalShell>
  );
}

/* ─── 3. Najemca ─── */
function ModalNajemca({ open, initial, buildingId, onClose, onSave }) {
  const [f, setF] = useMSt({ name: "", email: "", nip: "", lokal: "", meter: "" });
  useMEff(() => {
    if (open) setF({
      name:  initial && initial.name  || "",
      email: initial && initial.email || "",
      nip:   initial && initial.nip   || "",
      lokal: initial && initial.lokal || "",
      meter: "",
    });
  }, [open]);
  const s = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const meterList = buildingId ? WF.meters.filter((m) => m.bid === buildingId) : WF.meters;
  const hasNip = f.nip.trim().length > 0;

  return (
    <ModalShell
      open={open} onClose={onClose}
      title={initial ? "Edytuj najemcę" : "Dodaj najemcę"}
      subtitle={initial ? initial.name : "Nowy najemca w systemie"}
      footer={
        <>
          <button className="btn ghost" onClick={onClose}>Anuluj</button>
          <div className="spacer" />
          <button className="btn primary" onClick={() => { onSave(f); onClose(); }}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {initial ? " Zapisz zmiany" : " Dodaj najemcę"}
          </button>
        </>
      }
    >
      <div className="form-grid">
        <div className="fr full">
          <label>Imię i nazwisko / nazwa firmy</label>
          <input className="fin" value={f.name} onChange={(e) => s("name", e.target.value)} placeholder="np. Jan Kowalski lub Firma XYZ sp. z o.o." />
        </div>
        <div className="fr">
          <label>E-mail</label>
          <input className="fin" type="email" value={f.email} onChange={(e) => s("email", e.target.value)} placeholder="kontakt@email.pl" />
        </div>
        <div className="fr">
          <label>NIP <span className="opt">(opcjonalny)</span></label>
          <input className="fin mono" value={f.nip} onChange={(e) => s("nip", e.target.value)} placeholder="873-000-00-00" />
          <div className={"fhint" + (hasNip ? " vat" : "")}>
            {hasNip ? "✓ Faktura VAT" : "Brak NIP → zostanie wystawiony rachunek"}
          </div>
        </div>
        <div className="fr">
          <label>Nr lokalu</label>
          <input className="fin" value={f.lokal} onChange={(e) => s("lokal", e.target.value)} placeholder="np. U1, M3" />
        </div>
        <div className="fr full">
          <label>Przypisany licznik <span className="opt">(opcjonalny)</span></label>
          <select className="fin" value={f.meter} onChange={(e) => s("meter", e.target.value)}>
            <option value="">— brak —</option>
            {meterList.map((m) => (
              <option key={m.id} value={m.id}>{m.meterName} · {m.lokal} · SN {m.serial}</option>
            ))}
          </select>
        </div>
      </div>
    </ModalShell>
  );
}

/* ─── 4. Taryfa ─── */
const TARIFF_GROUPS = ["G11", "G12", "C11", "C12a", "B"];

function ModalTaryfa({ open, onClose, onSave }) {
  const mkF = () => ({ name: "", group: "G11", validFrom: new Date().toISOString().slice(0, 10), margin: "0" });
  const [f, setF] = useMSt(mkF);
  const [rows, setRows] = useMSt([]);
  const [nid, setNid] = useMSt(0);

  useMEff(() => {
    if (open) { setF(mkF()); setRows([]); setNid(0); }
  }, [open]);

  const s = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const upd = (id, k, v) => setRows((rs) => rs.map((r) => r._id === id ? { ...r, [k]: v } : r));
  const del = (id) => setRows((rs) => rs.filter((r) => r._id !== id));
  const add = () => {
    setRows((rs) => [...rs, { _id: nid, name: "Nowy składnik", type: "per_kwh", price: 0, unit: "zł/kWh", vat: 23 }]);
    setNid((n) => n + 1);
  };
  const clone = () => {
    const cloned = WF.tariff.components.map((c, i) => ({ ...c, _id: nid + i }));
    setRows(cloned);
    setNid((n) => n + cloned.length);
    if (!f.name) s("name", WF.tariff.name + " (kopia)");
  };

  const sumKwh   = rows.filter((r) => r.type === "per_kwh").reduce((a, r) => a + (+r.price || 0), 0);
  const sumFixed = rows.filter((r) => r.type === "monthly_fixed").reduce((a, r) => a + (+r.price || 0), 0);
  const brutto   = (r) => (+r.price || 0) * (1 + (+r.vat || 0) / 100);

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="Dodaj taryfę" subtitle="Nowy cennik składników energii" size="lg"
      footer={
        <>
          <button className="btn ghost" onClick={onClose}>Anuluj</button>
          <div className="spacer" />
          {(sumKwh > 0 || sumFixed > 0) && (
            <span style={{ fontSize: 12, color: "var(--ink-faint)", paddingRight: 10 }}>
              {sumKwh > 0 && <span>{sumKwh.toLocaleString("pl-PL", { minimumFractionDigits: 4 })} zł/kWh</span>}
              {sumKwh > 0 && sumFixed > 0 && <span> · </span>}
              {sumFixed > 0 && <span>{sumFixed.toLocaleString("pl-PL", { minimumFractionDigits: 2 })} zł/mc</span>}
            </span>
          )}
          <button className="btn primary" onClick={() => { onSave({ ...f, components: rows }); onClose(); }}>
            <Icon name="check" size={15} /> Zapisz taryfę
          </button>
        </>
      }
    >
      {/* ── Meta fields ── */}
      <div className="form-grid">
        <div className="fr full">
          <label>Nazwa taryfy</label>
          <input className="fin" value={f.name} onChange={(e) => s("name", e.target.value)} placeholder='np. G12 – ZAEL 2026' />
        </div>
        <div className="fr">
          <label>Grupa taryfowa</label>
          <select className="fin" value={f.group} onChange={(e) => s("group", e.target.value)}>
            {TARIFF_GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <div className="fr">
          <label>Obowiązuje od</label>
          <input className="fin" type="date" value={f.validFrom} onChange={(e) => s("validFrom", e.target.value)} />
        </div>
        <div className="fr">
          <label>Marża zarządcy %</label>
          <input className="fin mono" type="number" min="0" max="100" step="0.1" value={f.margin} onChange={(e) => s("margin", e.target.value)} />
        </div>
        <div className="fr" style={{ justifyContent: "flex-end" }}>
          <label style={{ visibility: "hidden" }}>·</label>
          <button className="btn" style={{ width: "100%" }} onClick={clone}>
            <Icon name="doc" size={15} /> Klonuj z istniejącej
          </button>
        </div>
      </div>

      {/* ── Składniki ── */}
      <div style={{ margin: "16px 0 8px", paddingTop: 14, borderTop: "1px solid var(--line)" }}>
        <div className="form-sec">Składniki cennika</div>
      </div>
      <table className="wf">
        <thead>
          <tr>
            <th style={{ width: "34%" }}>Nazwa składnika</th>
            <th>Typ</th>
            <th style={{ textAlign: "right" }}>Cena netto</th>
            <th style={{ textAlign: "right", width: 80 }}>VAT %</th>
            <th style={{ textAlign: "right" }}>Cena brutto</th>
            <th style={{ width: 34 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r._id}>
              <td><input className="tin txt" value={r.name} onChange={(e) => upd(r._id, "name", e.target.value)} /></td>
              <td>
                <select className="tin sel" value={r.type} onChange={(e) => upd(r._id, "type", e.target.value)}>
                  <option value="per_kwh">za kWh</option>
                  <option value="monthly_fixed">stała / mc</option>
                </select>
              </td>
              <td style={{ textAlign: "right" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
                  <input className="tin" style={{ maxWidth: 96 }} value={r.price} onChange={(e) => upd(r._id, "price", e.target.value)} />
                  <span className="cell-sub" style={{ minWidth: 46 }}>{r.type === "per_kwh" ? "zł/kWh" : "zł/mc"}</span>
                </div>
              </td>
              <td style={{ textAlign: "right" }}><input className="tin" style={{ maxWidth: 56 }} value={r.vat} onChange={(e) => upd(r._id, "vat", e.target.value)} /></td>
              <td className="num-cell" style={{ textAlign: "right" }}>
                {brutto(r).toLocaleString("pl-PL", { minimumFractionDigits: r.type === "per_kwh" ? 4 : 2 })}
              </td>
              <td style={{ textAlign: "center" }}>
                <button className="row-del" onClick={() => del(r._id)} title="Usuń"><Icon name="trash" size={15} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <div className="empty-hint" style={{ padding: "16px 0 4px" }}>
          Brak składników — dodaj ręcznie lub kliknij „Klonuj z istniejącej".
        </div>
      )}
      <div style={{ padding: "10px 0 0" }}>
        <button className="btn" onClick={add}><Icon name="plus" size={15} /> Dodaj składnik</button>
      </div>
    </ModalShell>
  );
}

Object.assign(window, { ModalBudynek, ModalLicznik, ModalNajemca, ModalTaryfa });
