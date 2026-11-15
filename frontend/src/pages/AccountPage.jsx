// Mi cuenta: cambio de contrasena e idioma (Responsable: Mariana; idioma: Aaron).
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { passwordChecks } from "../auth/passwordRules";
import { LanguageToggle, useI18n } from "../i18n/LanguageContext";
import { PasswordChecklist } from "./RegisterPage";

export default function AccountPage() {
  const { user, changePassword } = useAuth();
  const { t, tError } = useI18n();
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const valid = passwordChecks(form.next).every((c) => c.ok) && form.current;

  async function submit(e) {
    e.preventDefault();
    if (form.next !== form.confirm) return setMsg({ type: "error", text: t("passwords_dont_match") });
    setBusy(true);
    setMsg(null);
    try {
      await changePassword(form.current, form.next);
      setForm({ current: "", next: "", confirm: "" });
      setMsg({ type: "ok", text: t("password_changed") });
    } catch (err) {
      setMsg({ type: "error", text: tError(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("account_title")}</h1>
          <p className="page-sub">{t("signed_in_as")} {user?.email}</p>
        </div>
      </div>
      <div className="grid grid-2">
        <form className="card stack" onSubmit={submit}>
          <div className="card-title">{t("change_password")}</div>
          <div className="field">
            <label>{t("current_password")}</label>
            <input className="input" type="password" autoComplete="current-password" value={form.current} onChange={set("current")} />
          </div>
          <div className="field">
            <label>{t("new_password")}</label>
            <input className="input" type="password" autoComplete="new-password" value={form.next} onChange={set("next")} />
            <PasswordChecklist value={form.next} />
          </div>
          <div className="field">
            <label>{t("confirm_password")}</label>
            <input className="input" type="password" autoComplete="new-password" value={form.confirm} onChange={set("confirm")} />
          </div>
          {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
          <div>
            <button className="btn btn-primary" disabled={busy || !valid}>{busy ? t("saving") : t("save")}</button>
          </div>
        </form>
        <div className="card stack" style={{ alignSelf: "start" }}>
          <div className="card-title">{t("language")}</div>
          <LanguageToggle />
          <p className="faint">{t("language_help")}</p>
        </div>
      </div>
    </>
  );
}
