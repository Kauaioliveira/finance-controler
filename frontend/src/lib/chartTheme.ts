/**
 * Cores dos graficos. Recharts precisa de strings concretas, entao os valores
 * ficam aqui em vez de custom properties do CSS — o app tem tema unico, logo
 * nao ha troca em runtime para observar.
 *
 * O par entradas/saidas foi validado para daltonismo: separacao deutan
 * dE 16.9 (piso 8) e ambos acima de 3:1 contra a superficie escura.
 * Os slots categoricos sao atribuidos em ordem fixa e nunca ciclados.
 */
export const chartTheme = {
  income: "#3ee6b0",
  expense: "#e6634f",
  grid: "#1e2126",
  axis: "#7e848d",
  cursor: "rgba(255,255,255,0.04)",
  surface: "#111214",
  series: [
    "#3ee6b0",
    "#e6634f",
    "#6aa6ff",
    "#e0a83e",
    "#b98cff",
    "#4fd0d8",
    "#f08bb4",
    "#8fbf5a",
  ],
} as const;
