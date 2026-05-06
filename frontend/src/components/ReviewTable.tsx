import { useEffect, useMemo, useState } from "react";

import { formatCurrency, formatDate } from "../lib/formatters";
import type { FinanceCategoryCatalogItem, FinancePersistedTransaction } from "../types";

type DraftState = Record<
  string,
  {
    finalCategory: string;
    reviewNotes: string;
  }
>;

type ReviewTableProps = {
  transactions: FinancePersistedTransaction[];
  categories: FinanceCategoryCatalogItem[];
  savingId: string | null;
  onSave: (transactionId: string, finalCategory: string, reviewNotes: string) => Promise<void>;
};

export function ReviewTable({
  transactions,
  categories,
  savingId,
  onSave,
}: ReviewTableProps) {
  const [drafts, setDrafts] = useState<DraftState>({});

  useEffect(() => {
    setDrafts((current) => {
      const next: DraftState = {};
      for (const item of transactions) {
        next[item.id] = current[item.id] ?? {
          finalCategory: item.final_category,
          reviewNotes: item.review_notes ?? "",
        };
      }
      return next;
    });
  }, [transactions]);

  const categoryMap = useMemo(
    () => new Map(categories.map((item) => [item.key, item.label])),
    [categories],
  );

  return (
    <section className="panel panel-table">
      <div className="panel-kicker">Revisao assistida</div>
      <div className="panel-header panel-header-tight">
        <div>
          <h2>Edite a categoria final antes do fechamento</h2>
          <p>
            A previsao da IA continua registrada, mas o analista define a
            classificacao oficial para snapshot e historico.
          </p>
        </div>
      </div>

      <div className="review-table">
        <div className="review-head">
          <span>Movimento</span>
          <span>Previsao</span>
          <span>Categoria final</span>
          <span>Observacao</span>
          <span>Acoes</span>
        </div>

        {transactions.map((item) => {
          const draft = drafts[item.id] ?? {
            finalCategory: item.final_category,
            reviewNotes: item.review_notes ?? "",
          };

          const dirty =
            draft.finalCategory !== item.final_category ||
            draft.reviewNotes !== (item.review_notes ?? "");

          return (
            <div key={item.id} className="review-row">
              <div className="review-cell review-cell-main">
                <strong>{item.description}</strong>
                <small>
                  {formatDate(item.transaction_date)} · linha {item.row_number} ·{" "}
                  {item.direction === "expense" ? "saida" : "entrada"} ·{" "}
                  {formatCurrency(item.amount)}
                </small>
              </div>

              <div className="review-cell">
                <strong>
                  {categoryMap.get(item.predicted_category) ?? item.predicted_category_label}
                </strong>
                <small>{Math.round(item.category_confidence * 100)}% de confianca</small>
              </div>

              <div className="review-cell">
                <select
                  className="toolbar-select"
                  value={draft.finalCategory}
                  onChange={(event) =>
                    setDrafts((current) => ({
                      ...current,
                      [item.id]: {
                        ...draft,
                        finalCategory: event.target.value,
                      },
                    }))
                  }
                >
                  {categories.map((category) => (
                    <option key={category.key} value={category.key}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="review-cell">
                <input
                  className="toolbar-input"
                  value={draft.reviewNotes}
                  onChange={(event) =>
                    setDrafts((current) => ({
                      ...current,
                      [item.id]: {
                        ...draft,
                        reviewNotes: event.target.value,
                      },
                    }))
                  }
                  placeholder="Notas da revisao"
                />
              </div>

              <div className="review-cell review-actions">
                <button
                  className="primary-button"
                  type="button"
                  disabled={!dirty || savingId === item.id}
                  onClick={() => void onSave(item.id, draft.finalCategory, draft.reviewNotes)}
                >
                  {savingId === item.id ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
