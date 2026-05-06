import { formatCurrency, formatPercent } from "../lib/formatters";
import type { FinanceCategoryBreakdown } from "../types";

type CategoryBreakdownProps = {
  categories: FinanceCategoryBreakdown[];
};

export function CategoryBreakdown({ categories }: CategoryBreakdownProps) {
  return (
    <section className="panel">
      <div className="panel-kicker">Mapa de categorias</div>
      <div className="panel-header">
        <div>
          <h2>Onde o caixa esta concentrado</h2>
          <p>
            Priorize revisao nas faixas com maior participacao para acelerar a
            leitura financeira do periodo.
          </p>
        </div>
      </div>

      <div className="category-list">
        {categories.map((item) => (
          <article key={item.category} className="category-item">
            <div className="category-main">
              <div>
                <strong>{item.label}</strong>
                <span>
                  {item.transaction_count} transacoes · {formatCurrency(item.total_amount)}
                </span>
              </div>
              <div className="category-metrics">
                <span>{item.direction === "expense" ? formatPercent(item.share) : "Receita"}</span>
                <span>{formatCurrency(item.net_amount)}</span>
              </div>
            </div>
            <div className="category-bar">
              <div
                className={`category-fill direction-${item.direction}`}
                style={{
                  width: `${Math.max(6, item.direction === "expense" ? item.share * 100 : 28)}%`,
                }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
