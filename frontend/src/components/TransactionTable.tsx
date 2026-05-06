import { formatCurrency, formatDate } from "../lib/formatters";
import type { FinancePersistedTransaction } from "../types";

type TransactionTableProps = {
  transactions: FinancePersistedTransaction[];
  title?: string;
  copy?: string;
};

export function TransactionTable({
  transactions,
  title = "Movimentacoes relevantes",
  copy = "Uma visao consolidada das transacoes persistidas para auditoria rapida.",
}: TransactionTableProps) {
  return (
    <section className="panel panel-table">
      <div className="panel-kicker">Transacoes</div>
      <div className="panel-header panel-header-tight">
        <div>
          <h2>{title}</h2>
          <p>{copy}</p>
        </div>
      </div>

      <div className="transaction-table">
        <div className="table-row table-head">
          <span>Data</span>
          <span>Descricao</span>
          <span>Categoria final</span>
          <span>Confianca</span>
          <span>Valor</span>
        </div>

        {transactions.map((item) => (
          <div key={item.id} className="table-row">
            <span>{formatDate(item.transaction_date)}</span>
            <span>
              <strong>{item.description}</strong>
              {item.review_notes ? <small>{item.review_notes}</small> : null}
            </span>
            <span>{item.final_category_label}</span>
            <span>{Math.round(item.category_confidence * 100)}%</span>
            <span className={item.direction === "expense" ? "amount-expense" : "amount-income"}>
              {item.direction === "expense" ? "-" : "+"}
              {formatCurrency(item.amount)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
