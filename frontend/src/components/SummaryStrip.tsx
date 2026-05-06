import { formatCurrency } from "../lib/formatters";
import type { FinanceSummary } from "../types";

type SummaryStripProps = {
  summary: FinanceSummary;
};

export function SummaryStrip({ summary }: SummaryStripProps) {
  const cards = [
    {
      label: "Entradas",
      value: formatCurrency(summary.total_income),
      tone: "positive",
    },
    {
      label: "Saidas",
      value: formatCurrency(summary.total_expenses),
      tone: "warning",
    },
    {
      label: "Saldo liquido",
      value: formatCurrency(summary.net_balance),
      tone: summary.net_balance >= 0 ? "positive" : "warning",
    },
    {
      label: "Transacoes",
      value: `${summary.transaction_count}`,
      tone: "neutral",
    },
  ] as const;

  return (
    <section className="summary-strip">
      {cards.map((card) => (
        <article key={card.label} className={`summary-card tone-${card.tone}`}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
        </article>
      ))}
    </section>
  );
}
