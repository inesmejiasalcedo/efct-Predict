// Sesion del usuario (Responsable: Mariana).
// Ya no hay usuario/contrasena fijos: el backend valida con bcrypt y entrega un token JWT.
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    if (!getToken()) return;
    api("/api/auth/me")
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false));
  }, [logout]);

  async function login(email, password) {
    const data = await api("/api/auth/login", { method: "POST", body: { email, password } });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function register(email, password, restaurantName) {
    const data = await api("/api/auth/register", {
      method: "POST",
      body: { email, password, restaurant_name: restaurantName },
    });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function changePassword(current, next) {
    await api("/api/auth/change-password", { method: "POST", body: { current_password: current, new_password: next } });
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout, changePassword, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
