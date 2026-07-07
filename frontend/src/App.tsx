import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

import ProtectedRoute from "@/components/common/ProtectedRoute";
import DashboardPage from "@/pages/DashboardPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";


/**
 * Main App component.
 * Defines all client-side routes.
 *
 * Public routes: login and register
 * Protected routes: dashboard (requires valid JWT)
 */
export default function App() {
  return (
    <>
      <Routes>
        {/* Redirect root to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>

        {/* Catch all - redirect unknown routes to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      {/* Global toast notifications */}
      <Toaster position="top-right" richColors />
    </>
  );
}
