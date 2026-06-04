import { useAuth } from "../../auth/AuthContext";
import { initials } from "../../lib/format";
import { Icon } from "../shared/Icon";

export function Topbar({ title, orgName }: { title: string; orgName: string }) {
  const { session, signOut } = useAuth();
  const userEmail = session?.user?.email ?? "";

  return (
    <div className="topbar">
      <div className="crumb">
        <b>{title}</b> · maj 2026
      </div>
      <div className="search">Szukaj licznika, najemcy, faktury…</div>
      <div className="spacer" />
      <button className="btn ghost sm" type="button">
        <Icon name="bell" size={15} /> Alerty
      </button>
      <div className="org-chip">
        <span>{orgName}</span>
        <div className="avatar" title={userEmail}>
          {initials(orgName)}
        </div>
      </div>
      <button className="btn ghost sm" type="button" onClick={() => void signOut()} title="Wyloguj">
        <Icon name="logout" size={15} /> Wyloguj
      </button>
    </div>
  );
}
