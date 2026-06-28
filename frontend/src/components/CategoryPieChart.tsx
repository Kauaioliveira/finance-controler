import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatCurrency } from "../lib/formatters";
import type { FinanceCategoryBreakdown } from "../types";

const CHART_COLORS = [
  "#6de2d1",
  "#ff8674",
  "#f4c66c",
  "#8aa8ff",
  "#8ce6a0",
  "#c4a0ff",
  "#ffb347",
  "#4fc3f7",
  "#f06292",
  "#aed581",
];

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
      <div style={{ color: "#98aac7" }}>
        {(item.payload.share * 100).toFixed(1)}% das saidas
      </div>
    </div>
  );
}

export function CategoryPieChart({ categories }: CategoryPieChartProps) {
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
                fill={CHART_COLORS[index % CHART_COLORS.length]}
                stroke="transparent"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: "#98aac7" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
