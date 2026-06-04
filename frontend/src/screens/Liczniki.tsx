import { useMemo, useState } from "react";
import { listBuildings, listMeters } from "../api/endpoints";
import type { MeterOut } from "../api/types";
import { ModalLicznik } from "../components/modals/ModalLicznik";
import { Icon } from "../components/shared/Icon";
import { useAsync } from "../lib/useAsync";

export function Liczniki() {
  const [bid, setBid] = useState<string>("all");
  const [modal, setModal] = useState<{ open: boolean; data: MeterOut | null }>({
    open: false,
    data: null,
  });

  const data = useAsync(() => Promise.all([listBuildings(), listMeters()]), []);

  const buildings = data.data?.[0] ?? [];
  const meters = data.data?.[1] ?? [];

  const buildingName = useMemo(() => {
    const m = new Map<string, string>();
    for (const b of buildings) m.set(b.id, b.name);
    return m;
  }, [buildings]);

  const rows = bid === "all" ? meters : meters.filter((m) => m.building_id === bid);

  return (
    <div className="content">
      <div className="page-h" style={{ alignItems: "center" }}>
        Liczniki <small>· {rows.length} podliczników</small>
        <span style={{ flex: 1 }} />
        <button
          className="btn primary"
          type="button"
          disabled={!data.data || buildings.length === 0}
          title={buildings.length === 0 ? "Najpierw dodaj budynek" : undefined}
          onClick={() => setModal({ open: true, data: null })}
        >
          <Icon name="plus" size={15} /> Dodaj licznik
        </button>
      </div>

      <div className="card sketch" style={{ padding: 0 }}>
        <div className="filterbar">
          <span className="lbl">Budynek:</span>
          <select className="sel" value={bid} onChange={(e) => setBid(e.target.value)}>
            <option value="all">Wszystkie budynki ({meters.length})</option>
            {buildings.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({meters.filter((m) => m.building_id === b.id).length})
              </option>
            ))}
          </select>
        </div>

        {data.error ? (
          <div className="empty-hint">Nie udało się wczytać liczników: {data.error}</div>
        ) : data.loading || !data.data ? (
          <div className="empty-hint">Wczytywanie…</div>
        ) : rows.length === 0 ? (
          <div className="empty-hint">
            {bid === "all"
              ? "Brak liczników. Wybierz budynek i dodaj pierwszy licznik."
              : "Brak liczników w tym budynku — dodaj pierwszy przyciskiem powyżej."}
          </div>
        ) : (
          <div style={{ padding: "4px var(--pad) var(--pad)" }}>
            <table className="wf">
              <thead>
                <tr>
                  <th>Lokal</th>
                  <th>Budynek</th>
                  <th>Nr seryjny M-Bus</th>
                  <th>Protokół</th>
                  <th>Grupa</th>
                  <th>PPE</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((m) => (
                  <tr key={m.id}>
                    <td className="cell-strong">{m.label || "—"}</td>
                    <td className="cell-sub">{buildingName.get(m.building_id) ?? "—"}</td>
                    <td>
                      <div className="mono">{m.serial_no}</div>
                      <div className="cell-sub">adr {m.mbus_address || "—"}</div>
                    </td>
                    <td className="cell-sub">{m.protocol}</td>
                    <td className="cell-sub">{m.tariff_group}</td>
                    <td className="mono">{m.ppe_code || "—"}</td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn sm ghost"
                        type="button"
                        onClick={() => setModal({ open: true, data: m })}
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

      <ModalLicznik
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
