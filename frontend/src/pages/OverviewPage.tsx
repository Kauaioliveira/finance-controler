import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import { formatCurrency, formatDateTime, formatImportStatus } from "../lib/formatters";
import type { FinanceImportResponse, FinanceSummary } from "../types";

type OverviewState = {
  imports: FinanceImportResponse[];
  loading: boolean;
  error: string | null;
};

const EMPTY_SUMMARY: FinanceSummary = {
  total_income: 0,
  total_expenses: 0,
  net_balance: 0,
  transaction_count: 0,
  categorized_count: 0,
  uncategorized_count: 0,
};

export function OverviewPage() {
  const [state, setState] = useState<OverviewState>({
    imports: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      try {
        const payload = await api.listFinanceImports({
          page: 1,
          pageSize: 6,
        });
        if (cancelled) {
          return;
        }
        setState({
          imports: payload.items,
          loading: false,
          error: null,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState({
          imports: [],
          loading: false,
          error: error instanceof Error ? error.message : "Falha ao carregar overview.",
        });
      }
    }

    loadOverview();

    return () => {
      cancelled = true;
    };
  }, []);

  const summary = useMemo(() => {
    return state.imports.reduce<FinanceSummary>((accumulator, item) => {
      const current = item.summary_preview?.summary;
      if (!current) {
        return accumulator;
      }
      return {
        total_income: accumulator.total_income + current.total_income,
        total_expenses: accumulator.total_expenses + current.total_expenses,
        net_balance: accumulator.net_balance + current.net_balance,
        transaction_count: accumulator.transaction_count + current.transaction_count,
        categorized_count: accumulator.categorized_count + current.categorized_count,
        uncategorized_count: accumulator.uncategorized_count + current.uncategorized_count,
      };
    }, EMPTY_SUMMARY);
  }, [state.imports]);

  const importsInReview = state.imports.filter((item) => item.status === "in_review").length;
  const finalizedImports = state.imports.filter((item) => item.status === "finalized").length;

  return (
    <div className="page-grid">
      <section className="page-hero panel">
        <div>
          <span className="eyebrow">Overview</span>
          <h3>Panorama rapido das ultimas importacoes processadas.</h3>
          <p>
            Use esta tela para entender volume, itens pendentes e quais cargas
            ja viraram relatorio oficial.
          </p>
        </div>

        <div className="hero-metrics">
          <article className="metric-tile">
            <span>Saldo consolidado</span>
            <strong>{formatCurrency(summary.net_balance)}</strong>
            <small>Somando previews recentes</small>
          </article>
          <article className="metric-tile">
            <span>Transacoes</span>
            <strong>{summary.transaction_count}</strong>
            <small>Total processado nas cargas visiveis</small>
          </article>
          <article className="metric-tile">
            <span>Em revisao</span>
            <strong>{importsInReview}</strong>
            <small>Fluxos aguardando fechamento</small>
          </article>
          <article className="metric-tile">
            <span>Finalizadas</span>
            <strong>{finalizedImports}</strong>
            <small>Snapshots ja carimbados</small>
          </article>
        </div>
      </section>

      {state.error ? <div className="alert-banner">{state.error}</div> : null}

      <section className="panel">
        <div className="panel-header panel-header-tight">
          <div>
            <div className="panel-kicker">Fila recente</div>
            <h2>Ultimas importacoes</h2>
            <p>Abra uma revisao pendente ou navegue direto para o relatorio persistido.</p>
          </div>
          <Link className="ghost-button link-button" to="/app/imports">
            Ver todas as importacoes
          </Link>
        </div>

        {state.loading ? (
          <div className="screen-state compact">
            <div className="loading-pulse" />
            <strong>Carregando overview...</strong>
          </div>
        ) : state.imports.length === 0 ? (
          <div className="empty-panel">
            <strong>Nenhuma importacao ainda</strong>
            <p>Comece pela tela de imports para subir o primeiro CSV financeiro.</p>
          </div>
        ) : (
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

                <div className="import-card-body">
                  <span>{item.processed_rows} linhas processadas</span>
                  <span>
                    {item.summary_preview?.summary
                      ? formatCurrency(item.summary_preview.summary.net_balance)
                      : "Sem preview"}
                  </span>
                </div>

                <div className="card-actions">
                  <Link className="ghost-button link-button" to={`/app/imports/${item.id}/review`}>
                    Abrir revisao
                  </Link>
                  <Link className="primary-button link-button" to={`/app/imports/${item.id}/report`}>
                    Ver relatorio
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
