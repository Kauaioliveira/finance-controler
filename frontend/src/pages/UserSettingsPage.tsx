import { useEffect, useMemo, useState } from "react";

import { api } from "../lib/api";
import { formatRoleLabel } from "../lib/formatters";
import { useAuth } from "../auth/AuthContext";
import type { Role, UserResponse } from "../types";

type UserDraftState = Record<
  string,
  {
    name: string;
    role: Role;
    password: string;
  }
>;

export function UserSettingsPage() {
  const { replaceSessionUser, user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [drafts, setDrafts] = useState<UserDraftState>({});
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    role: "viewer" as Role,
    password: "",
  });

  async function loadUsers() {
    setLoading(true);
    try {
      const payload = await api.listUsers(1, 50);
      setUsers(payload.items);
      setError(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao carregar usuarios.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  useEffect(() => {
    setDrafts((current) => {
      const next: UserDraftState = {};
      for (const item of users) {
        next[item.id] = current[item.id] ?? {
          name: item.name,
          role: item.role,
          password: "",
        };
      }
      return next;
    });
  }, [users]);

  const roleOptions = useMemo(() => ["admin", "analyst", "viewer"] as Role[], []);

  async function handleCreateUser() {
    setSavingId("create");
    setError(null);
    try {
      await api.createUser(form);
      setForm({
        name: "",
        email: "",
        role: "viewer",
        password: "",
      });
      await loadUsers();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao criar usuario.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleSaveUser(userItem: UserResponse) {
    const draft = drafts[userItem.id];
    if (!draft) {
      return;
    }
    setSavingId(userItem.id);
    setError(null);
    try {
      const updated = await api.updateUser(userItem.id, {
        name: draft.name,
        role: draft.role,
      });
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      if (currentUser?.id === updated.id) {
        replaceSessionUser({
          ...currentUser,
          name: updated.name,
          role: updated.role,
        });
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao salvar usuario.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleToggleStatus(userItem: UserResponse) {
    setSavingId(`status:${userItem.id}`);
    setError(null);
    try {
      const updated = await api.updateUserStatus(userItem.id, !userItem.is_active);
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao atualizar status.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleResetPassword(userItem: UserResponse) {
    const draft = drafts[userItem.id];
    if (!draft?.password.trim()) {
      setError("Preencha uma nova senha antes de enviar.");
      return;
    }
    setSavingId(`password:${userItem.id}`);
    setError(null);
    try {
      await api.updateUserPassword(userItem.id, draft.password.trim());
      setDrafts((current) => ({
        ...current,
        [userItem.id]: {
          ...current[userItem.id],
          password: "",
        },
      }));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao redefinir senha.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">Administracao</div>
            <h2>Gestao basica de usuarios</h2>
            <p>
              Crie acessos para admin, analyst e viewer, ajuste papeis e
              redefina senhas sem sair do cockpit.
            </p>
          </div>
        </div>

        <div className="form-grid">
          <label className="field-stack">
            <span>Nome</span>
            <input
              className="toolbar-input"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            />
          </label>
          <label className="field-stack">
            <span>Email</span>
            <input
              className="toolbar-input"
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            />
          </label>
          <label className="field-stack">
            <span>Papel</span>
            <select
              className="toolbar-select"
              value={form.role}
              onChange={(event) =>
                setForm((current) => ({ ...current, role: event.target.value as Role }))
              }
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {formatRoleLabel(role)}
                </option>
              ))}
            </select>
          </label>
          <label className="field-stack">
            <span>Senha inicial</span>
            <input
              className="toolbar-input"
              type="password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            />
          </label>
        </div>

        <div className="card-actions">
          <button
            className="primary-button"
            type="button"
            disabled={savingId === "create"}
            onClick={() => void handleCreateUser()}
          >
            {savingId === "create" ? "Criando..." : "Criar usuario"}
          </button>
        </div>
      </section>

      {error ? <div className="alert-banner">{error}</div> : null}

      <section className="panel">
        <div className="panel-header panel-header-tight">
          <div>
            <div className="panel-kicker">Equipe interna</div>
            <h2>Usuarios ativos e perfis de acesso</h2>
          </div>
        </div>

        {loading ? (
          <div className="screen-state compact">
            <div className="loading-pulse" />
            <strong>Carregando usuarios...</strong>
          </div>
        ) : (
          <div className="user-list">
            {users.map((item) => {
              const draft = drafts[item.id] ?? {
                name: item.name,
                role: item.role,
                password: "",
              };
              return (
                <article key={item.id} className="user-card">
                  <div className="user-card-head">
                    <div>
                      <strong>{item.email}</strong>
                      <small>{item.company.name}</small>
                    </div>
                    <span className={`status-pill ${item.is_active ? "status-processed" : "status-failed"}`}>
                      {item.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </div>

                  <div className="user-card-grid">
                    <label className="field-stack">
                      <span>Nome</span>
                      <input
                        className="toolbar-input"
                        value={draft.name}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [item.id]: {
                              ...draft,
                              name: event.target.value,
                            },
                          }))
                        }
                      />
                    </label>

                    <label className="field-stack">
                      <span>Papel</span>
                      <select
                        className="toolbar-select"
                        value={draft.role}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [item.id]: {
                              ...draft,
                              role: event.target.value as Role,
                            },
                          }))
                        }
                      >
                        {roleOptions.map((role) => (
                          <option key={role} value={role}>
                            {formatRoleLabel(role)}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field-stack">
                      <span>Nova senha</span>
                      <input
                        className="toolbar-input"
                        type="password"
                        value={draft.password}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [item.id]: {
                              ...draft,
                              password: event.target.value,
                            },
                          }))
                        }
                        placeholder="Opcional"
                      />
                    </label>
                  </div>

                  <div className="card-actions">
                    <button
                      className="ghost-button"
                      type="button"
                      disabled={savingId === item.id}
                      onClick={() => void handleSaveUser(item)}
                    >
                      {savingId === item.id ? "Salvando..." : "Salvar perfil"}
                    </button>
                    <button
                      className="ghost-button"
                      type="button"
                      disabled={savingId === `password:${item.id}`}
                      onClick={() => void handleResetPassword(item)}
                    >
                      {savingId === `password:${item.id}` ? "Enviando..." : "Atualizar senha"}
                    </button>
                    <button
                      className="primary-button"
                      type="button"
                      disabled={savingId === `status:${item.id}`}
                      onClick={() => void handleToggleStatus(item)}
                    >
                      {savingId === `status:${item.id}`
                        ? "Atualizando..."
                        : item.is_active
                          ? "Desativar"
                          : "Ativar"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
