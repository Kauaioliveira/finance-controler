import { type FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { status, login, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("admin@finance-controler.local");
  const [password, setPassword] = useState("Admin123!");
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
      <div className="background-grid" />
      <section className="auth-panel">
        <div className="auth-copy">
          <span className="eyebrow">Finance Controler</span>
          <h1>Entre na mesa operacional financeira.</h1>
          <p>
            A aplicacao agora exige autenticacao, separa papeis por RBAC e
            persiste importacoes, revisoes e snapshots de relatorio.
          </p>

          <div className="auth-badges">
            <span>JWT + refresh rotativo</span>
            <span>RBAC por papel</span>
            <span>PostgreSQL persistido</span>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="panel-kicker">Login interno</div>
          <h2>Acesse com email e senha</h2>
          <p>
            O seed inicial cria um admin para bootstrap. Depois, a gestao passa
            para a tela de usuarios.
          </p>

          <label className="field-stack">
            <span>Email</span>
            <input
              className="toolbar-input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="username"
            />
          </label>

          <label className="field-stack">
            <span>Senha</span>
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
            {submitting ? "Entrando..." : "Entrar no cockpit"}
          </button>

          <small className="helper-copy">
            Sugestao local de estudo: admin@finance-controler.local / Admin123!
          </small>
        </form>
      </section>
    </div>
  );
}
