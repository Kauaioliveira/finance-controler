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
import type { FinanceImportResponse } from "../types";

type ImportsChartProps = {
  imports: FinanceImportResponse[];
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
      <strong className="chart-tooltip-label">{label}</strong>
      {payload.map((entry) => (
        <div key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value)}
        </div>
      ))}
    </div>
  );
}

function shortenFilename(name: string): string {
  const base = name.replace(/\.[^.]+$/, "");
  return base.length > 14 ? `${base.slice(0, 12)}…` : base;
}

export function ImportsChart({ imports }: ImportsChartProps) {
  const data = imports
    .filter((item) => item.summary_preview?.summary)
    .map((item) => ({
      arquivo: shortenFilename(item.filename),
      Entradas: item.summary_preview!.summary!.total_income,
      Saidas: item.summary_preview!.summary!.total_expenses,
    }))
    .reverse();

  if (data.length === 0) return null;

  return (
    <section className="panel">
      <div className="panel-kicker">Comparativo de importacoes</div>
      <div className="panel-header panel-header-tight">
        <div>
          <h2>Entradas e saidas por importacao</h2>
          <p>Visao rapida do volume financeiro das ultimas cargas processadas.</p>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} barGap={4} barCategoryGap="32%">
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.07)"
              vertical={false}
            />
            <XAxis
              dataKey="arquivo"
              tick={{ fill: "#98aac7", fontSize: 11 }}
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
              wrapperStyle={{ paddingTop: 12, color: "#98aac7", fontSize: 13 }}
            />
            <Bar dataKey="Entradas" fill="#6de2d1" radius={[6, 6, 0, 0]} />
            <Bar dataKey="Saidas" fill="#ff8674" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
