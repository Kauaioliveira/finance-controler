from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.finance_parser import finance_parser


def test_parse_csv_normalizes_headers_amounts_and_direction() -> None:
    payload = (
        "Data,Descricao,Valor,Tipo,Categoria\n"
        "09/04/2026,Pagamento folha operacional,\"R$ 5.400,00\",saida,payroll\n"
        "10/04/2026,Recebimento cliente,\"22.300,00\",entrada,\n"
    ).encode("utf-8")

    rows = finance_parser.parse_csv("transactions.csv", payload)

    assert len(rows) == 2
    assert rows[0].date == "2026-04-09"
    assert rows[0].amount == 5400.0
    assert rows[0].direction == "expense"
    assert rows[0].category_hint == "payroll"
    assert rows[1].direction == "income"
    assert rows[1].amount == 22300.0


def test_parse_csv_uses_negative_amount_to_infer_expense() -> None:
    payload = (
        "date,description,amount\n"
        "2026-04-11,Uber aeroporto,-96.30\n"
    ).encode("utf-8")

    rows = finance_parser.parse_csv("transactions.csv", payload)

    assert len(rows) == 1
    assert rows[0].direction == "expense"
    assert rows[0].amount == 96.3


def test_parse_csv_rejects_missing_required_headers() -> None:
    payload = "descricao,valor\nConta de luz,120.00\n".encode("utf-8")

    with pytest.raises(ValidationError) as error:
        finance_parser.parse_csv("transactions.csv", payload)

    assert "colunas necessarias" in error.value.detail


def test_parse_csv_rejects_empty_filename_payload_combo() -> None:
    with pytest.raises(ValidationError) as error:
        finance_parser.parse_csv("transactions.csv", b"")

    assert error.value.detail == "O arquivo CSV enviado esta vazio."
