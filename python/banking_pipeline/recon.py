"""Daily proof: opening + credits - debits + interest = closing."""

from __future__ import annotations

from decimal import Decimal

from banking_pipeline.copybook import money


def reconcile(
    opening_accounts: list[dict],
    journal: list[dict],
    interest_rows: list[dict],
    final_accounts: list[dict],
) -> dict:
    opening = sum((money(row["ACCT-BALANCE"]) for row in opening_accounts), Decimal("0.00"))
    credits = sum(
        (money(row["JRN-AMOUNT"]) for row in journal if row.get("JRN-TYPE") == "C"),
        Decimal("0.00"),
    )
    debits = sum(
        (money(row["JRN-AMOUNT"]) for row in journal if row.get("JRN-TYPE") == "D"),
        Decimal("0.00"),
    )
    interest = sum((money(row["INT-AMOUNT"]) for row in interest_rows), Decimal("0.00"))
    closing = sum((money(row["ACCT-BALANCE"]) for row in final_accounts), Decimal("0.00"))
    expected = money(opening + credits - debits + interest)
    difference = money(closing - expected)
    status = "RECONCILED" if difference == 0 else "BREAK"
    return {
        "opening": str(money(opening)),
        "credits": str(money(credits)),
        "debits": str(money(debits)),
        "interest": str(money(interest)),
        "expected": str(expected),
        "actual": str(money(closing)),
        "difference": str(difference),
        "status": status,
    }
