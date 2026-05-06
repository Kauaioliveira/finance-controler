from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FinanceDirection = Literal["income", "expense"]
FinanceCategoryDirection = Literal["income", "expense", "mixed"]
FinanceImportStatus = Literal["uploaded", "processed", "in_review", "finalized", "failed"]


class FinanceTransaction(BaseModel):
    row_number: int
    date: str
    description: str
    amount: float
    direction: FinanceDirection
    category: str
    category_label: str
    confidence: float = Field(ge=0, le=1)
    notes: str | None = None


class FinancePersistedTransaction(BaseModel):
    id: str
    row_number: int
    transaction_date: str
    description: str
    amount: float
    direction: FinanceDirection
    predicted_category: str
    predicted_category_label: str
    final_category: str
    final_category_label: str
    category_confidence: float = Field(ge=0, le=1)
    review_notes: str | None = None
    reviewed_at: datetime | None = None
    reviewed_by_user_id: str | None = None


class FinanceSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    transaction_count: int
    categorized_count: int
    uncategorized_count: int


class FinanceCategoryBreakdown(BaseModel):
    category: str
    label: str
    direction: FinanceCategoryDirection
    total_amount: float
    net_amount: float
    transaction_count: int
    share: float = Field(ge=0, le=1)


class FinanceMonthlySummary(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class FinanceInsight(BaseModel):
    title: str
    detail: str
    tone: Literal["positive", "neutral", "warning"]


class FinanceAnalysisResponse(BaseModel):
    filename: str
    generated_at: datetime
    currency: str = "BRL"
    summary: FinanceSummary
    categories: list[FinanceCategoryBreakdown]
    monthly: list[FinanceMonthlySummary]
    top_transactions: list[FinanceTransaction]
    transactions: list[FinanceTransaction]
    insights: list[FinanceInsight]
    narrative: str


class FinanceReportResponse(BaseModel):
    import_id: str
    generated_at: datetime
    currency: str
    summary: FinanceSummary
    categories: list[FinanceCategoryBreakdown]
    monthly: list[FinanceMonthlySummary]
    top_transactions: list[FinancePersistedTransaction]
    insights: list[FinanceInsight]
    narrative: str


class FinanceImportSummaryPreview(BaseModel):
    summary: FinanceSummary | None = None
    categories: list[FinanceCategoryBreakdown] = Field(default_factory=list)
    insights: list[FinanceInsight] = Field(default_factory=list)


class FinanceImportResponse(BaseModel):
    id: str
    company_id: str
    uploaded_by_user_id: str
    uploaded_by_user_name: str | None = None
    filename: str
    source_type: str
    status: FinanceImportStatus
    currency: str
    total_rows: int
    processed_rows: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None = None
    summary_preview: FinanceImportSummaryPreview | None = None


class FinanceImportListResponse(BaseModel):
    items: list[FinanceImportResponse]
    total: int
    page: int
    page_size: int


class FinanceTransactionListResponse(BaseModel):
    items: list[FinancePersistedTransaction]
    total: int
    page: int
    page_size: int


class UpdateFinanceTransactionRequest(BaseModel):
    final_category: str = Field(..., min_length=1)
    review_notes: str | None = None


class FinalizeFinanceImportResponse(BaseModel):
    import_id: str
    status: FinanceImportStatus
    finalized_at: datetime


class FinanceCategoryCatalogItem(BaseModel):
    key: str
    label: str
    direction: FinanceCategoryDirection
    description: str


class FinanceCategoryCatalogResponse(BaseModel):
    categories: list[FinanceCategoryCatalogItem]
