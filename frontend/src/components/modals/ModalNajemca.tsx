import { useEffect, useState } from "react";
import { ApiError } from "../../api/client";
import { createTenant, updateTenant } from "../../api/endpoints";
import type { BuildingOut, TenantOut } from "../../api/types";
import { Icon } from "../shared/Icon";
import { ModalShell } from "./ModalShell";

// Modal Najemca podpięty do API (POST/PATCH /tenants).
// Pole "Nr lokalu" → unit_no. Dynamiczny hint NIP: z NIP → faktura VAT,
// bez NIP → rachunek (port z mockupu). Budynek wybierany w modalu przy
// tworzeniu; przy edycji read-only (PATCH /tenants budynku nie zmienia).
export function ModalNajemca({
  open,
  initial,
  buildings,
  defaultBuildingId,
  onClose,
  onSaved,
}: {
  open: boolean;
  initial: TenantOut | null;
  buildings: BuildingOut[];
  defaultBuildingId: string | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [buildingId, setBuildingId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [nip, setNip] = useState("");
  const [unitNo, setUnitNo] = useState("");
  const [active, setActive] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setBuildingId(initial?.building_id ?? defaultBuildingId ?? "");
      setName(initial?.name ?? "");
      setEmail(initial?.email ?? "");
      setNip(initial?.nip ?? "");
      setUnitNo(initial?.unit_no ?? "");
      setActive(initial?.active ?? true);
      setError(null);
    }
  }, [open, initial, defaultBuildingId]);

  const hasNip = nip.trim().length > 0;

  async function save() {
    setError(null);
    if (!name.trim()) {
      setError("Imię / nazwa firmy jest wymagane.");
      return;
    }
    if (!email.trim()) {
      setError("E-mail jest wymagany.");
      return;
    }
    if (!unitNo.trim()) {
      setError("Nr lokalu jest wymagany.");
      return;
    }
    if (!initial && !buildingId) {
      setError("Wybierz budynek, do którego należy najemca.");
      return;
    }
    setBusy(true);
    try {
      const common = {
        name: name.trim(),
        email: email.trim(),
        unit_no: unitNo.trim(),
        nip: nip.trim() || null,
        active,
      };
      if (initial) {
        await updateTenant(initial.id, common);
      } else {
        await createTenant({ building_id: buildingId as string, ...common });
      }
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Nie udało się zapisać najemcy.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ModalShell
      open={open}
      onClose={onClose}
      title={initial ? "Edytuj najemcę" : "Dodaj najemcę"}
      subtitle={initial ? initial.name : "Nowy najemca w systemie"}
      footer={
        <>
          <button className="btn ghost" type="button" onClick={onClose} disabled={busy}>
            Anuluj
          </button>
          <div className="spacer" />
          <button className="btn primary" type="button" onClick={save} disabled={busy}>
            <Icon name={initial ? "check" : "plus"} size={15} />
            {busy ? " Zapisywanie…" : initial ? " Zapisz zmiany" : " Dodaj najemcę"}
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
            <select className="fin" value={buildingId} onChange={(e) => setBuildingId(e.target.value)}>
              <option value="">— wybierz budynek —</option>
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="fr full">
          <label>Imię i nazwisko / nazwa firmy</label>
          <input
            className="fin"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="np. Jan Kowalski lub Firma XYZ sp. z o.o."
          />
        </div>
        <div className="fr">
          <label>E-mail</label>
          <input
            className="fin"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="kontakt@email.pl"
          />
        </div>
        <div className="fr">
          <label>Nr lokalu</label>
          <input
            className="fin"
            value={unitNo}
            onChange={(e) => setUnitNo(e.target.value)}
            placeholder="np. U1, M3"
          />
        </div>
        <div className="fr">
          <label>
            NIP <span className="opt">(opcjonalny)</span>
          </label>
          <input
            className="fin mono"
            value={nip}
            onChange={(e) => setNip(e.target.value)}
            placeholder="873-000-00-00"
          />
          <div className={"fhint" + (hasNip ? " vat" : " rachunek")}>
            {hasNip ? "✓ Faktura VAT" : "Brak NIP → zostanie wystawiony rachunek"}
          </div>
        </div>
        <div className="fr">
          <label>Status</label>
          <div className="fseg" style={{ display: "flex", width: "100%" }}>
            <button type="button" className={active ? "on" : ""} onClick={() => setActive(true)}>
              Aktywny
            </button>
            <button type="button" className={!active ? "on" : ""} onClick={() => setActive(false)}>
              Nieaktywny
            </button>
          </div>
        </div>
      </div>
    </ModalShell>
  );
}
