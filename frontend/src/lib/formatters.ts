export function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDate(value: string) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

export function formatDateTime(value: string) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatRoleLabel(value: string) {
  switch (value) {
    case "admin":
      return "Admin";
    case "analyst":
      return "Analyst";
    case "viewer":
      return "Viewer";
    default:
      return value;
  }
}

export function formatImportStatus(value: string) {
  switch (value) {
    case "uploaded":
      return "Upload recebido";
    case "processed":
      return "Processado";
    case "in_review":
      return "Em revisao";
    case "finalized":
      return "Finalizado";
    case "failed":
      return "Falhou";
    default:
      return value;
  }
}
