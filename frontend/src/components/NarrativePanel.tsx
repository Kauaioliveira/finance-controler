import { formatCurrency, formatDate } from "../lib/formatters";
import type { FinanceInsight, FinancePersistedTransaction } from "../types";

type NarrativePanelProps = {
  narrative: string;
  insights: FinanceInsight[];
  topTransactions: FinancePersistedTransaction[];
};

export function NarrativePanel({
  narrative,
  insights,
  topTransactions,
}: NarrativePanelProps) {
  return (
    <section className="panel panel-story">
      <div className="panel-kicker">Relatorio executivo</div>
      <div className="panel-header">
        <div>
          <h2>Leitura pronta para o time financeiro</h2>
          <p>
            Um resumo curto para reuniao, seguido dos gastos que mais merecem
            atencao humana.
          </p>
        </div>
      </div>

      <p className="narrative-copy">{narrative}</p>

      <div className="insight-grid">
        {insights.map((item) => (
          <article key={item.title} className={`insight-card tone-${item.tone}`}>
            <strong>{item.title}</strong>
            <p>{item.detail}</p>
          </article>
        ))}
      </div>

      <div className="expense-stack">
        <h3>Maiores saidas</h3>
        <div className="expense-list">
          {topTransactions.map((item) => (
            <article key={item.id} className="expense-item">
              <div>
                <strong>{item.description}</strong>
                <span>
                  {formatDate(item.transaction_date)} · {item.final_category_label}
                </span>
              </div>
              <strong>{formatCurrency(item.amount)}</strong>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
