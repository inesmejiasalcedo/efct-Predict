// Sede seleccionada en toda la app (Responsable: Gabriel - navegacion).
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const SiteContext = createContext(null);
const KEY = "efct_site";

export function SiteProvider({ children }) {
  const { user } = useAuth();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteIdState] = useState(() => {
    try {
      return Number(localStorage.getItem(KEY)) || null;
    } catch {
      return null;
    }
  });
  const [loaded, setLoaded] = useState(false);

  const reload = useCallback(async () => {
    if (!user || user.role === "admin") {
      setSites([]);
      setLoaded(true);
      return;
    }
    try {
      const list = await api("/api/business/sites");
      setSites(list);
      setSiteIdState((cur) => (list.some((s) => s.id === cur) ? cur : list[0]?.id ?? null));
    } finally {
      setLoaded(true);
    }
  }, [user]);

  useEffect(() => {
    setLoaded(false);
    reload();
  }, [reload]);

  function setSiteId(id) {
    setSiteIdState(id);
    try {
      localStorage.setItem(KEY, String(id));
    } catch {
      /* sin almacenamiento */
    }
  }

  const site = sites.find((s) => s.id === siteId) || null;
  return <SiteContext.Provider value={{ sites, site, siteId, setSiteId, reload, loaded }}>{children}</SiteContext.Provider>;
}

export function useSite() {
  return useContext(SiteContext);
}

export function SiteSelector() {
  const { sites, siteId, setSiteId } = useSite();
  if (sites.length < 2) return null;
  return (
    <select className="select" style={{ width: "auto", borderRadius: 999, padding: "7px 12px" }} value={siteId ?? ""} onChange={(e) => setSiteId(Number(e.target.value))}>
      {sites.map((s) => (
        <option key={s.id} value={s.id}>{s.name}</option>
      ))}
    </select>
  );
}
