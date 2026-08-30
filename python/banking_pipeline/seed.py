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
    return [
        {
            "TXN-ACCT-ID": "1000000001",
            "TXN-DATE": 20260801,
            "TXN-TYPE": "C",
            "TXN-AMOUNT": Decimal("500.00"),
            "TXN-DESC": "PAYROLL DEPOSIT",
        },
        {
            "TXN-ACCT-ID": "1000000001",
            "TXN-DATE": 20260812,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("200.00"),
            "TXN-DESC": "ATM WITHDRAWAL",
        },
        {
            "TXN-ACCT-ID": "1000000002",
            "TXN-DATE": 20260803,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("400.00"),
            "TXN-DESC": "POS PURCHASE",
        },
        {
            "TXN-ACCT-ID": "1000000002",
            "TXN-DATE": 20260818,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("100.00"),
            "TXN-DESC": "BILL PAYMENT",
        },
        {
            "TXN-ACCT-ID": "1000000003",
            "TXN-DATE": 20260805,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("500.00"),
            "TXN-DESC": "OVERDRAFT ATTEMPT",
        },
        {
            "TXN-ACCT-ID": "1000000004",
            "TXN-DATE": 20260809,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("50.00"),
            "TXN-DESC": "CLOSED ACCOUNT DEBIT",
        },
        {
            "TXN-ACCT-ID": "9999999999",
            "TXN-DATE": 20260810,
            "TXN-TYPE": "C",
            "TXN-AMOUNT": Decimal("25.00"),
            "TXN-DESC": "UNKNOWN ACCOUNT CREDIT",
        },
        {
            "TXN-ACCT-ID": "1000000003",
            "TXN-DATE": 20260820,
            "TXN-TYPE": "C",
            "TXN-AMOUNT": Decimal("75.00"),
            "TXN-DESC": "CASH DEPOSIT",
        },
        {
            "TXN-ACCT-ID": "1000000002",
            "TXN-DATE": 20260822,
            "TXN-TYPE": "X",
            "TXN-AMOUNT": Decimal("10.00"),
            "TXN-DESC": "BAD TYPE",
        },
        {
            "TXN-ACCT-ID": "1000000002",
            "TXN-DATE": 20260825,
            "TXN-TYPE": "D",
            "TXN-AMOUNT": Decimal("0.00"),
            "TXN-DESC": "ZERO AMOUNT",
        },
    ]


def write_seed_files() -> None:
    books = copybook_dir()
    out = data_dir()
    accounts = load_copybook(books / "ACCTREC.cpy")
    transactions = load_copybook(books / "TXNREC.cpy")
    write_records(accounts, out / "accounts.in.dat", sample_accounts())
    write_records(transactions, out / "transactions.dat", sample_transactions())
