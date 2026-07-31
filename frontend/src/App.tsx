import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

import ErrorBoundary from "@/components/common/ErrorBoundary";
import ProtectedRoute from "@/components/common/ProtectedRoute";
import AppLayout from "@/components/common/AppLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import VehiclesPage from "@/pages/VehiclesPage";
import VehicleDetailPage from "@/pages/VehicleDetailPage";
import SettingsPage from "@/pages/SettingsPage";
import MaintenanceGuidelinesPage from "@/pages/MaintenanceGuidelinesPage";
import NotFoundPage from "@/pages/NotFoundPage";

/**
 * Root application component.
 * Defines all client-side routes.
 *
 * Public routes  — login, register
 * Protected routes — wrapped in AppLayout (navbar + content area)
 */
export default function App() {
  return (
    <ErrorBoundary fallback={<NotFoundPage />}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes — all share AppLayout */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<><ErrorBoundary><DashboardPage /></ErrorBoundary></>} />
            <Route path="/vehicles" element={<><ErrorBoundary><VehiclesPage /></ErrorBoundary></>} />
            <Route path="/vehicles/:id" element={<><ErrorBoundary><VehicleDetailPage /></ErrorBoundary></>} />
            <Route path="/settings" element={<><ErrorBoundary><SettingsPage /></ErrorBoundary></>} />
            <Route path="/maintenance" element={<><ErrorBoundary><MaintenanceGuidelinesPage /></ErrorBoundary></>} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>

      <Toaster position="top-right" richColors />
    </ErrorBoundary>
  );
}
