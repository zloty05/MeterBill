import { useAuth } from "./auth/AuthContext";
import { AppShell } from "./components/layout/AppShell";
import { Login } from "./screens/Login";

export default function App() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="login-wrap">
        <div className="login-sub">Wczytywanie…</div>
      </div>
    );
  }

  return session ? <AppShell /> : <Login />;
}
