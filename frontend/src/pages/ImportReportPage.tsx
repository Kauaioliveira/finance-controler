import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CategoryBreakdown } from "../components/CategoryBreakdown";
import { MonthlyPulse } from "../components/MonthlyPulse";
import { NarrativePanel } from "../components/NarrativePanel";
import { SummaryStrip } from "../components/SummaryStrip";
import { TransactionTable } from "../components/TransactionTable";
import { api } from "../lib/api";
import { formatDateTime, formatImportStatus } from "../lib/formatters";
import type { FinanceImportResponse, FinanceReportResponse } from "../types";

type ReportState = {
  importItem: FinanceImportResponse | null;
  report: FinanceReportResponse | null;
  loading: boolean;
  finalizing: boolean;
  error: string | null;
};

export function ImportReportPage() {
  const { importId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<ReportState>({
    importItem: null,
    report: null,
    loading: true,
    finalizing: false,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadReport() {
      try {
        const [importItem, report] = await Promise.all([
          api.getFinanceImport(importId),
          api.getFinanceReport(importId),
        ]);
        if (cancelled) {
          return;
        }
        setState({
          importItem,
          report,
          loading: false,
          finalizing: false,
          error: null,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setState({
          importItem: null,
          report: null,
          loading: false,
          finalizing: false,
          error: error instanceof Error ? error.message : "Falha ao carregar relatorio.",
        });
      }
    }

    loadReport();

    return () => {
      cancelled = true;
    };
  }, [importId]);

  async function handleFinalize() {
    setState((current) => ({
      ...current,
      finalizing: true,
      error: null,
    }));
    try {
      await api.finalizeFinanceImport(importId);
      const importItem = await api.getFinanceImport(importId);
      setState((current) => ({
        ...current,
        importItem,
        finalizing: false,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        finalizing: false,
        error: error instanceof Error ? error.message : "Falha ao finalizar relatorio.",
      }));
    }
  }

  if (state.loading) {
    return (
      <div className="screen-state">
        <div className="loading-pulse" />
        <strong>Montando snapshot persistido...</strong>
        <p>Estamos carregando os dados finais do relatorio financeiro.</p>
      </div>
    );
  }

  if (!state.importItem || !state.report) {
    return (
      <div className="empty-panel">
        <strong>Relatorio indisponivel</strong>
        <p>Verifique se a importacao ainda esta sendo processada.</p>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">Snapshot persistido</div>
            <h2>{state.importItem.filename}</h2>
            <p>
              Gerado em {formatDateTime(state.report.generated_at)} · status{" "}
              <span className={`status-pill status-${state.importItem.status}`}>
                {formatImportStatus(state.importItem.status)}
              </span>
            </p>
          </div>

          <div className="card-actions">
            <Link className="ghost-button link-button" to={`/app/imports/${importId}/review`}>
              Voltar para revisao
            </Link>
            <button
              className="primary-button"
              type="button"
              disabled={state.importItem.status === "finalized" || state.finalizing}
              onClick={() => void handleFinalize()}
            >
              {state.importItem.status === "finalized"
                ? "Snapshot finalizado"
                : state.finalizing
                  ? "Finalizando..."
                  : "Finalizar agora"}
            </button>
          </div>
        </div>
      </section>

      {state.error ? <div className="alert-banner">{state.error}</div> : null}

      <SummaryStrip summary={state.report.summary} />

      <div className="content-grid">
        <CategoryBreakdown categories={state.report.categories} />
        <NarrativePanel
          narrative={state.report.narrative}
          insights={state.report.insights}
          topTransactions={state.report.top_transactions}
        />
      </div>

      <MonthlyPulse monthly={state.report.monthly} />

      <TransactionTable
        transactions={state.report.top_transactions}
        title="Maiores saidas persistidas"
        copy="Esses movimentos ficaram salvos no snapshot mais recente para referencia do time."
      />

      <div className="card-actions">
        <button className="ghost-button" type="button" onClick={() => navigate("/app/imports")}>
          Voltar para imports
        </button>
      </div>
    </div>
  );
}
