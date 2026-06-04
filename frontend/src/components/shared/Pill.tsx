// Status pill — port z mockupu (components.jsx). Klasy CSS w tokens.css.
export type PillStatus =
  | "ok"
  | "online"
  | "offline"
  | "est"
  | "ready"
  | "draft"
  | "sent"
  | "paid"
  | "overdue";

const LABELS: Record<PillStatus, string> = {
  ok: "online",
  online: "online",
  offline: "offline",
  est: "szacowany",
  ready: "gotowa",
  draft: "szkic",
  sent: "wysłana",
  paid: "opłacona",
  overdue: "po terminie",
};

const CLASS: Record<PillStatus, string> = {
  ok: "ok",
  online: "online",
  offline: "offline",
  est: "est",
  ready: "ready",
  draft: "draft",
  sent: "sent",
  paid: "paid",
  overdue: "overdue",
};

export function Pill({ status }: { status: PillStatus }) {
  return (
    <span className={"pill " + CLASS[status]}>
      <span className="dot" />
      {LABELS[status]}
    </span>
  );
}
