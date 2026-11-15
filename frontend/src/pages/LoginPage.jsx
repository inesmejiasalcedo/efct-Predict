// Inicio de sesion (Responsable: Mariana).
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LanguageToggle, useI18n } from "../i18n/LanguageContext";
import { BrandMark } from "../layout/AppLayout";

export function AuthLayout({ children }) {
  const { t } = useI18n();
  return (
    <div className="auth-wrap">
      <aside className="auth-side">
        <div className="row">
          <BrandMark size={38} />
          <strong style={{ fontSize: 18 }}>{t("app_name")}</strong>
        </div>
        <div>
          <h1>{t("side_title")}</h1>
          <p>{t("side_text")}</p>
          <div className="auth-points">
            <div>{t("side_p1")}</div>
            <div>{t("side_p2")}</div>
            <div>{t("side_p3")}</div>
          </div>
        </div>
        <small style={{ opacity: 0.7 }}>OpenWeather · TomTom · BCRP</small>
      </aside>
      <main className="auth-main">
        <div className="auth-card">
          <div className="row" style={{ justifyContent: "flex-end", marginBottom: 24 }}>
            <LanguageToggle />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const { t, tError } = useI18n();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const u = await login(email, password);
      navigate(u.role === "admin" ? "/admin" : "/", { replace: true });
    } catch (err) {
      setError(tError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <h2>{t("login_title")}</h2>
      <p className="muted" style={{ marginBottom: 24 }}>{t("login_sub")}</p>
      <form className="stack" onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">{t("email")}</label>
          <input id="email" className="input" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="password">{t("password")}</label>
          <input id="password" className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? t("loading") : t("login_btn")}
        </button>
      </form>
      <p className="muted" style={{ marginTop: 20, textAlign: "center" }}>
        {t("no_account")} <Link to="/registro" className="strong">{t("register_link")}</Link>
      </p>
    </AuthLayout>
  );
}
