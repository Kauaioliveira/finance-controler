import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Clock,
  FileSpreadsheet,
  Hash,
  Layers,
  List,
  Wallet,
} from "lucide-react";

import { ImportsChart } from "../components/ImportsChart";
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
      <section className="page-hero">
        <div className="panel-kicker">
          <Wallet aria-hidden="true" />
          saldo consolidado
        </div>
        <div className={summary.net_balance < 0 ? "hero-value amount-expense" : "hero-value"}>
          {formatCurrency(summary.net_balance)}
        </div>
        <div className="hero-delta">
          <Layers aria-hidden="true" />
          {state.imports.length} importacoes visiveis · {finalizedImports} finalizadas
        </div>

        <div className="hero-metrics">
          <article className="metric-tile tone-positive">
            <span>
              <ArrowDownLeft aria-hidden="true" />
              entradas
            </span>
            <strong>{formatCurrency(summary.total_income)}</strong>
          </article>
          <article className="metric-tile tone-warning">
            <span>
              <ArrowUpRight aria-hidden="true" />
              saidas
            </span>
            <strong>{formatCurrency(summary.total_expenses)}</strong>
          </article>
          <article className="metric-tile">
            <span>
              <Hash aria-hidden="true" />
              transacoes
            </span>
            <strong>{summary.transaction_count}</strong>
          </article>
          <article className="metric-tile tone-review">
            <span>
              <Clock aria-hidden="true" />
              em revisao
            </span>
            <strong>{importsInReview}</strong>
          </article>
        </div>
      </section>

      {state.error ? <div className="alert-banner">{state.error}</div> : null}

      <ImportsChart imports={state.imports} />

      <section className="panel">
        <div className="panel-header panel-header-tight">
          <div>
            <div className="panel-kicker">
              <List aria-hidden="true" />
              fila recente
            </div>
            <h2>Ultimas importacoes</h2>
            <p>Abra uma revisao pendente ou navegue direto para o relatorio persistido.</p>
          </div>
          <Link className="ghost-button link-button" to="/app/imports">
            Ver todas
            <ArrowRight aria-hidden="true" />
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
                    <strong>
                      <FileSpreadsheet size={14} aria-hidden="true" /> {item.filename}
                    </strong>
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
                    Revisar
                  </Link>
                  <Link className="accent-button link-button" to={`/app/imports/${item.id}/report`}>
                    Relatorio
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
