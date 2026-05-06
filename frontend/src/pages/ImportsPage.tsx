import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { UploadPanel } from "../components/UploadPanel";
import { api } from "../lib/api";
import { formatDateTime, formatImportStatus } from "../lib/formatters";
import type { ApiConfig, FinanceImportResponse, FinanceImportStatus } from "../types";

type ImportsState = {
  config: ApiConfig | null;
  imports: FinanceImportResponse[];
  statusFilter: FinanceImportStatus | "all";
  page: number;
  total: number;
  loading: boolean;
  uploading: boolean;
  error: string | null;
};

export function ImportsPage() {
  const navigate = useNavigate();
  const [state, setState] = useState<ImportsState>({
    config: null,
    imports: [],
    statusFilter: "all",
    page: 1,
    total: 0,
    loading: true,
    uploading: false,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadPage() {
      try {
        const [config, imports] = await Promise.all([
          state.config ? Promise.resolve(state.config) : api.getConfig(),
          api.listFinanceImports({
            page: state.page,
            pageSize: 8,
            status: state.statusFilter === "all" ? undefined : state.statusFilter,
          }),
        ]);
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          config,
          imports: imports.items,
          total: imports.total,
          loading: false,
          error: null,
        }));
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          loading: false,
          error: error instanceof Error ? error.message : "Falha ao carregar imports.",
        }));
      }
    }

    loadPage();

    return () => {
      cancelled = true;
    };
  }, [state.page, state.statusFilter, state.config]);

  async function handleImport(file: File) {
    setState((current) => ({
      ...current,
      uploading: true,
      error: null,
    }));
    try {
      const created = await api.createFinanceImport(file);
      navigate(`/app/imports/${created.id}/review`);
    } catch (error) {
      setState((current) => ({
        ...current,
        uploading: false,
        error: error instanceof Error ? error.message : "Falha ao importar CSV.",
      }));
      return;
    }
  }

  return (
    <div className="page-grid">
      <UploadPanel
        onImport={handleImport}
        loading={state.uploading}
        maxUploadSizeMb={state.config?.max_upload_size_mb ?? 10}
      />

      {state.error ? <div className="alert-banner">{state.error}</div> : null}

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">Historico persistido</div>
            <h2>Lista de importacoes financeiras</h2>
            <p>
              Filtre por status para acompanhar uploads recem processados, cargas
              em revisao e relatorios ja finalizados.
            </p>
          </div>

          <select
            className="toolbar-select filter-select"
            value={state.statusFilter}
            onChange={(event) =>
              setState((current) => ({
                ...current,
                statusFilter: event.target.value as ImportsState["statusFilter"],
                page: 1,
              }))
            }
          >
            <option value="all">Todos os status</option>
            {(state.config?.finance_statuses ?? []).map((status) => (
              <option key={status} value={status}>
                {formatImportStatus(status)}
              </option>
            ))}
          </select>
        </div>

        {state.loading ? (
          <div className="screen-state compact">
            <div className="loading-pulse" />
            <strong>Carregando fila de importacoes...</strong>
          </div>
        ) : state.imports.length === 0 ? (
          <div className="empty-panel">
            <strong>Nenhuma importacao nesse filtro</strong>
            <p>Altere o status ou envie um novo CSV para iniciar a operacao.</p>
          </div>
        ) : (
          <>
            <div className="import-list">
              {state.imports.map((item) => (
                <article key={item.id} className="import-card">
                  <div className="import-card-head">
                    <div>
                      <strong>{item.filename}</strong>
                      <small>
                        {formatDateTime(item.created_at)} · {item.uploaded_by_user_name ?? item.uploaded_by_user_id}
                      </small>
                    </div>
                    <span className={`status-pill status-${item.status}`}>
                      {formatImportStatus(item.status)}
                    </span>
                  </div>

                  <div className="import-card-body import-card-grid">
                    <span>Total de linhas: {item.total_rows}</span>
                    <span>Processadas: {item.processed_rows}</span>
                    <span>
                      Sem categoria: {item.summary_preview?.summary?.uncategorized_count ?? "--"}
                    </span>
                    <span>
                      Saldo:{" "}
                      {item.summary_preview?.summary
                        ? item.summary_preview.summary.net_balance.toLocaleString("pt-BR", {
                            style: "currency",
                            currency: item.currency,
                          })
                        : "--"}
                    </span>
                  </div>

                  {item.error_message ? <div className="alert-banner">{item.error_message}</div> : null}

                  <div className="card-actions">
                    <Link className="ghost-button link-button" to={`/app/imports/${item.id}/review`}>
                      Revisar
                    </Link>
                    <Link className="primary-button link-button" to={`/app/imports/${item.id}/report`}>
                      Relatorio
                    </Link>
                  </div>
                </article>
              ))}
            </div>

            <div className="pagination-row">
              <button
                className="ghost-button"
                type="button"
                disabled={state.page === 1}
                onClick={() =>
                  setState((current) => ({
                    ...current,
                    page: Math.max(1, current.page - 1),
                  }))
                }
              >
                Pagina anterior
              </button>
              <span>
                Pagina {state.page} · {state.total} itens
              </span>
              <button
                className="ghost-button"
                type="button"
                disabled={state.page * 8 >= state.total}
                onClick={() =>
                  setState((current) => ({
                    ...current,
                    page: current.page + 1,
                  }))
                }
              >
                Proxima pagina
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
