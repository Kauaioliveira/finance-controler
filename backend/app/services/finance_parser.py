from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

from app.core.exceptions import DocumentProcessingError, ValidationError


DATE_HEADERS = ("date", "data", "competencia", "posted_at", "transaction_date")
DESCRIPTION_HEADERS = (
    "description",
    "descricao",
    "historico",
    "memo",
    "details",
    "detalhes",
)
AMOUNT_HEADERS = ("amount", "valor", "value", "montante", "total", "price")
TYPE_HEADERS = ("type", "tipo", "direction", "natureza", "movement")
CATEGORY_HEADERS = ("category", "categoria")


@dataclass
class RawFinanceTransaction:
    row_number: int
    date: str
    description: str
    amount: float
    direction: str
    category_hint: str | None = None


class FinanceParser:
    def parse_csv(
        self,
        filename: str,
        payload: bytes,
    ) -> list[RawFinanceTransaction]:
        if not filename.lower().endswith(".csv"):
            raise ValidationError("A analise financeira inicial aceita apenas arquivos CSV.")
        if not payload:
            raise ValidationError("O arquivo CSV enviado esta vazio.")

        text = self._decode_payload(payload)
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            raise DocumentProcessingError("O CSV precisa ter cabecalho.")

        header_map = {
            self._normalize_header(header): header for header in reader.fieldnames if header
        }
        date_header = self._pick_header(header_map, DATE_HEADERS)
        description_header = self._pick_header(header_map, DESCRIPTION_HEADERS)
        amount_header = self._pick_header(header_map, AMOUNT_HEADERS)
        type_header = self._pick_header(header_map, TYPE_HEADERS, required=False)
        category_header = self._pick_header(header_map, CATEGORY_HEADERS, required=False)

        rows: list[RawFinanceTransaction] = []
        for row_index, row in enumerate(reader, start=2):
            description = (row.get(description_header, "") or "").strip()
            amount_raw = (row.get(amount_header, "") or "").strip()
            if not description and not amount_raw:
                continue
            if not description:
                raise ValidationError(
                    f"Linha {row_index}: a descricao da transacao nao pode ficar vazia."
                )
            if not amount_raw:
                raise ValidationError(
                    f"Linha {row_index}: o valor da transacao nao pode ficar vazio."
                )

            amount = self._parse_amount(amount_raw, row_index)
            date_value = self._normalize_date((row.get(date_header, "") or "").strip())
            direction = self._resolve_direction(
                amount=amount,
                direction_hint=(row.get(type_header, "") or "").strip() if type_header else "",
            )

            rows.append(
                RawFinanceTransaction(
                    row_number=row_index,
                    date=date_value,
                    description=description,
                    amount=abs(amount),
                    direction=direction,
                    category_hint=(
                        (row.get(category_header, "") or "").strip()
                        if category_header
                        else None
                    ),
                )
            )

        if not rows:
            raise ValidationError("Nenhuma transacao valida foi encontrada no CSV.")

        return rows

    def _decode_payload(self, payload: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise DocumentProcessingError("Nao foi possivel decodificar o arquivo CSV.")

    def _pick_header(
        self,
        header_map: dict[str, str],
        aliases: tuple[str, ...],
        *,
        required: bool = True,
    ) -> str | None:
        for alias in aliases:
            if alias in header_map:
                return header_map[alias]
        if required:
            expected = ", ".join(aliases)
            raise ValidationError(
                "O CSV nao possui as colunas necessarias. "
                f"Esperado um cabecalho compativel com: {expected}."
            )
        return None

    def _normalize_header(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        return ascii_text.strip().lower().replace(" ", "_")

    def _parse_amount(self, raw: str, row_index: int) -> float:
        value = raw.strip().replace("R$", "").replace("$", "")
        value = value.replace(" ", "")

        if "," in value and "." in value:
            if value.rfind(",") > value.rfind("."):
                value = value.replace(".", "").replace(",", ".")
            else:
                value = value.replace(",", "")
        elif "," in value:
            value = value.replace(".", "").replace(",", ".")

        try:
            return float(value)
        except ValueError as exc:
            raise ValidationError(
                f"Linha {row_index}: nao foi possivel interpretar o valor '{raw}'."
            ) from exc

    def _normalize_date(self, raw: str) -> str:
        if not raw:
            return "Sem data"

        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
        return raw

    def _resolve_direction(self, *, amount: float, direction_hint: str) -> str:
        hint = self._normalize_header(direction_hint) if direction_hint else ""
        if hint in {"income", "credit", "entrada", "receita", "credito"}:
            return "income"
        if hint in {"expense", "debit", "saida", "despesa", "debito"}:
            return "expense"
        return "income" if amount >= 0 else "expense"


finance_parser = FinanceParser()
