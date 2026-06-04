import { useEffect, useState } from "react";
import { createBuilding, updateBuilding } from "../../api/endpoints";
import type { BuildingOut } from "../../api/types";
import { ApiError } from "../../api/client";
import { Icon } from "../shared/Icon";
import { ModalShell } from "./ModalShell";

// Modal Budynek podpięty do API (POST/PATCH /buildings).
// Pola mapowane na kontrakt backendu: addr→address, ppe→main_meter_ppe.
// (Taryfa z mockupu pominięta — BuildingCreate jej nie przyjmuje.)
export function ModalBudynek({
  open,
  initial,
  onClose,
  onSaved,
}: {
  open: boolean;
  initial: BuildingOut | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [ppe, setPpe] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(initial?.name ?? "");
      setAddress(initial?.address ?? "");
      setPpe(initial?.main_meter_ppe ?? "");
      setError(null);
    }
  }, [open, initial]);

  async function save() {
    setError(null);
    if (!name.trim() || !address.trim()) {
      setError("Nazwa i adres są wymagane.");
      return;
    }
    setBusy(true);
    try {
      const body = {
        name: name.trim(),
        address: address.trim(),
        main_meter_ppe: ppe.trim() || null,
      };
      if (initial) await updateBuilding(initial.id, body);
      else await createBuilding(body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Nie udało się zapisać budynku.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ModalShell
      open={open}
      onClose={onClose}
      title={initial ? "Edytuj budynek" : "Dodaj budynek"}
      subtitle={initial ? initial.name : "Nowy obiekt w systemie"}
      footer={
        <>
          <button className="btn ghost" type="button" onClick={onClose} disabled={busy}>
            Anuluj
          </button>
          <div className="spacer" />
          <button className="btn primary" type="button" onClick={save} disabled={busy}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {busy ? " Zapisywanie…" : initial ? " Zapisz zmiany" : " Dodaj budynek"}
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
        <div className="fr full">
          <label>Nazwa budynku</label>
          <input
            className="fin"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="np. Kamienica Rynek 12"
          />
        </div>
        <div className="fr full">
          <label>Adres</label>
          <input
            className="fin"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="ul. Rynek 12, 33-100 Tarnów"
          />
        </div>
        <div className="fr full">
          <label>
            Kod PPE licznika głównego <span className="opt">(opcjonalny)</span>
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
