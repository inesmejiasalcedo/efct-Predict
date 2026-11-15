// Formulario de sede: ubicacion, aforo y horario (Responsable: Matias).
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useI18n } from "../../i18n/LanguageContext";

const EMPTY = { name: "", address: "", district: "", lat: "", lon: "", capacity: "", open_hour: 12, close_hour: 23 };
const HOURS = Array.from({ length: 25 }, (_, h) => h);

export default function SiteForm({ initial, onSaved, onCancel }) {
  const { t, tError } = useI18n();
  const [form, setForm] = useState(initial ? { ...EMPTY, ...initial } : EMPTY);
  const [districts, setDistricts] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/business/districts").then(setDistricts).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function pickDistrict(e) {
    const d = districts.find((x) => x.name === e.target.value);
    if (d) setForm({ ...form, district: d.name, lat: d.lat, lon: d.lon });
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const body = { ...form, lat: Number(form.lat), lon: Number(form.lon), capacity: Number(form.capacity), open_hour: Number(form.open_hour), close_hour: Number(form.close_hour) };
    try {
      const saved = initial?.id
        ? await api(`/api/business/sites/${initial.id}`, { method: "PUT", body })
        : await api("/api/business/sites", { method: "POST", body });
      onSaved(saved);
    } catch (err) {
      setError(tError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card stack" onSubmit={submit} style={{ background: "var(--bg-soft)" }}>
      <div className="card-title">{initial?.id ? t("edit_site") : t("add_site")}</div>
      <div className="form-grid">
        <div className="field">
          <label>{t("site_name")}</label>
          <input className="input" value={form.name} onChange={set("name")} placeholder={t("site_name_ph")} required />
        </div>
        <div className="field">
          <label>{t("address")} <span className="faint">({t("optional")})</span></label>
          <input className="input" value={form.address || ""} onChange={set("address")} />
        </div>
        <div className="field">
          <label>{t("district_preset")}</label>
          <select className="select" value={districts.some((d) => d.name === form.district) ? form.district : ""} onChange={pickDistrict}>
            <option value="">{t("district_choose")}</option>
            {[...new Set(districts.map((d) => d.city))].map((city) => (
              <optgroup key={city} label={city}>
                {districts.filter((d) => d.city === city).map((d) => (
                  <option key={d.name} value={d.name}>{d.name}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t("capacity")}</label>
          <input className="input" type="number" min="1" max="5000" value={form.capacity} onChange={set("capacity")} required />
          <span className="help">{t("capacity_help")}</span>
        </div>
        <div className="field">
          <label>{t("latitude")}</label>
          <input className="input" type="number" step="any" value={form.lat} onChange={set("lat")} required />
        </div>
        <div className="field">
          <label>{t("longitude")}</label>
          <input className="input" type="number" step="any" value={form.lon} onChange={set("lon")} required />
        </div>
        <div className="field">
          <label>{t("open_hour")}</label>
          <select className="select" value={form.open_hour} onChange={set("open_hour")}>
            {HOURS.slice(0, 24).map((h) => <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>)}
          </select>
        </div>
        <div className="field">
          <label>{t("close_hour")}</label>
          <select className="select" value={form.close_hour} onChange={set("close_hour")}>
            {HOURS.slice(1).map((h) => <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>)}
          </select>
        </div>
      </div>
      <span className="help faint">{t("location_help")}</span>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="row">
        <button className="btn btn-primary" disabled={busy}>{busy ? t("saving") : t("save")}</button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>{t("cancel")}</button>
      </div>
    </form>
  );
}
