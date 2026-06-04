import type { ReactNode } from "react";
import { Icon } from "../shared/Icon";

// Port z mockupu (modals.jsx). Klik poza modal → zamknięcie; animacje w tokens.css.
export function ModalShell({
  open,
  onClose,
  title,
  subtitle,
  size,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  size?: "lg";
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div
      className={"modal-overlay" + (open ? " open" : "")}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className={"modal" + (size ? " " + size : "")}>
        <div className="modal-head">
          <div>
            <h3>{title}</h3>
            {subtitle && <div className="sub">{subtitle}</div>}
          </div>
          <button className="x" type="button" onClick={onClose}>
            <Icon name="x" size={16} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}
