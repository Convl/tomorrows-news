import { useAuth } from "../contexts/AuthContext";
import { Outlet, Navigate } from "react-router-dom";

export default function ProtectedRoute() {
  const { user } = useAuth();
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
