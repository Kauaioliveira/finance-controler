import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

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

export function AppLayout() {
  const { user, logout } = useAuth();
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

  return (
    <div className="workspace-shell">
      <div className="background-grid" />

      <aside className="sidebar">
        <div className="brand-block">
          <span className="eyebrow">Finance Controler</span>
          <h1>Cockpit financeiro para operacao interna.</h1>
          <p>
            Upload, revisao humana, snapshots persistidos e leitura pronta para o
            fechamento.
          </p>
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
            <span className="eyebrow">Operacao</span>
            <h2>Mesa financeira autenticada e pronta para revisao.</h2>
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
