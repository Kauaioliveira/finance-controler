import { formatCurrency } from "../lib/formatters";
import type { FinanceMonthlySummary } from "../types";
import { Activity } from "lucide-react";

type MonthlyPulseProps = {
  monthly: FinanceMonthlySummary[];
};

export function MonthlyPulse({ monthly }: MonthlyPulseProps) {
  return (
    <section className="panel">
      <div className="panel-kicker">
        <Activity aria-hidden="true" />
        ritmo mensal
      </div>
      <div className="panel-header">
        <div>
          <h2>Batimento das entradas e saidas</h2>
          <p>
            Uma leitura rapida do periodo ajuda a localizar oscilacoes antes da
            reuniao financeira.
          </p>
        </div>
      </div>

      <div className="month-grid">
        {monthly.map((item) => (
          <article key={item.month} className="month-card">
            <span>{item.month}</span>
            <strong>{formatCurrency(item.net)}</strong>
            <div>
              <small>Entradas {formatCurrency(item.income)}</small>
              <small>Saidas {formatCurrency(item.expenses)}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
