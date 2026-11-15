// Panel de administracion de usuarios/restaurantes (Responsable: Aaron).
// HU: Como administrador quiero ver los restaurantes con sus sedes, ubicacion, aforo y
// precios, y activar o desactivar cuentas, sin acceder a datos confidenciales.
import { Fragment, useState } from "react";
import { api } from "../api/client";
import Spinner from "../components/ui/Spinner";
import { useI18n } from "../i18n/LanguageContext";
import { money } from "../i18n/formatters";
import useAsync from "../lib/useAsync";

function Stat({ label, value }) {
  return (
    <div className="card">
      <div className="faint">{label}</div>
      <div className="big-number">{value}</div>
    </div>
  );
}

function fmtDate(iso, lang) {
  if (!iso) return null;
  return new Date(iso).toLocaleString(lang === "en" ? "en-US" : "es-PE", { dateStyle: "medium", timeStyle: "short" });
}

function Restaurants() {
  const { t } = useI18n();
  const res = useAsync(() => api("/api/admin/restaurants"), []);
  const [open, setOpen] = useState(null);
  if (res.loading && !res.data) return <Spinner />;
  const rows = res.data || [];
  return (
    <div className="card table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>{t("col_restaurant")}</th>
            <th>{t("col_sites")}</th>
            <th>{t("col_capacity")}</th>
            <th>{t("col_prices")}</th>
            <th>{t("col_status")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <Fragment key={r.id}>
              <tr>
                <td>
                  <div className="strong">{r.name}</div>
                  <div className="faint">{r.category || ""}</div>
                </td>
                <td>
                  {r.sites.length === 0 && <span className="faint">-</span>}
                  {r.sites.map((s) => (
                    <div key={s.id} style={{ marginBottom: 4 }}>
                      <b>{s.name}</b> <span className="muted">{s.district || ""}</span>{" "}
                      <a className="faint" href={`https://www.google.com/maps?q=${s.lat},${s.lon}`} target="_blank" rel="noreferrer">↗</a>
                      <div className="faint">{s.capacity} {t("people")} · {String(s.open_hour).padStart(2, "0")}-{String(s.close_hour).padStart(2, "0")}h</div>
                    </div>
                  ))}
                </td>
                <td className="strong">{r.total_capacity}</td>
                <td>
                  {r.menu_stats.count === 0 ? (
                    <span className="faint">{t("no_menu")}</span>
                  ) : (
                    <>
                      <div>S/ {money(r.menu_stats.min)} - {money(r.menu_stats.max)}</div>
                      <button className="btn btn-sm btn-ghost" style={{ padding: "2px 0" }} onClick={() => setOpen(open === r.id ? null : r.id)}>
                        {open === r.id ? t("hide_menu") : t("view_menu", { count: r.menu_stats.count })}
                      </button>
                    </>
                  )}
                </td>
                <td>
                  <span className={`badge ${r.is_active ? "badge-low" : "badge-neutral"}`}>{r.is_active ? t("active") : t("inactive")}</span>
                </td>
              </tr>
              {open === r.id && (
                <tr>
                  <td colSpan={5} style={{ background: "var(--bg-soft)" }}>
                    <div className="grid grid-3" style={{ gap: 8 }}>
                      {r.menu.map((m, i) => (
                        <div key={i} className="row">
                          <span>{m.name}</span>
                          <span className="spacer" />
                          <b>S/ {money(m.price)}</b>
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Users() {
  const { t, tError, lang } = useI18n();
  const res = useAsync(() => api("/api/admin/users"), []);
  const [error, setError] = useState("");
  if (res.loading && !res.data) return <Spinner />;

  async function toggle(u) {
    setError("");
    try {
      await api(`/api/admin/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } });
      res.reload(true);
    } catch (err) {
      setError(tError(err));
    }
  }

  return (
    <div className="card table-wrap">
      {error && <div className="alert alert-error" style={{ marginBottom: 10 }}>{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>{t("col_email")}</th>
            <th>{t("col_restaurant")}</th>
            <th>{t("col_role")}</th>
            <th>{t("col_last_login")}</th>
            <th>{t("col_status")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {(res.data || []).map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              <td>{u.restaurant || "-"}</td>
              <td>{t(`role_${u.role}`)}</td>
              <td className="muted">{fmtDate(u.last_login_at, lang) || t("never")}</td>
              <td><span className={`badge ${u.is_active ? "badge-low" : "badge-neutral"}`}>{u.is_active ? t("active") : t("inactive")}</span></td>
              <td style={{ textAlign: "right" }}>
                {u.role !== "admin" && (
                  <button className={`btn btn-sm ${u.is_active ? "btn-danger" : ""}`} onClick={() => toggle(u)}>
                    {u.is_active ? t("deactivate") : t("activate")}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminPage() {
  const { t, lang } = useI18n();
  const stats = useAsync(() => api("/api/admin/stats"), []);
  const [tab, setTab] = useState("restaurants");
  const s = stats.data;
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("admin_title")}</h1>
          <p className="page-sub">{t("admin_sub")}</p>
        </div>
      </div>
      {s && (
        <div className="grid grid-4" style={{ marginBottom: "var(--gap)" }}>
          <Stat label={t("stat_restaurants")} value={s.restaurants} />
          <Stat label={t("stat_sites")} value={s.sites} />
          <Stat label={t("stat_items")} value={s.menu_items} />
          <Stat label={t("stat_users")} value={s.users} />
        </div>
      )}
      {s && <p className="faint" style={{ marginBottom: 14 }}>{t("stat_last_update")}: {fmtDate(s.last_data_update, lang) || t("never")}</p>}
      <div className="tabs">
        <button className={`tab ${tab === "restaurants" ? "active" : ""}`} onClick={() => setTab("restaurants")}>{t("tab_restaurants")}</button>
        <button className={`tab ${tab === "users" ? "active" : ""}`} onClick={() => setTab("users")}>{t("tab_users")}</button>
      </div>
      {tab === "restaurants" ? <Restaurants /> : <Users />}
    </>
  );
}
