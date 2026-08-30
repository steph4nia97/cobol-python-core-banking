"""Python oracle of the COBOL posting and interest rules, used for regression tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

from banking_pipeline.config import load_settings
from banking_pipeline.copybook import money

from banking_pipeline.recon import reconcile


def monthly_interest(balance: Decimal, rate: Decimal, months: int | None = None) -> Decimal:
    divisor = Decimal(str(months if months is not None else load_settings().months_in_year))
    raw = (money(balance) * Decimal(str(rate))) / divisor
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def post_transactions(
    accounts: list[dict],
    transactions: list[dict],
    processed_ids: set[str] | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    posted = deepcopy(accounts)
    index = {row["ACCT-ID"]: row for row in posted}
    exceptions: list[dict] = []
    journal: list[dict] = []
    seen = set(processed_ids or ())

    for txn in transactions:
        account_id = txn["TXN-ACCT-ID"]
        amount = money(txn["TXN-AMOUNT"])
        txn_id = str(txn.get("TXN-ID", "")).strip()
        if txn_id and txn_id in seen:
            exceptions.append(_exc(txn_id, account_id, "DUP", "ALREADY PROCESSED", amount))
            continue
        account = index.get(account_id)
        if account is None:
            exceptions.append(_exc(txn_id, account_id, "NFND", "ACCOUNT NOT FOUND", amount))
            continue
        if account["ACCT-STATUS"] == "C":
            exceptions.append(_exc(txn_id, account_id, "CLSD", "ACCOUNT IS CLOSED", amount))
            continue
        if amount <= 0:
            exceptions.append(_exc(txn_id, account_id, "IAMT", "INVALID TRANSACTION AMOUNT", amount))
            continue
        txn_type = txn["TXN-TYPE"]
        if txn_type == "C":
            before = money(account["ACCT-BALANCE"])
            account["ACCT-BALANCE"] = before + amount
            journal.append(_journal(txn, before, account["ACCT-BALANCE"]))
            if txn_id:
                seen.add(txn_id)
        elif txn_type == "D":
            if amount > money(account["ACCT-BALANCE"]):
                exceptions.append(_exc(txn_id, account_id, "NSF", "INSUFFICIENT FUNDS", amount))
            else:
                before = money(account["ACCT-BALANCE"])
                account["ACCT-BALANCE"] = before - amount
                journal.append(_journal(txn, before, account["ACCT-BALANCE"]))
                if txn_id:
                    seen.add(txn_id)
        else:
            exceptions.append(_exc(txn_id, account_id, "ITYP", "INVALID TRANSACTION TYPE", amount))

    return posted, exceptions, journal


def apply_interest(accounts: list[dict]) -> tuple[list[dict], list[dict]]:
    final = deepcopy(accounts)
    interest_rows: list[dict] = []
    months = load_settings().months_in_year
    for account in final:
        if account["ACCT-TYPE"] == "S" and account["ACCT-STATUS"] == "A":
            interest = monthly_interest(account["ACCT-BALANCE"], account["ACCT-RATE"], months)
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


def run_oracle(
    accounts: list[dict],
    transactions: list[dict],
    processed_ids: set[str] | None = None,
) -> dict:
    posted, exceptions, journal = post_transactions(accounts, transactions, processed_ids)
    final, interest_rows = apply_interest(posted)
    return {
        "posted": posted,
        "exceptions": exceptions,
        "journal": journal,
        "final": final,
        "interest": interest_rows,
        "statements": statements(final, interest_rows),
        "recon": reconcile(accounts, journal, interest_rows, final),
    }


def _exc(txn_id: str, account_id: str, code: str, message: str, amount: Decimal) -> dict:
    return {
        "EXC-TXN-ID": txn_id,
        "EXC-ACCT-ID": account_id,
        "EXC-CODE": code,
        "EXC-MESSAGE": message,
        "EXC-AMOUNT": money(amount),
    }


def _journal(txn: dict, before: Decimal, after: Decimal) -> dict:
    return {
        "JRN-TXN-ID": txn.get("TXN-ID", ""),
        "JRN-ACCT-ID": txn["TXN-ACCT-ID"],
        "JRN-DATE": txn["TXN-DATE"],
        "JRN-TYPE": txn["TXN-TYPE"],
        "JRN-AMOUNT": money(txn["TXN-AMOUNT"]),
        "JRN-BAL-BEFORE": money(before),
        "JRN-BAL-AFTER": money(after),
        "JRN-DESC": txn["TXN-DESC"],
    }
