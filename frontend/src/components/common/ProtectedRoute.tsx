import { Navigate, Outlet } from "react-router-dom";
import useAuthStore from "@/store/auth.store";

/**
 * Wraps routes that require authentication.
 * Redirects to login if the user is not authenticated.
 */
export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
