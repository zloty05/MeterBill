import { Icon } from "../shared/Icon";
import { NAV, type ScreenId } from "./nav";

export function Sidebar({
  active,
  onNav,
  orgName,
}: {
  active: ScreenId;
  onNav: (id: ScreenId) => void;
  orgName: string;
}) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark">
          <Icon name="bolt" size={18} />
        </div>
        <div>
          <div className="logo-name">EnergyBill</div>
          <div className="logo-sub">{orgName}</div>
        </div>
      </div>
      {NAV.map((n) => (
        <div
          key={n.id}
          className={"nav-item" + (active === n.id ? " active" : "")}
          onClick={() => onNav(n.id)}
        >
          <Icon name={n.icon} />
          <span>{n.label}</span>
        </div>
      ))}
      <div className="nav-spacer" />
      <div className="sb-foot">
        v0.1 · plan PRO
        <br />
        Gateway: WAGO PFC300 ✓ online
      </div>
    </aside>
  );
}
