// Rutas de la aplicacion (Responsable: Gabriel - navegacion).
import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import { useAuth } from "./auth/AuthContext";
import AppLayout from "./layout/AppLayout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SummaryPage from "./pages/SummaryPage";
import RiskDetailPage from "./pages/RiskDetailPage";
import BusinessPage from "./pages/BusinessPage";
import AccountPage from "./pages/AccountPage";
import AdminPage from "./pages/AdminPage";

function Home() {
  const { isAdmin } = useAuth();
  return isAdmin ? <Navigate to="/admin" replace /> : <SummaryPage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="riesgo/:type" element={<RiskDetailPage />} />
        <Route path="negocio" element={<BusinessPage />} />
        <Route path="cuenta" element={<AccountPage />} />
        <Route
          path="admin"
          element={
            <ProtectedRoute adminOnly>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
