export type Role = "admin" | "analyst" | "viewer";
export type FinanceDirection = "income" | "expense";
export type FinanceCategoryDirection = "income" | "expense" | "mixed";
export type FinanceImportStatus =
  | "uploaded"
  | "processed"
  | "in_review"
  | "finalized"
  | "failed";

export type FieldError = {
  field: string;
  message: string;
  type?: string;
};

export type ApiErrorPayload = {
  detail: string;
  code?: string;
  field_errors?: FieldError[];
};

export type HealthStatus = {
  status: string;
  schema_ready: boolean;
  detail: string;
};

export type ApiConfig = {
  app_name: string;
  environment: string;
  debug: boolean;
  demo_mode: boolean;
  max_chat_history: number;
  model: string;
  embeddings_model: string;
  database_ready: boolean;
  rag_top_k: number;
  rag_max_distance: number;
  allowed_origins: string[];
  max_upload_size_mb: number;
  supported_extensions: string[];
  supported_finance_extensions: string[];
  supported_roles: Role[];
  finance_statuses: FinanceImportStatus[];
  default_page_size: number;
  max_page_size: number;
};

export type CompanySummary = {
  id: string;
  name: string;
};

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  company: CompanySummary;
};

export type AuthTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
};

export type StoredSession = {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
};

export type UserResponse = {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  company: CompanySummary;
};

export type UserListResponse = {
  items: UserResponse[];
  total: number;
  page: number;
  page_size: number;
};

export type FinanceCategoryCatalogItem = {
  key: string;
  label: string;
  direction: FinanceCategoryDirection;
  description: string;
};

export type FinanceCategoryCatalogResponse = {
  categories: FinanceCategoryCatalogItem[];
};

export type FinanceSummary = {
  total_income: number;
  total_expenses: number;
  net_balance: number;
  transaction_count: number;
  categorized_count: number;
  uncategorized_count: number;
};

export type FinanceCategoryBreakdown = {
  category: string;
  label: string;
  direction: FinanceCategoryDirection;
  total_amount: number;
  net_amount: number;
  transaction_count: number;
  share: number;
};

export type FinanceMonthlySummary = {
  month: string;
  income: number;
  expenses: number;
  net: number;
};

export type FinanceInsight = {
  title: string;
  detail: string;
  tone: "positive" | "neutral" | "warning";
};

export type FinancePersistedTransaction = {
  id: string;
  row_number: number;
  transaction_date: string;
  description: string;
  amount: number;
  direction: FinanceDirection;
  predicted_category: string;
  predicted_category_label: string;
  final_category: string;
  final_category_label: string;
  category_confidence: number;
  review_notes: string | null;
  reviewed_at: string | null;
  reviewed_by_user_id: string | null;
};

export type FinanceImportSummaryPreview = {
  summary: FinanceSummary | null;
  categories: FinanceCategoryBreakdown[];
  insights: FinanceInsight[];
};

export type FinanceImportResponse = {
  id: string;
  company_id: string;
  uploaded_by_user_id: string;
  uploaded_by_user_name: string | null;
  filename: string;
  source_type: string;
  status: FinanceImportStatus;
  currency: string;
  total_rows: number;
  processed_rows: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  finalized_at: string | null;
  summary_preview: FinanceImportSummaryPreview | null;
};

export type FinanceImportListResponse = {
  items: FinanceImportResponse[];
  total: number;
  page: number;
  page_size: number;
};

export type FinanceTransactionListResponse = {
  items: FinancePersistedTransaction[];
  total: number;
  page: number;
  page_size: number;
};

export type FinalizeFinanceImportResponse = {
  import_id: string;
  status: FinanceImportStatus;
  finalized_at: string;
};

export type FinanceReportResponse = {
  import_id: string;
  generated_at: string;
  currency: string;
  summary: FinanceSummary;
  categories: FinanceCategoryBreakdown[];
  monthly: FinanceMonthlySummary[];
  top_transactions: FinancePersistedTransaction[];
  insights: FinanceInsight[];
  narrative: string;
};
