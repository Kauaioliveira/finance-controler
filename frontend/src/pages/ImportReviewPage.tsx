import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ReviewTable } from "../components/ReviewTable";
import { SummaryStrip } from "../components/SummaryStrip";
import { api } from "../lib/api";
import { formatImportStatus } from "../lib/formatters";
import type {
  FinanceCategoryCatalogItem,
  FinanceImportResponse,
  FinancePersistedTransaction,
} from "../types";

type ReviewState = {
  importItem: FinanceImportResponse | null;
  transactions: FinancePersistedTransaction[];
  categories: FinanceCategoryCatalogItem[];
  loading: boolean;
  transactionsLoading: boolean;
  savingId: string | null;
  finalizing: boolean;
  categoryFilter: string;
  query: string;
  page: number;
  total: number;
  error: string | null;
};

export function ImportReviewPage() {
  const { importId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<ReviewState>({
    importItem: null,
    transactions: [],
    categories: [],
    loading: true,
    transactionsLoading: true,
    savingId: null,
    finalizing: false,
    categoryFilter: "all",
    query: "",
    page: 1,
    total: 0,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadFrame() {
      try {
        const [importItem, catalog] = await Promise.all([
          api.getFinanceImport(importId),
          api.getFinanceCategories(),
        ]);
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          importItem,
          categories: catalog.categories,
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
          error: error instanceof Error ? error.message : "Falha ao carregar importacao.",
        }));
      }
    }

    loadFrame();

    return () => {
      cancelled = true;
    };
  }, [importId]);

  useEffect(() => {
    let cancelled = false;

    async function loadTransactions() {
      try {
        const payload = await api.getFinanceTransactions(importId, {
          page: state.page,
          pageSize: 20,
          category: state.categoryFilter === "all" ? undefined : state.categoryFilter,
          query: state.query || undefined,
        });
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          transactions: payload.items,
          total: payload.total,
          transactionsLoading: false,
          error: null,
        }));
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          transactionsLoading: false,
          error: error instanceof Error ? error.message : "Falha ao carregar transacoes.",
        }));
      }
    }

    setState((current) => ({
      ...current,
      transactionsLoading: true,
    }));
    loadTransactions();

    return () => {
      cancelled = true;
    };
  }, [importId, state.page, state.categoryFilter, state.query]);

  async function reloadImport() {
    const importItem = await api.getFinanceImport(importId);
    setState((current) => ({
      ...current,
      importItem,
    }));
  }

  async function handleSave(transactionId: string, finalCategory: string, reviewNotes: string) {
    setState((current) => ({
      ...current,
      savingId: transactionId,
      error: null,
    }));
    try {
      await api.updateFinanceTransaction(importId, transactionId, {
        final_category: finalCategory,
        review_notes: reviewNotes || null,
      });
      const [transactions, importItem] = await Promise.all([
        api.getFinanceTransactions(importId, {
          page: state.page,
          pageSize: 20,
          category: state.categoryFilter === "all" ? undefined : state.categoryFilter,
          query: state.query || undefined,
        }),
        api.getFinanceImport(importId),
      ]);
      setState((current) => ({
        ...current,
        savingId: null,
        importItem,
        transactions: transactions.items,
        total: transactions.total,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        savingId: null,
        error: error instanceof Error ? error.message : "Falha ao salvar revisao.",
      }));
    }
  }

  async function handleFinalize() {
    setState((current) => ({
      ...current,
      finalizing: true,
      error: null,
    }));
    try {
      await api.finalizeFinanceImport(importId);
      navigate(`/app/imports/${importId}/report`);
    } catch (error) {
      setState((current) => ({
        ...current,
        finalizing: false,
        error: error instanceof Error ? error.message : "Falha ao finalizar importacao.",
      }));
    }
  }

  if (state.loading) {
    return (
      <div className="screen-state">
        <div className="loading-pulse" />
        <strong>Carregando mesa de revisao...</strong>
        <p>Estamos buscando importacao, categorias e status atual.</p>
      </div>
    );
  }

  if (!state.importItem) {
    return (
      <div className="empty-panel">
        <strong>Importacao nao encontrada</strong>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">Mesa de revisao</div>
            <h2>{state.importItem.filename}</h2>
            <p>
              Status atual:{" "}
              <span className={`status-pill status-${state.importItem.status}`}>
                {formatImportStatus(state.importItem.status)}
              </span>
            </p>
          </div>

          <div className="card-actions">
            <Link className="ghost-button link-button" to={`/app/imports/${importId}/report`}>
              Ver relatorio
            </Link>
            <button
              className="primary-button"
              type="button"
              disabled={state.finalizing || state.importItem.status === "finalized"}
              onClick={() => void handleFinalize()}
            >
              {state.importItem.status === "finalized"
                ? "Ja finalizado"
                : state.finalizing
                  ? "Finalizando..."
                  : "Finalizar analise"}
            </button>
          </div>
        </div>

        {state.importItem.summary_preview?.summary ? (
          <SummaryStrip summary={state.importItem.summary_preview.summary} />
        ) : null}

        <div className="review-toolbar">
          <input
            className="toolbar-input"
            value={state.query}
            onChange={(event) =>
              setState((current) => ({
                ...current,
                query: event.target.value,
                page: 1,
              }))
            }
            placeholder="Buscar por descricao"
          />

          <select
            className="toolbar-select"
            value={state.categoryFilter}
            onChange={(event) =>
              setState((current) => ({
                ...current,
                categoryFilter: event.target.value,
                page: 1,
              }))
            }
          >
            <option value="all">Todas as categorias</option>
            {state.categories.map((item) => (
              <option key={item.key} value={item.key}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {state.error ? <div className="alert-banner">{state.error}</div> : null}

      {state.transactionsLoading ? (
        <div className="screen-state compact">
          <div className="loading-pulse" />
          <strong>Carregando transacoes...</strong>
        </div>
      ) : (
        <>
          <ReviewTable
            transactions={state.transactions}
            categories={state.categories}
            savingId={state.savingId}
            onSave={handleSave}
          />

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
              Pagina {state.page} · {state.total} transacoes
            </span>
            <button
              className="ghost-button"
              type="button"
              disabled={state.page * 20 >= state.total}
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
    </div>
  );
}
