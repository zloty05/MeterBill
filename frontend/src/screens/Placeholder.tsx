// Ekrany jeszcze niezbudowane w tym etapie (Liczniki/Najemcy/Taryfy/Faktury).
export function Placeholder({ title }: { title: string }) {
  return (
    <div className="content">
      <div className="page-h hand-title">{title}</div>
      <div className="card sketch">
        <div className="empty-hint">
          Ekran „{title}" w przygotowaniu — kolejny etap fazy frontendowej.
        </div>
      </div>
    </div>
  );
}
