import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { CircleDot, Gauge, Upload, Users, Wallet } from "lucide-react";

import { useAuth } from "../auth/AuthContext";
import { api } from "../lib/api";
import { formatRoleLabel } from "../lib/formatters";
import type { ApiConfig, HealthStatus } from "../types";

type ShellState = {
  health: HealthStatus | null;
  config: ApiConfig | null;
  error: string | null;
};

const INITIAL_STATE: ShellState = {
  health: null,
  config: null,
  error: null,
};

function initials(name: string | undefined) {
  if (!name) {
    return "--";
  }
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [shellState, setShellState] = useState<ShellState>(INITIAL_STATE);

  useEffect(() => {
    let cancelled = false;

    async function loadShell() {
      try {
        const [health, config] = await Promise.all([api.getHealth(), api.getConfig()]);
        if (cancelled) {
          return;
        }
        setShellState({
          health,
          config,
          error: null,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setShellState({
          health: null,
          config: null,
          error: error instanceof Error ? error.message : "Falha ao carregar shell.",
        });
      }
    }

    loadShell();

    return () => {
      cancelled = true;
    };
  }, []);

  const navItems = useMemo(
    () => [
      {
        label: "Overview",
        to: "/app/overview",
        Icon: Gauge,
      },
      {
        label: "Imports",
        to: "/app/imports",
        Icon: Upload,
      },
      ...(user?.role === "admin"
        ? [
            {
              label: "Usuarios",
              to: "/app/settings/users",
              Icon: Users,
            },
          ]
        : []),
    ],
    [user?.role],
  );

  const currentPageLabel = useMemo(() => {
    const match = navItems.find((item) => location.pathname.startsWith(item.to));
    return (match?.label ?? "Overview").toUpperCase();
  }, [location.pathname, navItems]);

  const online = shellState.health?.status === "ok";

  return (
    <div className="workspace-shell">
      <aside className="rail">
        <div className="rail-brand" aria-hidden="true">
          <Wallet size={18} />
        </div>

        <nav className="rail-nav" aria-label="Navegacao principal">
          {navItems.map(({ label, to, Icon }) => (
            <NavLink
              key={to}
              to={to}
              title={label}
              aria-label={label}
              className={({ isActive }) => (isActive ? "rail-link rail-link-active" : "rail-link")}
            >
              <Icon size={18} aria-hidden="true" />
            </NavLink>
          ))}
        </nav>

        <div className="rail-spacer" />

        <button
          className="rail-logout"
          type="button"
          onClick={() => void logout()}
          title={`Encerrar sessao — ${user?.name ?? ""}`}
          aria-label="Encerrar sessao"
        >
          {initials(user?.name)}
        </button>
      </aside>

      <div className="workspace-main">
        <header className="topbar">
          <span className="breadcrumb">
            FINANCE / <strong>{currentPageLabel}</strong>
          </span>

          <div className="status-cluster">
            <span className={online ? "status-card status-online" : "status-card status-offline"}>
              <CircleDot size={11} aria-hidden="true" />
              {online ? "conectado" : "sem conexao"}
            </span>
            <span className="status-card">{shellState.config?.model ?? "..."}</span>
            <span className="status-card">{user?.company.name}</span>
            <span className="status-card">{formatRoleLabel(user?.role ?? "")}</span>
          </div>
        </header>

        {shellState.error ? <div className="alert-banner">{shellState.error}</div> : null}

        <main className="workspace-stage">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
