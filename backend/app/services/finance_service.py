from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import UploadFile
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.exceptions import (
    AuthorizationError,
    DocumentProcessingError,
    ValidationError,
)
from app.repositories.finance_repository import FinanceRepository
from app.schemas.finance import (
    FinalizeFinanceImportResponse,
    FinanceAnalysisResponse,
    FinanceCategoryBreakdown,
    FinanceCategoryCatalogItem,
    FinanceCategoryCatalogResponse,
    FinanceImportListResponse,
    FinanceImportResponse,
    FinanceImportSummaryPreview,
    FinanceInsight,
    FinanceMonthlySummary,
    FinancePersistedTransaction,
    FinanceReportResponse,
    FinanceSummary,
    FinanceTransaction,
    FinanceTransactionListResponse,
    UpdateFinanceTransactionRequest,
)
from app.services.finance_parser import RawFinanceTransaction, finance_parser


@dataclass(frozen=True)
class FinanceCategoryDefinition:
    key: str
    label: str
    direction: str
    description: str
    keywords: tuple[str, ...]


CATEGORY_DEFINITIONS = (
    FinanceCategoryDefinition(
        key="sales_revenue",
        label="Receita de vendas",
        direction="income",
        description="Entradas vindas de clientes, vendas ou recebimentos operacionais.",
        keywords=("venda", "recebimento", "cliente", "invoice", "fatura", "pix recebido"),
    ),
    FinanceCategoryDefinition(
        key="financial_income",
        label="Receita financeira",
        direction="income",
        description="Rendimentos, juros recebidos ou ganhos financeiros eventuais.",
        keywords=("rendimento", "juros recebidos", "aplicacao", "cashback", "estorno recebido"),
    ),
    FinanceCategoryDefinition(
        key="taxes",
        label="Tributos e obrigacoes",
        direction="expense",
        description="Impostos, DAS, DARF e demais recolhimentos obrigatorios.",
        keywords=("imposto", "tributo", "darf", "simples", "icms", "iss", "pis", "cofins", "irpj", "csll"),
    ),
    FinanceCategoryDefinition(
        key="payroll",
        label="Folha e pessoas",
        direction="expense",
        description="Salarios, pro-labore, encargos trabalhistas e beneficios.",
        keywords=("salario", "folha", "prolabore", "pro-labore", "fgts", "inss", "ferias", "vale refeicao"),
    ),
    FinanceCategoryDefinition(
        key="rent_facilities",
        label="Estrutura e aluguel",
        direction="expense",
        description="Aluguel, condominio e gastos com a operacao fisica.",
        keywords=("aluguel", "condominio", "locacao", "escritorio", "coworking"),
    ),
    FinanceCategoryDefinition(
        key="software_tools",
        label="Software e ferramentas",
        direction="expense",
        description="Assinaturas de software, SaaS e ferramentas de operacao.",
        keywords=("software", "assinatura", "saas", "adobe", "microsoft", "google workspace", "openai", "aws", "notion"),
    ),
    FinanceCategoryDefinition(
        key="bank_fees",
        label="Tarifas e servicos financeiros",
        direction="expense",
        description="Tarifas bancarias, adquirencia, juros e custos financeiros.",
        keywords=("tarifa", "taxa bancaria", "maquininha", "adquirente", "juros", "iof", "anuidade"),
    ),
    FinanceCategoryDefinition(
        key="marketing",
        label="Marketing e aquisicao",
        direction="expense",
        description="Midia paga, campanhas e investimentos comerciais.",
        keywords=("ads", "campanha", "anuncio", "trafego", "meta ads", "google ads", "marketing"),
    ),
    FinanceCategoryDefinition(
        key="transport_travel",
        label="Transporte e viagens",
        direction="expense",
        description="Deslocamentos, combustivel, viagens e hospedagem.",
        keywords=("uber", "99", "combustivel", "gasolina", "hotel", "passagem", "viagem"),
    ),
    FinanceCategoryDefinition(
        key="utilities",
        label="Servicos recorrentes",
        direction="expense",
        description="Energia, agua, internet, telefone e infraestrutura utilitaria.",
        keywords=("energia", "agua", "internet", "telefone", "celular", "luz"),
    ),
    FinanceCategoryDefinition(
        key="professional_services",
        label="Servicos profissionais",
        direction="expense",
        description="Consultoria, advocacia, contabilidade e servicos especializados.",
        keywords=("contador", "contabilidade", "advocacia", "consultoria", "freelancer", "agencia"),
    ),
    FinanceCategoryDefinition(
        key="meals",
        label="Alimentacao",
        direction="expense",
        description="Refeicoes, cafe e alimentacao ligada a operacao.",
        keywords=("ifood", "restaurante", "almoco", "jantar", "cafe", "lanche"),
    ),
    FinanceCategoryDefinition(
        key="office_supplies",
        label="Materiais e escritorio",
        direction="expense",
        description="Compras de escritorio, materiais e suprimentos do dia a dia.",
        keywords=("papelaria", "material", "escritorio", "suprimento", "toner"),
    ),
    FinanceCategoryDefinition(
        key="transfers",
        label="Transferencias internas",
        direction="mixed",
        description="Movimentacoes entre contas e ajustes internos.",
        keywords=("transferencia", "ted", "pix entre contas", "ajuste interno"),
    ),
    FinanceCategoryDefinition(
        key="miscellaneous",
        label="Diversos",
        direction="mixed",
        description="Movimentacoes que ainda nao se encaixam em uma regra especifica.",
        keywords=(),
    ),
)

CATEGORY_LOOKUP = {item.key: item for item in CATEGORY_DEFINITIONS}


class FinanceService:
    def __init__(self) -> None:
        self.repository = FinanceRepository()

    async def analyze_file_preview(self, file: UploadFile) -> FinanceAnalysisResponse:
        filename = (file.filename or "").strip()
        if not filename:
            raise ValidationError("O arquivo financeiro precisa ter um nome valido.")
        payload = await file.read()
        await file.close()
        self._validate_upload_size(len(payload))
        rows = finance_parser.parse_csv(filename, payload)
        transactions = [self._categorize_transaction(row) for row in rows]
        report = await self._build_report(
            filename=filename,
            currency="BRL",
            transactions=transactions,
        )
        return FinanceAnalysisResponse(
            filename=filename,
            generated_at=report["generated_at"],
            currency="BRL",
            summary=report["summary"],
            categories=report["categories"],
            monthly=report["monthly"],
            top_transactions=report["top_transactions"],
            transactions=transactions,
            insights=report["insights"],
            narrative=report["narrative"],
        )

    async def create_import(self, current_user: dict, file: UploadFile) -> FinanceImportResponse:
        self._ensure_import_permission(current_user)
        filename = (file.filename or "").strip()
        if not filename:
            raise ValidationError("O arquivo financeiro precisa ter um nome valido.")

        payload = await file.read()
        await file.close()
        self._validate_upload_size(len(payload))

        try:
            rows = finance_parser.parse_csv(filename, payload)
        except (ValidationError, DocumentProcessingError):
            raise

        transactions = [self._categorize_transaction(row) for row in rows]
        import_row = self.repository.create_import(
            company_id=current_user["company_id"],
            uploaded_by_user_id=current_user["id"],
            filename=filename,
            source_type="csv",
            status="uploaded",
            currency="BRL",
            total_rows=len(rows),
            processed_rows=0,
        )

        self.repository.create_transactions(
            import_id=import_row["id"],
            transactions=[
                {
                    "row_number": item.row_number,
                    "transaction_date": item.date,
                    "description": item.description,
                    "amount": item.amount,
                    "direction": item.direction,
                    "predicted_category": item.category,
                    "final_category": item.category,
                    "category_confidence": item.confidence,
                    "review_notes": item.notes,
                }
                for item in transactions
            ],
        )

        persisted_rows = self.repository.get_all_transactions(
            company_id=current_user["company_id"],
            import_id=import_row["id"],
        )
        persisted_transactions = [
            self._build_persisted_transaction(row) for row in persisted_rows
        ]
        report = await self._build_report_from_persisted(
            filename=filename,
            currency="BRL",
            transactions=persisted_transactions,
        )
        self.repository.create_snapshot(
            import_id=import_row["id"],
            summary_json=report["summary"].model_dump(),
            categories_json=[item.model_dump() for item in report["categories"]],
            monthly_json=[item.model_dump() for item in report["monthly"]],
            top_transactions_json=[item.model_dump() for item in report["top_transactions"]],
            insights_json=[item.model_dump() for item in report["insights"]],
            narrative=report["narrative"],
        )
        updated = self.repository.update_import_status(
            company_id=current_user["company_id"],
            import_id=import_row["id"],
            status="processed",
            processed_rows=len(rows),
        )
        return self._build_import_response(updated)

    def list_imports(
        self,
        current_user: dict,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        uploaded_by_user_id: str | None = None,
    ) -> FinanceImportListResponse:
        offset = (page - 1) * page_size
        rows = self.repository.list_imports(
            company_id=current_user["company_id"],
            limit=page_size,
            offset=offset,
            status=status,
            date_from=date_from,
            date_to=date_to,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        total = self.repository.count_imports(
            company_id=current_user["company_id"],
            status=status,
            date_from=date_from,
            date_to=date_to,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        return FinanceImportListResponse(
            items=[self._build_import_response(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_import(self, current_user: dict, import_id: str) -> FinanceImportResponse:
        row = self.repository.get_import(current_user["company_id"], import_id)
        return self._build_import_response(row)

    def get_transactions(
        self,
        current_user: dict,
        import_id: str,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        query: str | None = None,
    ) -> FinanceTransactionListResponse:
        rows = self.repository.list_transactions(
            company_id=current_user["company_id"],
            import_id=import_id,
            limit=page_size,
            offset=(page - 1) * page_size,
            category=category,
            query=query,
        )
        total = self.repository.count_transactions(
            company_id=current_user["company_id"],
            import_id=import_id,
            category=category,
            query=query,
        )
        return FinanceTransactionListResponse(
            items=[self._build_persisted_transaction(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_transaction(
        self,
        current_user: dict,
        import_id: str,
        transaction_id: str,
        payload: UpdateFinanceTransactionRequest,
    ) -> FinancePersistedTransaction:
        self._ensure_import_permission(current_user)
        if payload.final_category not in CATEGORY_LOOKUP:
            raise ValidationError("Categoria final invalida.")

        row = self.repository.update_transaction(
            company_id=current_user["company_id"],
            import_id=import_id,
            transaction_id=transaction_id,
            final_category=payload.final_category,
            review_notes=payload.review_notes,
            reviewed_by_user_id=current_user["id"],
        )
        await self._refresh_snapshot(current_user["company_id"], import_id)
        return self._build_persisted_transaction(row)

    async def finalize_import(
        self,
        current_user: dict,
        import_id: str,
    ) -> FinalizeFinanceImportResponse:
        if current_user["role"] not in {"admin", "analyst"}:
            raise AuthorizationError("Apenas admin e analyst podem finalizar analises.")
        await self._refresh_snapshot(current_user["company_id"], import_id)
        updated = self.repository.finalize_import(
            company_id=current_user["company_id"],
            import_id=import_id,
            finalized_at=datetime.now(UTC),
        )
        return FinalizeFinanceImportResponse(
            import_id=updated["id"],
            status=updated["status"],
            finalized_at=updated["finalized_at"],
        )

    def get_report(self, current_user: dict, import_id: str) -> FinanceReportResponse:
        import_row = self.repository.get_import(current_user["company_id"], import_id)
        snapshot = self.repository.get_latest_snapshot(import_id)
        return FinanceReportResponse(
            import_id=import_row["id"],
            generated_at=snapshot["created_at"],
            currency=import_row["currency"],
            summary=FinanceSummary.model_validate(snapshot["summary_json"]),
            categories=[
                FinanceCategoryBreakdown.model_validate(item)
                for item in snapshot["categories_json"]
            ],
            monthly=[
                FinanceMonthlySummary.model_validate(item)
                for item in snapshot["monthly_json"]
            ],
            top_transactions=[
                FinancePersistedTransaction.model_validate(item)
                for item in snapshot["top_transactions_json"]
            ],
            insights=[
                FinanceInsight.model_validate(item)
                for item in snapshot["insights_json"]
            ],
            narrative=snapshot["narrative"],
        )

    def get_category_catalog(self) -> FinanceCategoryCatalogResponse:
        return FinanceCategoryCatalogResponse(
            categories=[
                FinanceCategoryCatalogItem(
                    key=item.key,
                    label=item.label,
                    direction=item.direction,  # type: ignore[arg-type]
                    description=item.description,
                )
                for item in CATEGORY_DEFINITIONS
            ]
        )

    async def _refresh_snapshot(self, company_id: str, import_id: str) -> None:
        import_row = self.repository.get_import(company_id, import_id)
        rows = self.repository.get_all_transactions(company_id=company_id, import_id=import_id)
        transactions = [self._build_persisted_transaction(row) for row in rows]
        report = await self._build_report_from_persisted(
            filename=import_row["filename"],
            currency=import_row["currency"],
            transactions=transactions,
        )
        self.repository.create_snapshot(
            import_id=import_id,
            summary_json=report["summary"].model_dump(),
            categories_json=[item.model_dump() for item in report["categories"]],
            monthly_json=[item.model_dump() for item in report["monthly"]],
            top_transactions_json=[item.model_dump() for item in report["top_transactions"]],
            insights_json=[item.model_dump() for item in report["insights"]],
            narrative=report["narrative"],
        )

    def _categorize_transaction(
        self,
        transaction: RawFinanceTransaction,
    ) -> FinanceTransaction:
        description_normalized = self._normalize_text(transaction.description)
        hinted_category = self._match_category_hint(transaction.category_hint)
        if hinted_category:
            category = hinted_category
            confidence = 0.98
            notes = "Categoria reaproveitada do arquivo importado."
        else:
            category = self._match_category_by_keyword(
                description_normalized,
                direction=transaction.direction,
            )
            confidence = 0.9 if category.key != "miscellaneous" else 0.55
            notes = None if category.key != "miscellaneous" else "Sem regra especifica; revisar manualmente."

        return FinanceTransaction(
            row_number=transaction.row_number,
            date=transaction.date,
            description=transaction.description,
            amount=round(transaction.amount, 2),
            direction=transaction.direction,  # type: ignore[arg-type]
            category=category.key,
            category_label=category.label,
            confidence=confidence,
            notes=notes,
        )

    def _build_import_response(self, row: dict) -> FinanceImportResponse:
        summary_preview = None
        if row.get("summary_json"):
            summary_preview = FinanceImportSummaryPreview(
                summary=FinanceSummary.model_validate(row["summary_json"]),
                categories=[
                    FinanceCategoryBreakdown.model_validate(item)
                    for item in row.get("categories_json", [])
                ],
                insights=[
                    FinanceInsight.model_validate(item)
                    for item in row.get("insights_json", [])
                ],
            )
        return FinanceImportResponse(
            id=row["id"],
            company_id=row["company_id"],
            uploaded_by_user_id=row["uploaded_by_user_id"],
            uploaded_by_user_name=row.get("uploaded_by_user_name"),
            filename=row["filename"],
            source_type=row["source_type"],
            status=row["status"],
            currency=row["currency"],
            total_rows=row["total_rows"],
            processed_rows=row["processed_rows"],
            error_message=row.get("error_message"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            finalized_at=row.get("finalized_at"),
            summary_preview=summary_preview,
        )

    def _build_persisted_transaction(self, row: dict) -> FinancePersistedTransaction:
        predicted = CATEGORY_LOOKUP.get(
            row["predicted_category"],
            CATEGORY_LOOKUP["miscellaneous"],
        )
        final = CATEGORY_LOOKUP.get(row["final_category"], CATEGORY_LOOKUP["miscellaneous"])
        return FinancePersistedTransaction(
            id=row["id"],
            row_number=row["row_number"],
            transaction_date=row["transaction_date"],
            description=row["description"],
            amount=float(row["amount"]),
            direction=row["direction"],  # type: ignore[arg-type]
            predicted_category=row["predicted_category"],
            predicted_category_label=predicted.label,
            final_category=row["final_category"],
            final_category_label=final.label,
            category_confidence=float(row["category_confidence"]),
            review_notes=row.get("review_notes"),
            reviewed_at=row.get("reviewed_at"),
            reviewed_by_user_id=row.get("reviewed_by_user_id"),
        )

    def _match_category_hint(
        self,
        category_hint: str | None,
    ) -> FinanceCategoryDefinition | None:
        if not category_hint:
            return None
        normalized = self._normalize_text(category_hint).replace(" ", "_")
        if normalized in CATEGORY_LOOKUP:
            return CATEGORY_LOOKUP[normalized]
        for item in CATEGORY_DEFINITIONS:
            if normalized == self._normalize_text(item.label).replace(" ", "_"):
                return item
        return None

    def _match_category_by_keyword(
        self,
        description: str,
        *,
        direction: str,
    ) -> FinanceCategoryDefinition:
        for item in CATEGORY_DEFINITIONS:
            if item.key == "miscellaneous":
                continue
            if item.direction != "mixed" and item.direction != direction:
                continue
            if any(keyword in description for keyword in item.keywords):
                return item
        if direction == "income":
            return CATEGORY_LOOKUP["sales_revenue"]
        return CATEGORY_LOOKUP["miscellaneous"]

    async def _build_report(
        self,
        *,
        filename: str,
        currency: str,
        transactions: list[FinanceTransaction],
    ) -> dict[str, object]:
        summary = self._build_summary_from_preview(transactions)
        categories = self._build_category_breakdown_from_preview(transactions, summary.total_expenses)
        monthly = self._build_monthly_summary_from_preview(transactions)
        top_transactions = self._build_top_transactions_from_preview(transactions)
        insights = self._build_insights(summary, categories, monthly)
        narrative = await self._build_narrative(summary, categories, monthly, insights)
        return {
            "generated_at": datetime.now(UTC),
            "filename": filename,
            "currency": currency,
            "summary": summary,
            "categories": categories,
            "monthly": monthly,
            "top_transactions": top_transactions,
            "insights": insights,
            "narrative": narrative,
        }

    async def _build_report_from_persisted(
        self,
        *,
        filename: str,
        currency: str,
        transactions: list[FinancePersistedTransaction],
    ) -> dict[str, object]:
        summary = self._build_summary_from_persisted(transactions)
        categories = self._build_category_breakdown_from_persisted(transactions, summary.total_expenses)
        monthly = self._build_monthly_summary_from_persisted(transactions)
        top_transactions = self._build_top_transactions_from_persisted(transactions)
        insights = self._build_insights(summary, categories, monthly)
        narrative = await self._build_narrative(summary, categories, monthly, insights)
        return {
            "generated_at": datetime.now(UTC),
            "filename": filename,
            "currency": currency,
            "summary": summary,
            "categories": categories,
            "monthly": monthly,
            "top_transactions": top_transactions,
            "insights": insights,
            "narrative": narrative,
        }

    def _build_summary_from_preview(self, transactions: list[FinanceTransaction]) -> FinanceSummary:
        total_income = round(
            sum(item.amount for item in transactions if item.direction == "income"),
            2,
        )
        total_expenses = round(
            sum(item.amount for item in transactions if item.direction == "expense"),
            2,
        )
        categorized_count = sum(1 for item in transactions if item.category != "miscellaneous")
        return FinanceSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net_balance=round(total_income - total_expenses, 2),
            transaction_count=len(transactions),
            categorized_count=categorized_count,
            uncategorized_count=len(transactions) - categorized_count,
        )

    def _build_summary_from_persisted(self, transactions: list[FinancePersistedTransaction]) -> FinanceSummary:
        total_income = round(
            sum(item.amount for item in transactions if item.direction == "income"),
            2,
        )
        total_expenses = round(
            sum(item.amount for item in transactions if item.direction == "expense"),
            2,
        )
        categorized_count = sum(1 for item in transactions if item.final_category != "miscellaneous")
        return FinanceSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net_balance=round(total_income - total_expenses, 2),
            transaction_count=len(transactions),
            categorized_count=categorized_count,
            uncategorized_count=len(transactions) - categorized_count,
        )

    def _build_category_breakdown_from_preview(
        self,
        transactions: list[FinanceTransaction],
        total_expenses: float,
    ) -> list[FinanceCategoryBreakdown]:
        grouped: dict[str, list[FinanceTransaction]] = defaultdict(list)
        for item in transactions:
            grouped[item.category].append(item)
        return self._build_category_rows(grouped, total_expenses, category_getter=lambda item: item.category)

    def _build_category_breakdown_from_persisted(
        self,
        transactions: list[FinancePersistedTransaction],
        total_expenses: float,
    ) -> list[FinanceCategoryBreakdown]:
        grouped: dict[str, list[FinancePersistedTransaction]] = defaultdict(list)
        for item in transactions:
            grouped[item.final_category].append(item)
        return self._build_category_rows(grouped, total_expenses, category_getter=lambda item: item.final_category)

    def _build_category_rows(self, grouped: dict[str, list], total_expenses: float, *, category_getter) -> list[FinanceCategoryBreakdown]:
        categories: list[FinanceCategoryBreakdown] = []
        for category_key, items in grouped.items():
            definition = CATEGORY_LOOKUP.get(category_key, CATEGORY_LOOKUP["miscellaneous"])
            income_total = sum(item.amount for item in items if item.direction == "income")
            expense_total = sum(item.amount for item in items if item.direction == "expense")
            magnitude = expense_total if expense_total > 0 else income_total
            share = expense_total / total_expenses if definition.direction == "expense" and total_expenses > 0 else 0.0
            categories.append(
                FinanceCategoryBreakdown(
                    category=category_key,
                    label=definition.label,
                    direction=definition.direction,  # type: ignore[arg-type]
                    total_amount=round(magnitude, 2),
                    net_amount=round(income_total - expense_total, 2),
                    transaction_count=len(items),
                    share=round(share, 4),
                )
            )
        return sorted(
            categories,
            key=lambda item: (item.direction != "expense", -item.total_amount, item.label),
        )

    def _build_monthly_summary_from_preview(
        self,
        transactions: list[FinanceTransaction],
    ) -> list[FinanceMonthlySummary]:
        return self._build_monthly_rows(transactions, date_getter=lambda item: item.date)

    def _build_monthly_summary_from_persisted(
        self,
        transactions: list[FinancePersistedTransaction],
    ) -> list[FinanceMonthlySummary]:
        return self._build_monthly_rows(transactions, date_getter=lambda item: item.transaction_date)

    def _build_monthly_rows(self, transactions: list, *, date_getter) -> list[FinanceMonthlySummary]:
        buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for item in transactions:
            value = date_getter(item)
            month_key = value[:7] if len(value) >= 7 and value[4] == "-" else "Sem data"
            buckets[month_key][item.direction] += item.amount
        return [
            FinanceMonthlySummary(
                month=month,
                income=round(values["income"], 2),
                expenses=round(values["expense"], 2),
                net=round(values["income"] - values["expense"], 2),
            )
            for month, values in sorted(buckets.items(), key=lambda pair: pair[0])
        ]

    def _build_top_transactions_from_preview(
        self,
        transactions: list[FinanceTransaction],
    ) -> list[FinanceTransaction]:
        expenses = [item for item in transactions if item.direction == "expense"]
        return sorted(expenses, key=lambda item: item.amount, reverse=True)[:5]

    def _build_top_transactions_from_persisted(
        self,
        transactions: list[FinancePersistedTransaction],
    ) -> list[FinancePersistedTransaction]:
        expenses = [item for item in transactions if item.direction == "expense"]
        return sorted(expenses, key=lambda item: item.amount, reverse=True)[:5]

    def _build_insights(
        self,
        summary: FinanceSummary,
        categories: list[FinanceCategoryBreakdown],
        monthly: list[FinanceMonthlySummary],
    ) -> list[FinanceInsight]:
        insights: list[FinanceInsight] = []
        if summary.net_balance >= 0:
            insights.append(
                FinanceInsight(
                    title="Caixa operacional positivo",
                    detail=f"O periodo analisado fechou com saldo de {self._format_currency(summary.net_balance)}.",
                    tone="positive",
                )
            )
        else:
            insights.append(
                FinanceInsight(
                    title="Alerta de queima de caixa",
                    detail=(
                        "As despesas superaram as entradas no periodo analisado. "
                        "Vale revisar as categorias de maior peso antes do fechamento."
                    ),
                    tone="warning",
                )
            )

        top_expense = next((item for item in categories if item.direction == "expense"), None)
        if top_expense:
            insights.append(
                FinanceInsight(
                    title="Categoria com maior impacto",
                    detail=f"{top_expense.label} concentrou {top_expense.share * 100:.1f}% das saidas relevantes.",
                    tone="neutral" if top_expense.share < 0.35 else "warning",
                )
            )

        if monthly:
            last_month = monthly[-1]
            insights.append(
                FinanceInsight(
                    title="Pulso mensal",
                    detail=(
                        f"No mes {last_month.month}, as entradas ficaram em {self._format_currency(last_month.income)} "
                        f"e as saidas em {self._format_currency(last_month.expenses)}."
                    ),
                    tone="neutral",
                )
            )

        if summary.uncategorized_count > 0:
            insights.append(
                FinanceInsight(
                    title="Itens para revisar",
                    detail=f"{summary.uncategorized_count} transacao(oes) cairam em Diversos e merecem revisao humana.",
                    tone="warning",
                )
            )
        return insights[:4]

    async def _build_narrative(
        self,
        summary: FinanceSummary,
        categories: list[FinanceCategoryBreakdown],
        monthly: list[FinanceMonthlySummary],
        insights: list[FinanceInsight],
    ) -> str:
        settings = get_settings()
        if settings.demo_mode:
            return self._fallback_narrative(summary, categories, insights)

        top_categories = [f"{item.label}: {self._format_currency(item.total_amount)}" for item in categories[:4]]
        monthly_snapshot = [
            f"{item.month} -> entradas {self._format_currency(item.income)}, saidas {self._format_currency(item.expenses)}, saldo {self._format_currency(item.net)}"
            for item in monthly[:4]
        ]
        prompt = (
            "Voce e um analista financeiro para pequenas e medias empresas. "
            "Escreva um resumo executivo em portugues do Brasil, em no maximo 120 palavras, "
            "sem inventar dados. Use tom claro e objetivo. Responda sem markdown, sem bullets.\n\n"
            f"Resumo: entradas={summary.total_income}, saidas={summary.total_expenses}, saldo={summary.net_balance}.\n"
            f"Categorias: {'; '.join(top_categories) or 'sem categorias relevantes'}.\n"
            f"Meses: {'; '.join(monthly_snapshot) or 'sem recorte mensal'}.\n"
            f"Insights: {'; '.join(insight.detail for insight in insights)}."
        )
        try:
            model = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.2,
            )
            response = await model.ainvoke(prompt)
            content = response.content
            if isinstance(content, str):
                return self._sanitize_narrative(content)
            return self._sanitize_narrative(str(content))
        except Exception:
            return self._fallback_narrative(summary, categories, insights)

    def _fallback_narrative(
        self,
        summary: FinanceSummary,
        categories: list[FinanceCategoryBreakdown],
        insights: list[FinanceInsight],
    ) -> str:
        top_label = categories[0].label if categories else "sem categoria dominante"
        balance_phrase = "fechou no azul" if summary.net_balance >= 0 else "fechou pressionado pelas saidas"
        return (
            "A leitura inicial do arquivo mostra que o fluxo financeiro "
            f"{balance_phrase}, com destaque para {top_label}. "
            f"Foram analisadas {summary.transaction_count} transacoes, e {summary.uncategorized_count} "
            "merecem revisao manual para aumentar a confianca dos proximos relatorios. "
            + (" ".join(insight.detail for insight in insights[:2]))
        ).strip()

    def _format_currency(self, value: float) -> str:
        formatted = f"{value:,.2f}"
        return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def _sanitize_narrative(self, value: str) -> str:
        cleaned = value.replace("**", "").replace("__", "").strip()
        return " ".join(cleaned.split())

    def _ensure_import_permission(self, current_user: dict) -> None:
        if current_user["role"] not in {"admin", "analyst"}:
            raise AuthorizationError("Voce nao tem permissao para importar ou revisar transacoes.")

    def _validate_upload_size(self, size_bytes: int) -> None:
        settings = get_settings()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValidationError(
                "O arquivo excede o limite permitido para upload. "
                f"Limite atual: {settings.max_upload_size_mb} MB."
            )

    def _normalize_text(self, value: str) -> str:
        return value.strip().lower()


finance_service = FinanceService()
