import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthContext";
import { api } from "../lib/api";
import { formatRoleLabel } from "../lib/formatters";
import type { ApiConfig, HealthStatus } from "../types";

import { ThemeToggle } from "./ThemeToggle";

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
      },
      {
        label: "Imports",
        to: "/app/imports",
      },
      ...(user?.role === "admin"
        ? [
            {
              label: "Usuarios",
              to: "/app/settings/users",
            },
          ]
        : []),
    ],
    [user?.role],
  );

  const currentPageLabel = useMemo(() => {
    const match = navItems.find((item) => location.pathname.startsWith(item.to));
    return match?.label ?? "Overview";
  }, [location.pathname, navItems]);

  return (
    <div className="workspace-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <h1>Finance Controler</h1>
          <p>Operacao financeira interna</p>
        </div>

        <nav className="side-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "side-link side-link-active" : "side-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="operator-card">
            <span className="panel-kicker">Operador atual</span>
            <strong>{user?.name}</strong>
            <small>
              {formatRoleLabel(user?.role ?? "")} · {user?.company.name}
            </small>
          </div>

          <button className="ghost-button" type="button" onClick={() => void logout()}>
            Encerrar sessao
          </button>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="topbar">
          <div>
            <h2>{currentPageLabel}</h2>
            <p>{user?.company.name}</p>
          </div>

          <div className="status-cluster">
            <article className="status-card compact">
              <span>Backend</span>
              <strong>{shellState.health?.status ?? "..."}</strong>
              <small>{shellState.health?.detail ?? "Aguardando healthcheck"}</small>
            </article>
            <article className="status-card compact">
              <span>Modelo</span>
              <strong>{shellState.config?.model ?? "..."}</strong>
              <small>{shellState.config?.demo_mode ? "Demo mode" : "OpenAI ativa"}</small>
            </article>
            <article className="status-card compact">
              <span>Banco</span>
              <strong>{shellState.config?.database_ready ? "Pronto" : "Pendente"}</strong>
              <small>
                {shellState.config?.supported_finance_extensions.join(", ") ?? "carregando"}
              </small>
            </article>

            <ThemeToggle />
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
