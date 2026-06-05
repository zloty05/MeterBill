import { useMemo, useState } from "react";
import { listBuildings, listTenants } from "../api/endpoints";
import type { TenantOut } from "../api/types";
import { ModalNajemca } from "../components/modals/ModalNajemca";
import { Icon } from "../components/shared/Icon";
import { Pill } from "../components/shared/Pill";
import { useAsync } from "../lib/useAsync";

export function Najemcy() {
  const [bid, setBid] = useState<string>("all");
  const [modal, setModal] = useState<{ open: boolean; data: TenantOut | null }>({
    open: false,
    data: null,
  });

  const data = useAsync(() => Promise.all([listBuildings(), listTenants()]), []);

  const buildings = data.data?.[0] ?? [];
  const tenants = data.data?.[1] ?? [];

  const buildingName = useMemo(() => {
    const m = new Map<string, string>();
    for (const b of buildings) m.set(b.id, b.name);
    return m;
  }, [buildings]);

  const rows = bid === "all" ? tenants : tenants.filter((t) => t.building_id === bid);

  return (
    <div className="content">
      <div className="page-h" style={{ alignItems: "center" }}>
        Najemcy <small>· {rows.length} najemców</small>
        <span style={{ flex: 1 }} />
        <button
          className="btn primary"
          type="button"
          disabled={!data.data || buildings.length === 0}
          title={buildings.length === 0 ? "Najpierw dodaj budynek" : undefined}
          onClick={() => setModal({ open: true, data: null })}
        >
          <Icon name="plus" size={15} /> Dodaj najemcę
        </button>
      </div>

      <div className="card sketch" style={{ padding: 0 }}>
        <div className="filterbar">
          <span className="lbl">Budynek:</span>
          <select className="sel" value={bid} onChange={(e) => setBid(e.target.value)}>
            <option value="all">Wszystkie budynki ({tenants.length})</option>
            {buildings.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({tenants.filter((t) => t.building_id === b.id).length})
              </option>
            ))}
          </select>
        </div>

        {data.error ? (
          <div className="empty-hint">Nie udało się wczytać najemców: {data.error}</div>
        ) : data.loading || !data.data ? (
          <div className="empty-hint">Wczytywanie…</div>
        ) : rows.length === 0 ? (
          <div className="empty-hint">
            {bid === "all"
              ? "Brak najemców. Dodaj pierwszego przyciskiem powyżej."
              : "Brak najemców w tym budynku."}
          </div>
        ) : (
          <div style={{ padding: "4px var(--pad) var(--pad)" }}>
            <table className="wf">
              <thead>
                <tr>
                  <th>Najemca</th>
                  <th>Budynek / lokal</th>
                  <th>Typ</th>
                  <th>E-mail</th>
                  <th>NIP</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id}>
                    <td className="cell-strong">{t.name}</td>
                    <td className="cell-sub">
                      {buildingName.get(t.building_id) ?? "—"} · {t.unit_no}
                    </td>
                    <td>
                      <span className="pill draft">
                        <span className="dot" />
                        {t.nip ? "firma · VAT" : "os. fizyczna"}
                      </span>
                    </td>
                    <td className="cell-sub">{t.email}</td>
                    <td className="mono">{t.nip || "—"}</td>
                    <td>
                      <Pill status={t.active ? "online" : "offline"} />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn sm ghost"
                        type="button"
                        onClick={() => setModal({ open: true, data: t })}
                      >
                        Edytuj
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ModalNajemca
        open={modal.open}
        initial={modal.data}
        buildings={buildings}
        defaultBuildingId={bid !== "all" ? bid : null}
        onClose={() => setModal({ open: false, data: null })}
        onSaved={data.reload}
      />
    </div>
  );
}
