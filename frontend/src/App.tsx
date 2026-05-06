import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ImportReportPage } from "./pages/ImportReportPage";
import { ImportReviewPage } from "./pages/ImportReviewPage";
import { ImportsPage } from "./pages/ImportsPage";
import { LoginPage } from "./pages/LoginPage";
import { OverviewPage } from "./pages/OverviewPage";
import { UserSettingsPage } from "./pages/UserSettingsPage";

function RootRedirect() {
  const { status } = useAuth();

  if (status === "bootstrapping") {
    return (
      <div className="screen-state">
        <div className="loading-pulse" />
        <strong>Preparando o cockpit financeiro...</strong>
        <p>Estamos carregando sessao, configuracao e rotas protegidas.</p>
      </div>
    );
  }

  return <Navigate to={status === "authenticated" ? "/app/overview" : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="/app/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="imports" element={<ImportsPage />} />
          <Route path="imports/:importId/review" element={<ImportReviewPage />} />
          <Route path="imports/:importId/report" element={<ImportReportPage />} />
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="settings/users" element={<UserSettingsPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
