/* global React, ReactDOM, Sidebar, Topbar, LayoutAction, LayoutBuildings,
   ScreenBudynki, ScreenLiczniki, ScreenNajemcy, ScreenFaktury, ScreenTaryfy,
   useTweaks, TweaksPanel, TweakSection, TweakRadio */
const { useState: useStateApp, useEffect: useEffectApp } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "sidebar": "dark",
  "density": "compact",
  "layout": "buildings"
}/*EDITMODE-END*/;

function Dashboard({ t, setTweak }) {
  const [layout, setLayout] = useStateApp(t.layout || "buildings");
  useEffectApp(() => { if (t.layout && t.layout !== layout) setLayout(t.layout); }, [t.layout]);
  const pick = (id) => { setLayout(id); setTweak("layout", id); };
  return (
    <>
      <div className="layout-switch">
        <div className="seg">
          <button className={layout === "action" ? "on" : ""} onClick={() => pick("action")}>① Co wymaga uwagi dziś</button>
          <button className={layout === "buildings" ? "on" : ""} onClick={() => pick("buildings")}>② Kafelki per budynek</button>
        </div>
        <span className="switch-note">2 warianty układu — przełączaj do porównania</span>
      </div>
      {layout === "action" ? <LayoutAction /> : <LayoutBuildings />}
    </>
  );
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [screen, setScreen] = useStateApp("dashboard");

  useEffectApp(() => {
    document.body.setAttribute("data-sidebar", t.sidebar);
    document.body.setAttribute("data-density", t.density);
  }, [t.sidebar, t.density]);

  const title = (WF.nav.find((n) => n.id === screen) || {}).label || "Dashboard";

  const SCREENS = {
    dashboard: <Dashboard t={t} setTweak={setTweak} />,
    budynki: <ScreenBudynki />,
    liczniki: <ScreenLiczniki />,
    najemcy: <ScreenNajemcy />,
    taryfy: <ScreenTaryfy />,
    faktury: <ScreenFaktury />,
  };

  return (
    <div className="app">
      <Sidebar active={screen} onNav={setScreen} />
      <div className="main">
        <Topbar title={title} />
        {SCREENS[screen]}
      </div>

      <TweaksPanel>
        <TweakSection label="Wygląd" />
        <TweakRadio label="Sidebar" value={t.sidebar}
          options={[{ value: "light", label: "Jasny" }, { value: "dark", label: "Ciemny" }]}
          onChange={(v) => setTweak("sidebar", v)} />
        <TweakRadio label="Gęstość" value={t.density}
          options={[{ value: "comfortable", label: "Komfort" }, { value: "compact", label: "Kompakt" }]}
          onChange={(v) => setTweak("density", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
