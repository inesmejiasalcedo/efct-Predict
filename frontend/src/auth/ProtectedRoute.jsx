// Protege rutas: sin sesion -> login. adminOnly -> solo administradores. (Responsable: Mariana)
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Spinner from "../components/ui/Spinner";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner full />;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}
