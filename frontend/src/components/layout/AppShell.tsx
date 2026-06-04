import { useState } from "react";
import { getOrg } from "../../api/endpoints";
import { useAsync } from "../../lib/useAsync";
import { Dashboard } from "../../screens/Dashboard";
import { Budynki } from "../../screens/Budynki";
import { Placeholder } from "../../screens/Placeholder";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { NAV, type ScreenId } from "./nav";

export function AppShell() {
  const [screen, setScreen] = useState<ScreenId>("dashboard");
  const { data: org } = useAsync(() => getOrg(), []);
  const orgName = org?.name ?? "…";

  const title = NAV.find((n) => n.id === screen)?.label ?? "Dashboard";

  return (
    <div className="app">
      <Sidebar active={screen} onNav={setScreen} orgName={orgName} />
      <div className="main">
        <Topbar title={title} orgName={orgName} />
        {screen === "dashboard" && <Dashboard onOpenBuildings={() => setScreen("budynki")} />}
        {screen === "budynki" && <Budynki />}
        {screen === "liczniki" && <Placeholder title="Liczniki" />}
        {screen === "najemcy" && <Placeholder title="Najemcy" />}
        {screen === "taryfy" && <Placeholder title="Taryfy" />}
        {screen === "faktury" && <Placeholder title="Faktury" />}
      </div>
    </div>
  );
}
