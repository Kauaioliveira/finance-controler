import { type FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Database,
  Lock,
  Mail,
  ShieldCheck,
  Terminal,
  Users,
  Wallet,
} from "lucide-react";

import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { status, login, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const target = (location.state as { from?: string } | null)?.from ?? "/app/overview";

  if (status === "authenticated") {
    return <Navigate to={target} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(target, { replace: true });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-copy">
        <div className="auth-brand">
          <Wallet aria-hidden="true" />
          FINANCE CONTROLER
        </div>

        <div className="auth-copy-main">
          <span className="eyebrow">
            <Terminal aria-hidden="true" />
            operacao financeira interna
          </span>
          <h1>Cockpit financeiro para importar, revisar e reportar com precisao</h1>
          <p>
            Importe extratos em CSV, deixe o modelo pre-categorizar, revise antes de
            fechar e mantenha snapshots persistidos de cada relatorio.
          </p>

          <div className="auth-badges">
            <span>
              <ShieldCheck aria-hidden="true" />
              JWT + refresh
            </span>
            <span>
              <Users aria-hidden="true" />
              RBAC por papel
            </span>
            <span>
              <Database aria-hidden="true" />
              PostgreSQL persistido
            </span>
          </div>
        </div>

        <div className="auth-footnote">operacao interna · acesso restrito</div>
      </div>

      <div className="auth-form">
        <form onSubmit={handleSubmit}>
          <div>
            <div className="panel-kicker">login interno</div>
            <h2>Acesse com email e senha</h2>
          </div>

          <label className="field-stack">
            <span>
              <Mail aria-hidden="true" />
              Email
            </span>
            <input
              className="toolbar-input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="username"
              placeholder="voce@empresa.com"
            />
          </label>

          <label className="field-stack">
            <span>
              <Lock aria-hidden="true" />
              Senha
            </span>
            <input
              className="toolbar-input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>

          {error ? <div className="alert-banner">{error}</div> : null}

          <button className="primary-button auth-submit" type="submit" disabled={submitting}>
            {submitting ? "Entrando..." : "Entrar"}
            {submitting ? null : <ArrowRight aria-hidden="true" />}
          </button>

          <small className="helper-copy">
            Use as credenciais liberadas pelo administrador do ambiente.
          </small>
        </form>
      </div>
    </div>
  );
}
