// Traduccion de toda la pagina ES/EN (Responsable: Aaron).
// t("clave", {param}) devuelve el texto en el idioma activo con {param} reemplazado.
import { createContext, useContext, useEffect, useState } from "react";
import es from "./es";
import en from "./en";
import { api } from "../api/client";

const DICTS = { es, en };
const KEY = "efct_lang";
const LanguageContext = createContext(null);

function initialLang() {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "es" || saved === "en") return saved;
  } catch {
    /* sin almacenamiento */
  }
  return navigator.language?.startsWith("en") ? "en" : "es";
}

export function translate(lang, key, params = {}) {
  const text = DICTS[lang]?.[key] ?? DICTS.es[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, p) => (params[p] ?? params[p] === 0 ? String(params[p]) : ""));
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  function setLang(next, { persistRemote = true } = {}) {
    setLangState(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* sin almacenamiento */
    }
    if (persistRemote) api("/api/auth/language", { method: "PUT", body: { language: next } }).catch(() => {});
  }

  const t = (key, params) => translate(lang, key, params);
  const tError = (err) => t(`err.${err?.code || "server_error"}`);

  return <LanguageContext.Provider value={{ lang, setLang, t, tError }}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  return useContext(LanguageContext);
}

export function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <div className="seg" role="group" aria-label="Language">
      {["es", "en"].map((l) => (
        <button key={l} className={lang === l ? "active" : ""} onClick={() => setLang(l)} type="button">
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
