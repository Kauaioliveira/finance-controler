from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from psycopg.types.json import Jsonb

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.database import database


class FinanceRepository:
    def create_import(
        self,
        *,
        company_id: str,
        uploaded_by_user_id: str,
        filename: str,
        source_type: str,
        status: str,
        currency: str,
        total_rows: int,
        processed_rows: int,
        error_message: str | None = None,
    ) -> dict:
        import_id = str(uuid4())
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO finance_imports (
                    id,
                    company_id,
                    uploaded_by_user_id,
                    filename,
                    source_type,
                    status,
                    currency,
                    total_rows,
                    processed_rows,
                    error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    import_id,
                    company_id,
                    uploaded_by_user_id,
                    filename,
                    source_type,
                    status,
                    currency,
                    total_rows,
                    processed_rows,
                    error_message,
                ),
            )
        return self.get_import(company_id, import_id)

    def update_import_status(
        self,
        *,
        company_id: str,
        import_id: str,
        status: str,
        processed_rows: int | None = None,
        error_message: str | None = None,
        finalized_at: datetime | None = None,
    ) -> dict:
        self._get_import_row(company_id, import_id)
        with database.connection() as connection:
            connection.execute(
                """
                UPDATE finance_imports
                SET
                    status = %s,
                    processed_rows = COALESCE(%s, processed_rows),
                    error_message = %s,
                    finalized_at = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (status, processed_rows, error_message, finalized_at, import_id),
            )
        return self.get_import(company_id, import_id)

    def create_transactions(
        self,
        *,
        import_id: str,
        transactions: list[dict[str, object]],
    ) -> None:
        with database.connection() as connection:
            for item in transactions:
                connection.execute(
                    """
                    INSERT INTO finance_transactions (
                        id,
                        import_id,
                        row_number,
                        transaction_date,
                        description,
                        amount,
                        direction,
                        predicted_category,
                        final_category,
                        category_confidence,
                        review_notes,
                        reviewed_by_user_id,
                        reviewed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        import_id,
                        item["row_number"],
                        item["transaction_date"],
                        item["description"],
                        item["amount"],
                        item["direction"],
                        item["predicted_category"],
                        item["final_category"],
                        item["category_confidence"],
                        item.get("review_notes"),
                        item.get("reviewed_by_user_id"),
                        item.get("reviewed_at"),
                    ),
                )

    def create_snapshot(
        self,
        *,
        import_id: str,
        summary_json: dict[str, object],
        categories_json: list[dict[str, object]],
        monthly_json: list[dict[str, object]],
        top_transactions_json: list[dict[str, object]],
        insights_json: list[dict[str, object]],
        narrative: str,
    ) -> dict:
        snapshot_id = str(uuid4())
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO finance_report_snapshots (
                    id,
                    import_id,
                    summary_json,
                    categories_json,
                    monthly_json,
                    top_transactions_json,
                    insights_json,
                    narrative
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot_id,
                    import_id,
                    Jsonb(summary_json),
                    Jsonb(categories_json),
                    Jsonb(monthly_json),
                    Jsonb(top_transactions_json),
                    Jsonb(insights_json),
                    narrative,
                ),
            )
        return self.get_latest_snapshot(import_id)

    def list_imports(
        self,
        *,
        company_id: str,
        limit: int,
        offset: int,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        uploaded_by_user_id: str | None = None,
    ) -> list[dict]:
        filters = ["i.company_id = %s"]
        params: list[object] = [company_id]
        if status:
            filters.append("i.status = %s")
            params.append(status)
        if date_from:
            filters.append("DATE(i.created_at) >= %s")
            params.append(date_from)
        if date_to:
            filters.append("DATE(i.created_at) <= %s")
            params.append(date_to)
        if uploaded_by_user_id:
            filters.append("i.uploaded_by_user_id = %s")
            params.append(uploaded_by_user_id)

        where_clause = " AND ".join(filters)
        params.extend([limit, offset])
        query = f"""
            SELECT
                i.id,
                i.company_id,
                i.uploaded_by_user_id,
                uploader.name AS uploaded_by_user_name,
                i.filename,
                i.source_type,
                i.status,
                i.currency,
                i.total_rows,
                i.processed_rows,
                i.error_message,
                i.created_at,
                i.updated_at,
                i.finalized_at,
                s.summary_json,
                s.categories_json,
                s.insights_json
            FROM finance_imports AS i
            INNER JOIN users AS uploader ON uploader.id = i.uploaded_by_user_id
            LEFT JOIN LATERAL (
                SELECT summary_json, categories_json, insights_json
                FROM finance_report_snapshots
                WHERE import_id = i.id
                ORDER BY created_at DESC
                LIMIT 1
            ) AS s ON TRUE
            WHERE {where_clause}
            ORDER BY i.created_at DESC
            LIMIT %s OFFSET %s
        """
        with database.connection() as connection:
            return connection.execute(query, tuple(params)).fetchall()

    def count_imports(
        self,
        *,
        company_id: str,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        uploaded_by_user_id: str | None = None,
    ) -> int:
        filters = ["company_id = %s"]
        params: list[object] = [company_id]
        if status:
            filters.append("status = %s")
            params.append(status)
        if date_from:
            filters.append("DATE(created_at) >= %s")
            params.append(date_from)
        if date_to:
            filters.append("DATE(created_at) <= %s")
            params.append(date_to)
        if uploaded_by_user_id:
            filters.append("uploaded_by_user_id = %s")
            params.append(uploaded_by_user_id)

        query = f"SELECT COUNT(*) AS total FROM finance_imports WHERE {' AND '.join(filters)}"
        with database.connection() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return int(row["total"])

    def get_import(self, company_id: str, import_id: str) -> dict:
        row = self._get_import_row(company_id, import_id)
        latest_snapshot = self.get_latest_snapshot(import_id, raise_if_missing=False)
        row["summary_json"] = latest_snapshot["summary_json"] if latest_snapshot else None
        row["categories_json"] = latest_snapshot["categories_json"] if latest_snapshot else []
        row["insights_json"] = latest_snapshot["insights_json"] if latest_snapshot else []
        return row

    def _get_import_row(self, company_id: str, import_id: str) -> dict:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    company_id,
                    uploaded_by_user_id,
                    (
                        SELECT name
                        FROM users
                        WHERE users.id = finance_imports.uploaded_by_user_id
                    ) AS uploaded_by_user_name,
                    filename,
                    source_type,
                    status,
                    currency,
                    total_rows,
                    processed_rows,
                    error_message,
                    created_at,
                    updated_at,
                    finalized_at
                FROM finance_imports
                WHERE id = %s AND company_id = %s
                """,
                (import_id, company_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("Importacao financeira nao encontrada.")
        return row

    def list_transactions(
        self,
        *,
        company_id: str,
        import_id: str,
        limit: int,
        offset: int,
        category: str | None = None,
        query: str | None = None,
    ) -> list[dict]:
        self._get_import_row(company_id, import_id)
        filters = ["t.import_id = %s"]
        params: list[object] = [import_id]
        if category:
            filters.append("t.final_category = %s")
            params.append(category)
        if query:
            filters.append("LOWER(t.description) LIKE %s")
            params.append(f"%{query.lower()}%")
        params.extend([limit, offset])
        sql = f"""
            SELECT
                t.id,
                t.row_number,
                t.transaction_date,
                t.description,
                t.amount,
                t.direction,
                t.predicted_category,
                t.final_category,
                t.category_confidence,
                t.review_notes,
                t.reviewed_at,
                t.reviewed_by_user_id
            FROM finance_transactions AS t
            WHERE {' AND '.join(filters)}
            ORDER BY t.row_number ASC
            LIMIT %s OFFSET %s
        """
        with database.connection() as connection:
            return connection.execute(sql, tuple(params)).fetchall()

    def count_transactions(
        self,
        *,
        company_id: str,
        import_id: str,
        category: str | None = None,
        query: str | None = None,
    ) -> int:
        self._get_import_row(company_id, import_id)
        filters = ["import_id = %s"]
        params: list[object] = [import_id]
        if category:
            filters.append("final_category = %s")
            params.append(category)
        if query:
            filters.append("LOWER(description) LIKE %s")
            params.append(f"%{query.lower()}%")
        sql = f"SELECT COUNT(*) AS total FROM finance_transactions WHERE {' AND '.join(filters)}"
        with database.connection() as connection:
            row = connection.execute(sql, tuple(params)).fetchone()
        return int(row["total"])

    def get_all_transactions(self, *, company_id: str, import_id: str) -> list[dict]:
        return self.list_transactions(
            company_id=company_id,
            import_id=import_id,
            limit=10_000,
            offset=0,
        )

    def update_transaction(
        self,
        *,
        company_id: str,
        import_id: str,
        transaction_id: str,
        final_category: str,
        review_notes: str | None,
        reviewed_by_user_id: str,
    ) -> dict:
        import_row = self._get_import_row(company_id, import_id)
        if import_row["status"] == "finalized":
            raise ConflictError("A importacao ja foi finalizada e nao pode mais ser editada.")

        with database.connection() as connection:
            row = connection.execute(
                """
                UPDATE finance_transactions
                SET
                    final_category = %s,
                    review_notes = %s,
                    reviewed_by_user_id = %s,
                    reviewed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s AND import_id = %s
                RETURNING
                    id,
                    row_number,
                    transaction_date,
                    description,
                    amount,
                    direction,
                    predicted_category,
                    final_category,
                    category_confidence,
                    review_notes,
                    reviewed_at,
                    reviewed_by_user_id
                """,
                (
                    final_category,
                    review_notes,
                    reviewed_by_user_id,
                    transaction_id,
                    import_id,
                ),
            ).fetchone()
        if row is None:
            raise NotFoundError("Transacao financeira nao encontrada.")

        self.update_import_status(
            company_id=company_id,
            import_id=import_id,
            status="in_review",
        )
        return row

    def finalize_import(
        self,
        *,
        company_id: str,
        import_id: str,
        finalized_at: datetime,
    ) -> dict:
        return self.update_import_status(
            company_id=company_id,
            import_id=import_id,
            status="finalized",
            finalized_at=finalized_at,
        )

    def get_latest_snapshot(self, import_id: str, *, raise_if_missing: bool = True) -> dict | None:
        with database.connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    import_id,
                    summary_json,
                    categories_json,
                    monthly_json,
                    top_transactions_json,
                    insights_json,
                    narrative,
                    created_at
                FROM finance_report_snapshots
                WHERE import_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (import_id,),
            ).fetchone()
        if row is None and raise_if_missing:
            raise NotFoundError("Snapshot do relatorio nao encontrado.")
        return row
