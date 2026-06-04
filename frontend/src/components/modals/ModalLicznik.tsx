import { useEffect, useState } from "react";
import { ApiError } from "../../api/client";
import { createMeter, updateMeter } from "../../api/endpoints";
import type { BuildingOut, MeterOut, MeterProtocol } from "../../api/types";
import { Icon } from "../shared/Icon";
import { ModalShell } from "./ModalShell";

// Protokoły: etykieta UI → wartość kontraktu backendu (MeterProtocol).
const PROTOCOLS: { label: string; value: MeterProtocol }[] = [
  { label: "M-Bus", value: "mbus" },
  { label: "Modbus", value: "modbus" },
  { label: "ręczny", value: "manual" },
];

// Modal Licznik podpięty do API (POST/PATCH /meters).
// Pola mapowane na kontrakt: lokal→label, serial→serial_no, mbus→mbus_address.
// Przy TWORZENIU budynek wybierany jest w modalu (select); przy EDYCJI budynku
// nie zmieniamy (PATCH /meters go nie obsługuje). `defaultBuildingId` wstępnie
// ustawia select (np. gdy dodajemy z poziomu szczegółów budynku albo filtra).
export function ModalLicznik({
  open,
  initial,
  buildings,
  defaultBuildingId,
  onClose,
  onSaved,
}: {
  open: boolean;
  initial: MeterOut | null;
  buildings: BuildingOut[];
  defaultBuildingId: string | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [buildingId, setBuildingId] = useState("");
  const [label, setLabel] = useState("");
  const [serial, setSerial] = useState("");
  const [mbus, setMbus] = useState("");
  const [protocol, setProtocol] = useState<MeterProtocol>("mbus");
  const [tariffGroup, setTariffGroup] = useState("G11");
  const [ppe, setPpe] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      // przy edycji budynek z licznika; przy tworzeniu — domyślny lub pusty
      setBuildingId(initial?.building_id ?? defaultBuildingId ?? "");
      setLabel(initial?.label ?? "");
      setSerial(initial?.serial_no ?? "");
      setMbus(initial?.mbus_address ?? "");
      setProtocol(initial?.protocol ?? "mbus");
      setTariffGroup(initial?.tariff_group ?? "G11");
      setPpe(initial?.ppe_code ?? "");
      setError(null);
    }
  }, [open, initial, defaultBuildingId]);

  async function save() {
    setError(null);
    if (!serial.trim()) {
      setError("Nr seryjny jest wymagany.");
      return;
    }
    if (!initial && !buildingId) {
      setError("Wybierz budynek, do którego należy licznik.");
      return;
    }
    setBusy(true);
    try {
      const common = {
        serial_no: serial.trim(),
        mbus_address: mbus.trim() || null,
        protocol,
        tariff_group: tariffGroup.trim() || "G11",
        ppe_code: ppe.trim() || null,
        label: label.trim() || null,
      };
      if (initial) {
        await updateMeter(initial.id, common);
      } else {
        await createMeter({ building_id: buildingId as string, ...common });
      }
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Nie udało się zapisać licznika.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ModalShell
      open={open}
      onClose={onClose}
      title={initial ? "Edytuj licznik" : "Dodaj licznik"}
      subtitle={initial ? `${initial.label || "—"} · SN ${initial.serial_no}` : "Nowy podlicznik w systemie"}
      footer={
        <>
          <button className="btn ghost" type="button" onClick={onClose} disabled={busy}>
            Anuluj
          </button>
          <div className="spacer" />
          <button className="btn primary" type="button" onClick={save} disabled={busy}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {busy ? " Zapisywanie…" : initial ? " Zapisz zmiany" : " Dodaj licznik"}
          </button>
        </>
      }
    >
      {error && (
        <div className="login-err" style={{ marginBottom: 14 }}>
          {error}
        </div>
      )}
      <div className="form-grid">
        {initial ? (
          <div className="fr full">
            <label>Budynek</label>
            <input
              className="fin"
              value={buildings.find((b) => b.id === initial.building_id)?.name ?? "—"}
              disabled
            />
          </div>
        ) : (
          <div className="fr full">
            <label>Budynek</label>
            <select
              className="fin"
              value={buildingId}
              onChange={(e) => setBuildingId(e.target.value)}
            >
              <option value="">— wybierz budynek —</option>
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="fr">
          <label>
            Etykieta lokalu <span className="opt">(opcjonalna)</span>
          </label>
          <input
            className="fin"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="np. U1, M3, B2"
          />
        </div>
        <div className="fr">
          <label>Nr seryjny</label>
          <input
            className="fin mono"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            placeholder="48201577"
          />
        </div>
        <div className="fr">
          <label>
            Adres M-Bus <span className="opt">(hex)</span>
          </label>
          <input
            className="fin mono"
            value={mbus}
            onChange={(e) => setMbus(e.target.value)}
            placeholder="05"
          />
        </div>
        <div className="fr">
          <label>Protokół</label>
          <div className="fseg" style={{ display: "flex", width: "100%" }}>
            {PROTOCOLS.map((p) => (
              <button
                key={p.value}
                type="button"
                className={protocol === p.value ? "on" : ""}
                onClick={() => setProtocol(p.value)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="fr">
          <label>Grupa taryfowa</label>
          <input
            className="fin"
            value={tariffGroup}
            onChange={(e) => setTariffGroup(e.target.value)}
            placeholder="G11"
          />
        </div>
        <div className="fr">
          <label>
            Kod PPE <span className="opt">(opcjonalny)</span>
          </label>
          <input
            className="fin mono"
            value={ppe}
            onChange={(e) => setPpe(e.target.value)}
            placeholder="PL0037…"
          />
        </div>
      </div>
    </ModalShell>
  );
}
