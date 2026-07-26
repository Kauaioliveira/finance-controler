import { useEffect, useState } from "react";

/**
 * Recharts needs concrete color strings, so the CSS custom properties have to
 * be resolved in JS and re-read whenever the theme changes.
 */
export type ChartTheme = {
  income: string;
  expense: string;
  grid: string;
  axis: string;
  cursor: string;
  series: string[];
};

const TOKENS = [
  "--chart-income",
  "--chart-expense",
  "--chart-grid",
  "--chart-axis",
  "--chart-cursor",
  "--chart-1",
  "--chart-2",
  "--chart-3",
  "--chart-4",
  "--chart-5",
  "--chart-6",
  "--chart-7",
  "--chart-8",
] as const;

function readChartTheme(): ChartTheme {
  const styles = getComputedStyle(document.documentElement);
  const read = (token: (typeof TOKENS)[number]) => styles.getPropertyValue(token).trim();

  return {
    income: read("--chart-income"),
    expense: read("--chart-expense"),
    grid: read("--chart-grid"),
    axis: read("--chart-axis"),
    cursor: read("--chart-cursor"),
    series: [
      read("--chart-1"),
      read("--chart-2"),
      read("--chart-3"),
      read("--chart-4"),
      read("--chart-5"),
      read("--chart-6"),
      read("--chart-7"),
      read("--chart-8"),
    ],
  };
}

export function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState<ChartTheme>(readChartTheme);

  useEffect(() => {
    const sync = () => setTheme(readChartTheme());

    // The toggle stamps data-theme on <html>; the OS setting fires matchMedia.
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    const query = window.matchMedia("(prefers-color-scheme: dark)");
    query.addEventListener("change", sync);

    sync();

    return () => {
      observer.disconnect();
      query.removeEventListener("change", sync);
    };
  }, []);

  return theme;
}
