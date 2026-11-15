// Personalizacion del negocio: restaurante, sedes y menu (Responsable: Matias).
// HU: Como dueno quiero registrar mis sedes (ubicacion, aforo) y mi menu para que el
// pronostico se ajuste a mi negocio.
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import MenuEditor from "../components/business/MenuEditor";
import SiteForm from "../components/business/SiteForm";
import Spinner from "../components/ui/Spinner";
import { useI18n } from "../i18n/LanguageContext";
import useAsync from "../lib/useAsync";
import { useSite } from "../site/SiteContext";

function RestaurantTab() {
  const { t, tError } = useI18n();
  const res = useAsync(() => api("/api/business/restaurant"), []);
  const [msg, setMsg] = useState(null);
  const [form, setForm] = useState(null);
  if (res.loading && !res.data) return <Spinner />;
  const f = form || { name: res.data?.name || "", category: res.data?.category || "", description: res.data?.description || "" };
  const set = (k) => (e) => setForm({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    try {
      await api("/api/business/restaurant", { method: "PUT", body: f });
      setMsg({ type: "ok", text: t("saved") });
    } catch (err) {
      setMsg({ type: "error", text: tError(err) });
    }
  }

  return (
    <form className="card stack" onSubmit={submit} style={{ maxWidth: 640 }}>
      <div className="field">
        <label>{t("restaurant_name")}</label>
        <input className="input" value={f.name} onChange={set("name")} required maxLength={120} />
      </div>
      <div className="field">
        <label>{t("category")} <span className="faint">({t("optional")})</span></label>
        <input className="input" value={f.category} onChange={set("category")} placeholder={t("category_ph")} maxLength={80} />
      </div>
      <div className="field">
        <label>{t("description")} <span className="faint">({t("optional")})</span></label>
        <textarea className="textarea" value={f.description} onChange={set("description")} placeholder={t("restaurant_desc_ph")} maxLength={500} />
      </div>
      {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
      <div><button className="btn btn-primary">{t("save")}</button></div>
    </form>
  );
}

function SitesTab({ startOpen }) {
  const { t } = useI18n();
  const { sites, reload } = useSite();
  const [editing, setEditing] = useState(startOpen ? "new" : null);

  async function remove(site) {
    if (!window.confirm(t("confirm_delete", { name: site.name }))) return;
    await api(`/api/business/sites/${site.id}`, { method: "DELETE" });
    reload();
  }

  async function saved() {
    setEditing(null);
    await reload();
  }

  return (
    <div className="stack" style={{ gap: "var(--gap)" }}>
      {sites.length === 0 && editing !== "new" && <div className="alert alert-info">{t("sites_empty")}</div>}
      {editing === "new" ? (
        <SiteForm onSaved={saved} onCancel={() => setEditing(null)} />
      ) : (
        <div><button className="btn btn-primary" onClick={() => setEditing("new")}>+ {t("add_site")}</button></div>
      )}
      <div className="grid grid-2">
        {sites.map((s) =>
          editing === s.id ? (
            <div key={s.id} className="span-2">
              <SiteForm initial={s} onSaved={saved} onCancel={() => setEditing(null)} />
            </div>
          ) : (
            <div key={s.id} className="card stack" style={{ gap: 8 }}>
              <div className="row">
                <div className="strong" style={{ fontSize: 17 }}>{s.name}</div>
                <span className="spacer" />
                <button className="btn btn-sm btn-ghost" onClick={() => setEditing(s.id)}>{t("edit")}</button>
                <button className="btn btn-sm btn-ghost" style={{ color: "var(--high)" }} onClick={() => remove(s)}>{t("delete")}</button>
              </div>
              <div className="muted">{[s.address, s.district].filter(Boolean).join(" · ") || `${s.lat}, ${s.lon}`}</div>
              <div className="row" style={{ gap: 16 }}>
                <span><span className="faint">{t("capacity")}: </span><b>{s.capacity}</b> {t("people")}</span>
                <span><span className="faint">{t("schedule")}: </span><b>{String(s.open_hour).padStart(2, "0")}:00 - {String(s.close_hour).padStart(2, "0")}:00</b></span>
              </div>
              <a className="faint" href={`https://www.google.com/maps?q=${s.lat},${s.lon}`} target="_blank" rel="noreferrer">
                {s.lat}, {s.lon} ↗
              </a>
            </div>
          )
        )}
      </div>
    </div>
  );
}

export default function BusinessPage() {
  const { t } = useI18n();
  const [params] = useSearchParams();
  const isNew = params.get("nuevo") === "1";
  const [tab, setTab] = useState(isNew ? "sites" : "sites");
  const tabs = [
    ["sites", t("tab_sites")],
    ["menu", t("tab_menu")],
    ["restaurant", t("tab_restaurant")],
  ];
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("business_title")}</h1>
          <p className="page-sub">{t("business_sub")}</p>
        </div>
      </div>
      <div className="tabs">
        {tabs.map(([k, label]) => (
          <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>
      {tab === "sites" && <SitesTab startOpen={isNew} />}
      {tab === "menu" && <MenuEditor />}
      {tab === "restaurant" && <RestaurantTab />}
    </>
  );
}
