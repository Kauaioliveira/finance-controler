import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { useChartTheme } from "../lib/chartTheme";
import { formatCurrency } from "../lib/formatters";
import type { FinanceCategoryBreakdown } from "../types";

type CategoryPieChartProps = {
  categories: FinanceCategoryBreakdown[];
};

type TooltipEntry = {
  name: string;
  value: number;
  payload: { share: number };
  color: string;
};

type CustomTooltipProps = {
  active?: boolean;
  payload?: TooltipEntry[];
};

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="chart-tooltip">
      <strong>{item.name}</strong>
      <div>{formatCurrency(item.value)}</div>
      <div className="chart-tooltip-label">
        {(item.payload.share * 100).toFixed(1)}% das saidas
      </div>
    </div>
  );
}

export function CategoryPieChart({ categories }: CategoryPieChartProps) {
  const chart = useChartTheme();
  const data = categories
    .filter((c) => c.direction === "expense" && c.total_amount > 0)
    .slice(0, 8)
    .map((c) => ({
      name: c.label,
      value: c.total_amount,
      share: c.share,
    }));

  if (data.length === 0) return null;

  return (
    <div className="chart-wrap chart-wrap--pie">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={64}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell
                key={index}
                fill={chart.series[index]}
                stroke="var(--surface)"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: "var(--text-muted)" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
