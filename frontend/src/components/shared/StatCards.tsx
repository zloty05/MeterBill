import { Icon, type IconName } from "./Icon";

export type StatCard = {
  tone?: "" | "accent" | "warn" | "danger";
  label: string;
  num: string | number;
  sub: string;
  icon: IconName;
};

// Prop-driven (mockup czytał globalne WF.stats). Tu wartości liczone z API.
export function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="stat-row">
      {cards.map((c, i) => (
        <div key={i} className={"stat sketch " + (i % 2 ? "sketch-2 " : "") + (c.tone ?? "")}>
          <div className="corner">
            <Icon name={c.icon} size={20} />
          </div>
          <div className="label">{c.label}</div>
          <div className="num">{c.num}</div>
          <div className="sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}
