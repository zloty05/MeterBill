import { useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { Icon } from "../components/shared/Icon";

export function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const { error } = await signIn(email.trim(), password);
    setBusy(false);
    if (error) setError(error);
    // sukces → onAuthStateChange ustawia sesję, App przełącza na AppShell
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={onSubmit}>
        <div className="login-brand">
          <div className="logo-mark">
            <Icon name="bolt" size={18} />
          </div>
          <div>
            <div className="login-title">EnergyBill</div>
            <div className="login-sub">Panel zarządcy nieruchomości</div>
          </div>
        </div>

        {error && <div className="login-err">{error}</div>}

        <div className="login-form">
          <div className="fr">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              className="fin"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="zarzadca@firma.pl"
              required
            />
          </div>
          <div className="fr">
            <label htmlFor="password">Hasło</label>
            <input
              id="password"
              className="fin"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
        </div>

        <button className="btn primary" type="submit" disabled={busy} style={{ justifyContent: "center" }}>
          {busy ? "Logowanie…" : "Zaloguj się"}
        </button>
      </form>
    </div>
  );
}
