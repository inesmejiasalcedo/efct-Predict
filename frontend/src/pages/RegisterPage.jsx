// Registro de un nuevo restaurante (Responsable: Mariana).
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { passwordChecks } from "../auth/passwordRules";
import { useI18n } from "../i18n/LanguageContext";
import { AuthLayout } from "./LoginPage";

export function PasswordChecklist({ value }) {
  const { t } = useI18n();
  return (
    <div className="row" style={{ gap: 12, fontSize: 12 }}>
      {passwordChecks(value).map((c) => (
        <span key={c.key} style={{ color: c.ok ? "var(--low)" : "var(--faint)" }}>
          {c.ok ? "✓" : "○"} {t(c.key)}
        </span>
      ))}
    </div>
  );
}

export default function RegisterPage() {
  const { user, register } = useAuth();
  const { t, tError } = useI18n();
  const navigate = useNavigate();
  const [form, setForm] = useState({ restaurant: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;
  const valid = passwordChecks(form.password).every((c) => c.ok);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(form.email, form.password, form.restaurant);
      navigate("/negocio?nuevo=1", { replace: true });
    } catch (err) {
      setError(tError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <h2>{t("register_title")}</h2>
      <p className="muted" style={{ marginBottom: 24 }}>{t("register_sub")}</p>
      <form className="stack" onSubmit={submit}>
        <div className="field">
          <label htmlFor="restaurant">{t("restaurant_name")}</label>
          <input id="restaurant" className="input" value={form.restaurant} onChange={set("restaurant")} required maxLength={120} />
        </div>
        <div className="field">
          <label htmlFor="email">{t("email")}</label>
          <input id="email" className="input" type="email" autoComplete="email" value={form.email} onChange={set("email")} required />
        </div>
        <div className="field">
          <label htmlFor="password">{t("password")}</label>
          <input id="password" className="input" type="password" autoComplete="new-password" value={form.password} onChange={set("password")} required />
          <PasswordChecklist value={form.password} />
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <button className="btn btn-primary btn-block" disabled={busy || !valid}>
          {busy ? t("loading") : t("register_btn")}
        </button>
      </form>
      <p className="muted" style={{ marginTop: 20, textAlign: "center" }}>
        {t("have_account")} <Link to="/login" className="strong">{t("login_link")}</Link>
      </p>
    </AuthLayout>
  );
}
