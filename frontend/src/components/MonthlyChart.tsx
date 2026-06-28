import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatCurrency } from "../lib/formatters";
import type { FinanceMonthlySummary } from "../types";

type MonthlyChartProps = {
  monthly: FinanceMonthlySummary[];
};

type TooltipPayloadEntry = {
  name: string;
  value: number;
  color: string;
};

type CustomTooltipProps = {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
};

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>
      {payload.map((entry) => (
        <div key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value)}
        </div>
      ))}
    </div>
  );
}

export function MonthlyChart({ monthly }: MonthlyChartProps) {
  const data = monthly.map((item) => ({
    mes: item.month,
    Entradas: item.income,
    Saidas: item.expenses,
  }));

  return (
    <section className="panel">
      <div className="panel-kicker">Evolucao mensal</div>
      <div className="panel-header">
        <div>
          <h2>Entradas e saidas por mes</h2>
          <p>Comparativo visual do fluxo de caixa ao longo do periodo importado.</p>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} barGap={4} barCategoryGap="32%">
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.07)"
              vertical={false}
            />
            <XAxis
              dataKey="mes"
              tick={{ fill: "#98aac7", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v: number) =>
                v >= 1000 ? `R$${(v / 1000).toFixed(0)}k` : `R$${v}`
              }
              tick={{ fill: "#98aac7", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={64}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
            />
            <Legend
              wrapperStyle={{ paddingTop: 16, color: "#98aac7", fontSize: 13 }}
            />
            <Bar dataKey="Entradas" fill="#6de2d1" radius={[6, 6, 0, 0]} />
            <Bar dataKey="Saidas" fill="#ff8674" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
