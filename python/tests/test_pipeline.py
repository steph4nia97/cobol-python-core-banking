from decimal import Decimal

import pytest

from banking_pipeline.config import load_settings
from banking_pipeline.copybook import load_copybook
from banking_pipeline.expected import (
    CLOSING_TOTAL,
    CREDIT_TOTAL,
    DEBIT_TOTAL,
    FIVE_PERCENT_ON_100K,
    INTEREST_TOTAL,
    LUCIA_FINAL,
    LUCIA_ID,
    LUCIA_INTEREST,
    LUCIA_POSTED,
    LUCIA_RATE,
    MARIA_FINAL,
    MARIA_ID,
    MARIA_INTEREST,
    MARIA_POSTED,
    MARIA_RATE,
    OPENING_TOTAL,
    README_MARKERS,
)
from banking_pipeline.oracle import monthly_interest, run_oracle
from banking_pipeline.paths import copybook_dir, repo_root
from banking_pipeline.seed import sample_accounts, sample_transactions, write_seed_files


def books():
    root = copybook_dir()
    return {
        "acct": load_copybook(root / "ACCTREC.cpy"),
        "txn": load_copybook(root / "TXNREC.cpy"),
        "exc": load_copybook(root / "EXCREC.cpy"),
        "interest": load_copybook(root / "INTREC.cpy"),
        "stmt": load_copybook(root / "STMTREC.cpy"),
        "journal": load_copybook(root / "JRNREC.cpy"),
        "control": load_copybook(root / "CTLREC.cpy"),
    }


def test_copybook_record_lengths():
    loaded = books()
    assert loaded["acct"].record_length == 61
    assert loaded["txn"].record_length == 91
    assert loaded["exc"].record_length == 96
    assert loaded["interest"].record_length == 22
    assert loaded["stmt"].record_length == 76
    assert loaded["journal"].record_length == 119
    assert loaded["control"].record_length == 124


def test_config_months_not_hardcoded_five_percent():
    assert load_settings().months_in_year == 12
    assert load_settings().currency == "USD"


def test_valid_deposit_and_withdrawal():
    result = run_oracle(sample_accounts(), sample_transactions())
    by_id = {row["ACCT-ID"]: row for row in result["final"]}
    assert by_id[MARIA_ID]["ACCT-BALANCE"] == MARIA_FINAL
    assert by_id["1000000002"]["ACCT-BALANCE"] == Decimal("2000.00")


def test_nsf_unknown_closed_zero_and_bad_type():
    result = run_oracle(sample_accounts(), sample_transactions())
    codes = {row["EXC-CODE"].strip() for row in result["exceptions"]}
    assert codes == {"NFND", "CLSD", "NSF", "ITYP", "IAMT"}
    assert len(result["exceptions"]) == 5
    assert len(result["journal"]) == 5


def test_checking_gets_no_interest():
    result = run_oracle(sample_accounts(), sample_transactions())
    interest_ids = {row["INT-ACCT-ID"] for row in result["interest"]}
    assert "1000000002" not in interest_ids
    assert "1000000003" not in interest_ids


def test_duplicate_transaction_is_rejected():
    first = run_oracle(sample_accounts(), sample_transactions())
    posted_ids = {row["JRN-TXN-ID"] for row in first["journal"]}
    second = run_oracle(sample_accounts(), sample_transactions(), processed_ids=posted_ids)
    assert all(row["EXC-CODE"].strip() in {"DUP", "NFND", "CLSD", "NSF", "ITYP", "IAMT"} for row in second["exceptions"])
    dupes = [row for row in second["exceptions"] if row["EXC-CODE"].strip() == "DUP"]
    assert len(dupes) == 5
    by_id = {row["ACCT-ID"]: row for row in second["final"]}
    assert by_id[MARIA_ID]["ACCT-BALANCE"] == Decimal("15062.50")


def test_reconciliation_equation():
    result = run_oracle(sample_accounts(), sample_transactions())
    recon = result["recon"]
    assert Decimal(recon["opening"]) == OPENING_TOTAL
    assert Decimal(recon["credits"]) == CREDIT_TOTAL
    assert Decimal(recon["debits"]) == DEBIT_TOTAL
    assert Decimal(recon["interest"]) == INTEREST_TOTAL
    assert Decimal(recon["actual"]) == CLOSING_TOTAL
    assert recon["status"] == "RECONCILED"
    assert recon["difference"] == "0.00"


def test_interest_uses_each_accounts_rate_not_a_global_five_percent():
    by_id = {row["ACCT-ID"]: row for row in sample_accounts()}
    assert by_id[MARIA_ID]["ACCT-RATE"] == MARIA_RATE
    assert by_id[LUCIA_ID]["ACCT-RATE"] == LUCIA_RATE
    five_on_100k = monthly_interest(Decimal("100000.00"), Decimal("0.0500"))
    assert five_on_100k == FIVE_PERCENT_ON_100K
    assert monthly_interest(LUCIA_POSTED, LUCIA_RATE) == LUCIA_INTEREST
    assert monthly_interest(MARIA_POSTED, MARIA_RATE) == MARIA_INTEREST
    assert five_on_100k != LUCIA_INTEREST
    assert by_id[LUCIA_ID]["ACCT-BALANCE"] == Decimal("100000.00")
    result = run_oracle(sample_accounts(), sample_transactions())
    assert {row["ACCT-ID"]: row["ACCT-BALANCE"] for row in result["final"]}[LUCIA_ID] == LUCIA_FINAL


def test_readme_documents_rates_and_stack():
    readme = (repo_root() / "README.md").read_text(encoding="utf-8")
    for marker in README_MARKERS:
        assert marker in readme, f"README missing {marker}"


def test_seed_files_have_fixed_width():
    write_seed_files()
    from banking_pipeline.paths import data_dir

    accounts = (data_dir() / "accounts.in.dat").read_text(encoding="utf-8").splitlines()
    txns = (data_dir() / "transactions.dat").read_text(encoding="utf-8").splitlines()
    assert all(len(line) == 61 for line in accounts)
    assert all(len(line) == 91 for line in txns)


def test_cobol_matches_oracle_when_compiled():
    from banking_pipeline.compile_cobol import CobolNotInstalledError, cobc_path
    from banking_pipeline.convert import convert_work_files
    from banking_pipeline.jobs import run_jobs
    from banking_pipeline.paths import work_dir

    try:
        cobc_path()
    except CobolNotInstalledError:
        pytest.skip("GnuCOBOL is not installed")

    run_jobs(compile_first=True)
    cobol = convert_work_files(work_dir())
    expected = run_oracle(sample_accounts(), sample_transactions())
    cobol_balances = {row["acct_id"]: Decimal(row["acct_balance"]) for row in cobol["final"]}
    oracle_balances = {row["ACCT-ID"]: row["ACCT-BALANCE"] for row in expected["final"]}
    assert cobol_balances == oracle_balances
    assert (cobol.get("control") or {}).get("ctl_status", "").strip().startswith("BAL")
