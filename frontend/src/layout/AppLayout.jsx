// Estructura comun: barra superior + contenido (Responsable: Gabriel).
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LanguageToggle, useI18n } from "../i18n/LanguageContext";
import { SiteSelector } from "../site/SiteContext";

export function BrandMark({ size = 32 }) {
  return (
    <span className="brand-mark" style={{ width: size, height: size }}>
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="#17140f" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l6-7 4 3 8-9" />
      </svg>
    </span>
  );
}

export default function AppLayout() {
  const { user, logout, isAdmin } = useAuth();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const onDashboard = location.pathname === "/" || location.pathname.startsWith("/riesgo");

  const links = isAdmin
    ? [{ to: "/admin", label: t("nav_admin") }]
    : [
        { to: "/", label: t("nav_summary"), end: true },
        { to: "/negocio", label: t("nav_business") },
      ];
  links.push({ to: "/cuenta", label: t("nav_account") });

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to={isAdmin ? "/admin" : "/"} className="brand">
            <BrandMark />
            <span>
              {t("app_name")}
              <small>{t("tagline")}</small>
            </span>
          </NavLink>
          <nav className={`nav ${open ? "open" : ""}`} onClick={() => setOpen(false)}>
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end}>
                {l.label}
              </NavLink>
            ))}
            <button className="nav-logout" onClick={logout}>{t("logout")}</button>
          </nav>
          <div className="topbar-right">
            {onDashboard && <SiteSelector />}
            <LanguageToggle />
            <button className="btn btn-sm btn-ghost" onClick={logout} title={user?.email}>
              {t("logout")}
            </button>
            <button className="btn btn-sm menu-toggle" onClick={() => setOpen(!open)} aria-label="Menu">
              ☰
            </button>
          </div>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
      <footer className="footer">EFCT Predict v2 · ISW2 · Universidad de Lima</footer>
    </div>
  );
}
