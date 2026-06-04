import type { BuildingOut } from "../../api/types";
import type { BuildingStats } from "../../lib/aggregates";
import { Icon } from "../shared/Icon";
import { Pill } from "../shared/Pill";

// Kafelek budynku (Layout B). Agregaty z buildBuildingStats; pola, których
// API nie dostarcza (online/total, kWh/mc) → "—".
export function BuildingTile({
  b,
  stats,
  onOpen,
}: {
  b: BuildingOut;
  stats?: BuildingStats;
  onOpen?: () => void;
}) {
  const toSend = stats?.toSend ?? 0;
  const overdue = stats?.overdue ?? 0;
  const meters = stats?.metersTotal ?? 0;

  return (
    <div className="card sketch bld-tile">
      <div className="bld-head">
        <div>
          <div className="ttl">{b.name}</div>
          <div className="addr">{b.address}</div>
        </div>
        <div className="spacer" />
        {overdue > 0 ? <Pill status="draft" /> : <Pill status="ok" />}
      </div>
      <div className="bld-mini">
        <div>
          <div className="m-num green">{meters || "—"}</div>
          <div className="m-lbl">liczniki</div>
        </div>
        <div>
          <div className="m-num">{toSend}</div>
          <div className="m-lbl">do wysłania</div>
        </div>
        <div>
          <div className={"m-num" + (overdue ? " red" : "")}>{overdue}</div>
          <div className="m-lbl">zaległe</div>
        </div>
        <div>
          <div className="m-num">{stats?.tenantsCount ?? "—"}</div>
          <div className="m-lbl">najemcy</div>
        </div>
      </div>
      <div className="bld-foot">
        <span className="cell-sub" style={{ fontSize: 14, color: "var(--ink-soft)" }}>
          {toSend} faktur gotowych
        </span>
        <div className="spacer" />
        <button className="btn sm ghost" type="button" onClick={onOpen}>
          <Icon name="arrow" size={13} /> Szczegóły
        </button>
      </div>
    </div>
  );
}
