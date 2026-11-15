// Menu: item, precio y descripcion opcional mediante cajas de texto (Responsable: Matias).
import { useState } from "react";
import { api } from "../../api/client";
import { useI18n } from "../../i18n/LanguageContext";
import { money } from "../../i18n/formatters";
import useAsync from "../../lib/useAsync";
import Spinner from "../ui/Spinner";

const EMPTY = { name: "", price: "", description: "", category: "" };

function ItemForm({ initial, onSubmit, onCancel, submitLabel }) {
  const { t } = useI18n();
  const [form, setForm] = useState(initial || EMPTY);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    const ok = await onSubmit({ ...form, price: Number(form.price) });
    setBusy(false);
    if (ok && !initial) setForm(EMPTY);
  }

  return (
    <form onSubmit={submit} className="stack" style={{ gap: 10 }}>
      <div className="form-grid" style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
        <div className="field">
          <label>{t("item_name")}</label>
          <input className="input" value={form.name} onChange={set("name")} placeholder={t("item_name_ph")} required maxLength={120} />
        </div>
        <div className="field">
          <label>{t("item_price")}</label>
          <input className="input" type="number" min="0.1" step="0.1" value={form.price} onChange={set("price")} required />
        </div>
        <div className="field">
          <label>{t("item_category")} <span className="faint">({t("optional")})</span></label>
          <input className="input" value={form.category || ""} onChange={set("category")} placeholder={t("item_category_ph")} maxLength={60} />
        </div>
      </div>
      <div className="field">
        <label>{t("description")} <span className="faint">({t("optional")})</span></label>
        <textarea className="textarea" value={form.description || ""} onChange={set("description")} placeholder={t("item_desc_ph")} maxLength={500} />
      </div>
      <div className="row">
        <button className="btn btn-primary btn-sm" disabled={busy}>{busy ? t("saving") : submitLabel}</button>
        {onCancel && <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>{t("cancel")}</button>}
      </div>
    </form>
  );
}

export default function MenuEditor() {
  const { t, tError } = useI18n();
  const menu = useAsync(() => api("/api/business/menu"), []);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");

  async function save(body, id) {
    setError("");
    try {
      if (id) await api(`/api/business/menu/${id}`, { method: "PUT", body });
      else await api("/api/business/menu", { method: "POST", body });
      setEditing(null);
      await menu.reload(true);
      return true;
    } catch (err) {
      setError(tError(err));
      return false;
    }
  }

  async function remove(item) {
    if (!window.confirm(t("confirm_delete", { name: item.name }))) return;
    await api(`/api/business/menu/${item.id}`, { method: "DELETE" });
    menu.reload(true);
  }

  if (menu.loading && !menu.data) return <Spinner />;
  const items = menu.data?.items || [];
  const stats = menu.data?.stats;

  return (
    <div className="stack" style={{ gap: "var(--gap)" }}>
      <div className="card">
        <div className="card-title">{t("add_item")}</div>
        <ItemForm onSubmit={(b) => save(b)} submitLabel={t("add")} />
        {error && <div className="alert alert-error" style={{ marginTop: 10 }}>{error}</div>}
      </div>

      <div className="card">
        <div className="card-title">
          {t("tab_menu")}
          {stats?.count > 0 && <span className="hint">{t("menu_stats", { count: stats.count, avg: money(stats.avg), min: money(stats.min), max: money(stats.max) })}</span>}
        </div>
        {items.length === 0 ? (
          <p className="muted">{t("menu_empty")}</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>{t("item_name")}</th>
                  <th>{t("item_category")}</th>
                  <th style={{ textAlign: "right" }}>{t("item_price")}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {items.map((it) =>
                  editing === it.id ? (
                    <tr key={it.id}>
                      <td colSpan={4}>
                        <ItemForm initial={it} onSubmit={(b) => save(b, it.id)} onCancel={() => setEditing(null)} submitLabel={t("save")} />
                      </td>
                    </tr>
                  ) : (
                    <tr key={it.id}>
                      <td>
                        <div className="strong">{it.name}</div>
                        {it.description && <div className="faint">{it.description}</div>}
                      </td>
                      <td className="muted">{it.category || "-"}</td>
                      <td style={{ textAlign: "right" }} className="strong">S/ {money(it.price)}</td>
                      <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                        <button className="btn btn-sm btn-ghost" onClick={() => setEditing(it.id)}>{t("edit")}</button>
                        <button className="btn btn-sm btn-ghost" style={{ color: "var(--high)" }} onClick={() => remove(it)}>{t("delete")}</button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
