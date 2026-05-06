import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types";

type ProtectedRouteProps = {
  roles?: Role[];
};

export function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === "bootstrapping") {
    return (
      <div className="screen-state">
        <div className="loading-pulse" />
        <strong>Conectando a mesa operacional...</strong>
        <p>Estamos restaurando a sessao e preparando o ambiente.</p>
      </div>
    );
  }

  if (status !== "authenticated" || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/app/overview" replace />;
  }

  return <Outlet />;
}
