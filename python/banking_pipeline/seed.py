"""Sample master and transaction files used by the COBOL job stream."""

from decimal import Decimal

from banking_pipeline.copybook import load_copybook, write_records
from banking_pipeline.paths import copybook_dir, data_dir


def sample_accounts() -> list[dict]:
    return [
        {
            "ACCT-ID": "1000000001",
            "ACCT-NAME": "MARIA GONZALEZ",
            "ACCT-TYPE": "S",
            "ACCT-STATUS": "A",
            "ACCT-BALANCE": Decimal("15000.00"),
            "ACCT-RATE": Decimal("0.0500"),
        },
        {
            "ACCT-ID": "1000000002",
            "ACCT-NAME": "CARLOS RAMIREZ",
            "ACCT-TYPE": "C",
            "ACCT-STATUS": "A",
            "ACCT-BALANCE": Decimal("2500.00"),
            "ACCT-RATE": Decimal("0.0000"),
        },
        {
            "ACCT-ID": "1000000003",
            "ACCT-NAME": "SOFIA HERRERA",
            "ACCT-TYPE": "C",
            "ACCT-STATUS": "A",
            "ACCT-BALANCE": Decimal("100.00"),
            "ACCT-RATE": Decimal("0.0000"),
        },
        {
            "ACCT-ID": "1000000004",
            "ACCT-NAME": "PEDRO ALVAREZ",
            "ACCT-TYPE": "S",
            "ACCT-STATUS": "C",
            "ACCT-BALANCE": Decimal("800.00"),
            "ACCT-RATE": Decimal("0.0300"),
        },
        {
            "ACCT-ID": "1000000005",
            "ACCT-NAME": "LUCIA FERNANDEZ",
            "ACCT-TYPE": "S",
            "ACCT-STATUS": "A",
            "ACCT-BALANCE": Decimal("100000.00"),
            "ACCT-RATE": Decimal("0.0425"),  # 4.25% — not Maria's 5%
        },
    ]


def sample_transactions() -> list[dict]:
    def txn(seq: int, account: str, day: int, txn_type: str, amount: Decimal, desc: str) -> dict:
        return {
            "TXN-ID": f"TXN-20260830-{seq:06d}",
            "TXN-ACCT-ID": account,
            "TXN-DATE": day,
            "TXN-TYPE": txn_type,
            "TXN-AMOUNT": amount,
            "TXN-DESC": desc,
        }

    return [
        txn(1, "1000000001", 20260801, "C", Decimal("500.00"), "PAYROLL DEPOSIT"),
        txn(2, "1000000001", 20260812, "D", Decimal("200.00"), "ATM WITHDRAWAL"),
        txn(3, "1000000002", 20260803, "D", Decimal("400.00"), "POS PURCHASE"),
        txn(4, "1000000002", 20260818, "D", Decimal("100.00"), "BILL PAYMENT"),
        txn(5, "1000000003", 20260805, "D", Decimal("500.00"), "OVERDRAFT ATTEMPT"),
        txn(6, "1000000004", 20260809, "D", Decimal("50.00"), "CLOSED ACCOUNT DEBIT"),
        txn(7, "9999999999", 20260810, "C", Decimal("25.00"), "UNKNOWN ACCOUNT CREDIT"),
        txn(8, "1000000003", 20260820, "C", Decimal("75.00"), "CASH DEPOSIT"),
        txn(9, "1000000002", 20260822, "X", Decimal("10.00"), "BAD TYPE"),
        txn(10, "1000000002", 20260825, "D", Decimal("0.00"), "ZERO AMOUNT"),
    ]


def write_seed_files() -> None:
    books = copybook_dir()
    out = data_dir()
    accounts = load_copybook(books / "ACCTREC.cpy")
    transactions = load_copybook(books / "TXNREC.cpy")
    write_records(accounts, out / "accounts.in.dat", sample_accounts())
    write_records(transactions, out / "transactions.dat", sample_transactions())
