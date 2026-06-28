import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

import { formatCurrency, formatDate, formatPercent } from "./formatters";
import type { FinanceReportResponse } from "../types";

type ExportMeta = {
  filename: string;
  companyName: string;
};

// ─── PDF ─────────────────────────────────────────────────────────────────────

const PDF_DARK = [9, 16, 29] as [number, number, number];
const PDF_ACCENT = [109, 226, 209] as [number, number, number];
const PDF_MUTED = [100, 120, 150] as [number, number, number];
const PDF_WHITE = [237, 244, 255] as [number, number, number];
const PDF_RED = [255, 134, 116] as [number, number, number];
const PDF_GREEN = [140, 230, 160] as [number, number, number];

function addHeader(doc: jsPDF, meta: ExportMeta, pageWidth: number) {
  doc.setFillColor(...PDF_DARK);
  doc.rect(0, 0, pageWidth, 38, "F");

  doc.setFillColor(...PDF_ACCENT);
  doc.rect(0, 0, 4, 38, "F");

  doc.setTextColor(...PDF_ACCENT);
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("Finance Controler", 14, 15);

  doc.setTextColor(...PDF_MUTED);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(meta.companyName, 14, 23);
  doc.text(`Arquivo: ${meta.filename}`, 14, 30);

  const today = new Date().toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  doc.text(`Gerado em ${today}`, pageWidth - 14, 30, { align: "right" });
}

function addSectionTitle(doc: jsPDF, title: string, y: number) {
  doc.setTextColor(...PDF_ACCENT);
  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  doc.text(title.toUpperCase(), 14, y);
  doc.setDrawColor(...PDF_ACCENT);
  doc.setLineWidth(0.4);
  doc.line(14, y + 2, 196, y + 2);
}

export function exportToPDF(report: FinanceReportResponse, meta: ExportMeta) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 48;

  addHeader(doc, meta, pageWidth);

  // ── Summary cards ──────────────────────────────────────────────────────────
  addSectionTitle(doc, "Resumo financeiro", y);
  y += 10;

  const cards = [
    { label: "Entradas", value: formatCurrency(report.summary.total_income), color: PDF_GREEN },
    { label: "Saidas", value: formatCurrency(report.summary.total_expenses), color: PDF_RED },
    {
      label: "Saldo liquido",
      value: formatCurrency(report.summary.net_balance),
      color: report.summary.net_balance >= 0 ? PDF_GREEN : PDF_RED,
    },
    { label: "Transacoes", value: String(report.summary.transaction_count), color: PDF_WHITE },
  ];

  const cardW = (pageWidth - 28 - 9) / 4;
  cards.forEach((card, i) => {
    const x = 14 + i * (cardW + 3);
    doc.setFillColor(20, 32, 52);
    doc.roundedRect(x, y, cardW, 22, 3, 3, "F");
    doc.setTextColor(...PDF_MUTED);
    doc.setFontSize(7.5);
    doc.setFont("helvetica", "normal");
    doc.text(card.label, x + 5, y + 7);
    doc.setTextColor(...card.color);
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.text(card.value, x + 5, y + 17);
  });
  y += 32;

  // ── Categories ─────────────────────────────────────────────────────────────
  addSectionTitle(doc, "Categorias", y);
  y += 6;

  autoTable(doc, {
    startY: y,
    head: [["Categoria", "Transacoes", "Total", "Share"]],
    body: report.categories.map((c) => [
      c.label,
      c.transaction_count,
      formatCurrency(c.total_amount),
      c.direction === "expense" ? formatPercent(c.share) : "Receita",
    ]),
    styles: { fontSize: 8.5, textColor: PDF_WHITE, fillColor: [14, 22, 38] },
    headStyles: { fillColor: PDF_DARK, textColor: PDF_ACCENT, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [18, 28, 46] },
    margin: { left: 14, right: 14 },
    theme: "grid",
    tableLineColor: [30, 45, 70],
    tableLineWidth: 0.2,
  });

  y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;

  // ── Monthly ────────────────────────────────────────────────────────────────
  if (doc.internal.pageSize.getHeight() - y < 60) {
    doc.addPage();
    y = 20;
  }

  addSectionTitle(doc, "Evolucao mensal", y);
  y += 6;

  autoTable(doc, {
    startY: y,
    head: [["Mes", "Entradas", "Saidas", "Saldo"]],
    body: report.monthly.map((m) => [
      m.month,
      formatCurrency(m.income),
      formatCurrency(m.expenses),
      formatCurrency(m.net),
    ]),
    styles: { fontSize: 8.5, textColor: PDF_WHITE, fillColor: [14, 22, 38] },
    headStyles: { fillColor: PDF_DARK, textColor: PDF_ACCENT, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [18, 28, 46] },
    margin: { left: 14, right: 14 },
    theme: "grid",
    tableLineColor: [30, 45, 70],
    tableLineWidth: 0.2,
  });

  y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;

  // ── Top transactions ───────────────────────────────────────────────────────
  if (report.top_transactions.length > 0) {
    if (doc.internal.pageSize.getHeight() - y < 60) {
      doc.addPage();
      y = 20;
    }

    addSectionTitle(doc, "Maiores movimentos", y);
    y += 6;

    autoTable(doc, {
      startY: y,
      head: [["Data", "Descricao", "Categoria", "Valor"]],
      body: report.top_transactions.map((t) => [
        formatDate(t.transaction_date),
        t.description.slice(0, 48),
        t.final_category_label,
        formatCurrency(t.amount),
      ]),
      styles: { fontSize: 8.5, textColor: PDF_WHITE, fillColor: [14, 22, 38] },
      headStyles: { fillColor: PDF_DARK, textColor: PDF_ACCENT, fontStyle: "bold" },
      alternateRowStyles: { fillColor: [18, 28, 46] },
      margin: { left: 14, right: 14 },
      theme: "grid",
      tableLineColor: [30, 45, 70],
      tableLineWidth: 0.2,
    });
  }

  // ── Narrative ──────────────────────────────────────────────────────────────
  if (report.narrative) {
    doc.addPage();
    y = 20;
    addSectionTitle(doc, "Analise da IA", y);
    y += 8;
    doc.setTextColor(...PDF_WHITE);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    const lines = doc.splitTextToSize(report.narrative, pageWidth - 28) as string[];
    doc.text(lines, 14, y);
  }

  // ── Footer on all pages ────────────────────────────────────────────────────
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setTextColor(...PDF_MUTED);
    doc.setFontSize(7.5);
    doc.text(
      `Finance Controler · Pagina ${i} de ${totalPages}`,
      pageWidth / 2,
      doc.internal.pageSize.getHeight() - 8,
      { align: "center" },
    );
  }

  const safeName = meta.filename.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9_-]/g, "_");
  doc.save(`relatorio_${safeName}.pdf`);
}

// ─── Excel ────────────────────────────────────────────────────────────────────

export function exportToExcel(report: FinanceReportResponse, meta: ExportMeta) {
  const wb = XLSX.utils.book_new();

  // Sheet 1 – Resumo
  const summaryRows = [
    ["Finance Controler — Relatorio Financeiro"],
    ["Empresa", meta.companyName],
    ["Arquivo", meta.filename],
    ["Gerado em", new Date().toLocaleDateString("pt-BR")],
    [],
    ["Entradas", report.summary.total_income],
    ["Saidas", report.summary.total_expenses],
    ["Saldo liquido", report.summary.net_balance],
    ["Total de transacoes", report.summary.transaction_count],
    ["Categorizadas", report.summary.categorized_count],
    ["Sem categoria", report.summary.uncategorized_count],
  ];
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryRows);
  wsSummary["!cols"] = [{ wch: 22 }, { wch: 18 }];
  XLSX.utils.book_append_sheet(wb, wsSummary, "Resumo");

  // Sheet 2 – Categorias
  const catHeader = ["Categoria", "Direcao", "Transacoes", "Total (R$)", "Liquido (R$)", "Share (%)"];
  const catRows = report.categories.map((c) => [
    c.label,
    c.direction === "income" ? "Receita" : c.direction === "expense" ? "Despesa" : "Misto",
    c.transaction_count,
    c.total_amount,
    c.net_amount,
    +(c.share * 100).toFixed(2),
  ]);
  const wsCategories = XLSX.utils.aoa_to_sheet([catHeader, ...catRows]);
  wsCategories["!cols"] = [{ wch: 28 }, { wch: 10 }, { wch: 12 }, { wch: 14 }, { wch: 14 }, { wch: 10 }];
  XLSX.utils.book_append_sheet(wb, wsCategories, "Categorias");

  // Sheet 3 – Mensal
  const monthHeader = ["Mes", "Entradas (R$)", "Saidas (R$)", "Saldo (R$)"];
  const monthRows = report.monthly.map((m) => [m.month, m.income, m.expenses, m.net]);
  const wsMonthly = XLSX.utils.aoa_to_sheet([monthHeader, ...monthRows]);
  wsMonthly["!cols"] = [{ wch: 12 }, { wch: 16 }, { wch: 16 }, { wch: 16 }];
  XLSX.utils.book_append_sheet(wb, wsMonthly, "Mensal");

  // Sheet 4 – Transacoes
  const txHeader = ["Data", "Descricao", "Categoria prevista", "Categoria final", "Valor (R$)", "Direcao", "Confianca (%)", "Notas"];
  const txRows = report.top_transactions.map((t) => [
    formatDate(t.transaction_date),
    t.description,
    t.predicted_category_label,
    t.final_category_label,
    t.amount,
    t.direction === "income" ? "Entrada" : "Saida",
    +(t.category_confidence * 100).toFixed(1),
    t.review_notes ?? "",
  ]);
  const wsTransactions = XLSX.utils.aoa_to_sheet([txHeader, ...txRows]);
  wsTransactions["!cols"] = [
    { wch: 12 }, { wch: 40 }, { wch: 22 }, { wch: 22 },
    { wch: 14 }, { wch: 10 }, { wch: 12 }, { wch: 30 },
  ];
  XLSX.utils.book_append_sheet(wb, wsTransactions, "Transacoes");

  const safeName = meta.filename.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9_-]/g, "_");
  XLSX.writeFile(wb, `relatorio_${safeName}.xlsx`);
}
