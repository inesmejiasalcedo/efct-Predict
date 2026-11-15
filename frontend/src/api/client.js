// Cliente HTTP hacia el backend (Responsable: Mariana).
// Adjunta el token de sesion y convierte errores del backend en codigos traducibles.

const API_BASE = import.meta.env.VITE_API_URL || ""; // vacio = mismo origen (proxy de Vite o backend en la nube)
const TOKEN_KEY = "efct_token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* almacenamiento bloqueado: la sesion dura solo esta pestana */
  }
}

export class ApiError extends Error {
  constructor(status, code, problems) {
    super(code);
    this.status = status;
    this.code = code;
    this.problems = problems || [];
  }
}

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

export async function api(path, { method = "GET", body, params } = {}) {
  let url = API_BASE + path;
  if (params) url += "?" + new URLSearchParams(params).toString();
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError(0, "network_error");
  }
  if (res.status === 204) return null;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* respuesta sin cuerpo */
  }
  if (!res.ok) {
    const detail = data?.detail;
    const code = typeof detail === "string" ? detail : detail?.code || (Array.isArray(detail) ? "invalid_data" : "server_error");
    if (res.status === 401 && token) onUnauthorized();
    throw new ApiError(res.status, code, detail?.problems);
  }
  return data;
}
