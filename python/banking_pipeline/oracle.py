"""Python oracle of the COBOL posting and interest rules, used for regression tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

from banking_pipeline.copybook import money

MONTHS = Decimal("12")


def monthly_interest(balance: Decimal, rate: Decimal) -> Decimal:
    raw = (money(balance) * Decimal(str(rate))) / MONTHS
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def post_transactions(
    accounts: list[dict],
    transactions: list[dict],
) -> tuple[list[dict], list[dict]]:
    posted = deepcopy(accounts)
    index = {row["ACCT-ID"]: row for row in posted}
    exceptions: list[dict] = []

    for txn in transactions:
        account_id = txn["TXN-ACCT-ID"]
        amount = money(txn["TXN-AMOUNT"])
        account = index.get(account_id)
        if account is None:
            exceptions.append(_exc(account_id, "NFND", "ACCOUNT NOT FOUND", amount))
            continue
        if account["ACCT-STATUS"] == "C":
            exceptions.append(_exc(account_id, "CLSD", "ACCOUNT IS CLOSED", amount))
            continue
        if amount <= 0:
            exceptions.append(_exc(account_id, "IAMT", "INVALID TRANSACTION AMOUNT", amount))
            continue
        txn_type = txn["TXN-TYPE"]
        if txn_type == "C":
            account["ACCT-BALANCE"] = money(account["ACCT-BALANCE"]) + amount
        elif txn_type == "D":
            if amount > money(account["ACCT-BALANCE"]):
                exceptions.append(_exc(account_id, "NSF", "INSUFFICIENT FUNDS", amount))
            else:
                account["ACCT-BALANCE"] = money(account["ACCT-BALANCE"]) - amount
        else:
            exceptions.append(_exc(account_id, "ITYP", "INVALID TRANSACTION TYPE", amount))

    return posted, exceptions


def apply_interest(accounts: list[dict]) -> tuple[list[dict], list[dict]]:
    final = deepcopy(accounts)
    interest_rows: list[dict] = []
    for account in final:
        if account["ACCT-TYPE"] == "S" and account["ACCT-STATUS"] == "A":
            interest = monthly_interest(account["ACCT-BALANCE"], account["ACCT-RATE"])
            account["ACCT-BALANCE"] = money(account["ACCT-BALANCE"]) + interest
            interest_rows.append({"INT-ACCT-ID": account["ACCT-ID"], "INT-AMOUNT": interest})
    return final, interest_rows


def statements(
    accounts: list[dict],
    interest_rows: list[dict],
    run_date: date | None = None,
) -> list[dict]:
    stmt_date = int((run_date or date.today()).strftime("%Y%m%d"))
    interest_map = {row["INT-ACCT-ID"]: money(row["INT-AMOUNT"]) for row in interest_rows}
    rows = []
    for account in accounts:
        rows.append(
            {
                "STMT-ACCT-ID": account["ACCT-ID"],
                "STMT-NAME": account["ACCT-NAME"],
                "STMT-TYPE": account["ACCT-TYPE"],
                "STMT-STATUS": account["ACCT-STATUS"],
                "STMT-BALANCE": money(account["ACCT-BALANCE"]),
                "STMT-INTEREST": interest_map.get(account["ACCT-ID"], money(0)),
                "STMT-DATE": stmt_date,
            }
        )
    return rows


def run_oracle(accounts: list[dict], transactions: list[dict]) -> dict:
    posted, exceptions = post_transactions(accounts, transactions)
    final, interest_rows = apply_interest(posted)
    return {
        "posted": posted,
        "exceptions": exceptions,
        "final": final,
        "interest": interest_rows,
        "statements": statements(final, interest_rows),
    }


def _exc(account_id: str, code: str, message: str, amount: Decimal) -> dict:
    return {
        "EXC-ACCT-ID": account_id,
        "EXC-CODE": code,
        "EXC-MESSAGE": message,
        "EXC-AMOUNT": money(amount),
    }
