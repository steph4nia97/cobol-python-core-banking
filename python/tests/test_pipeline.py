from decimal import Decimal

import pytest

from banking_pipeline.copybook import (
    format_record,
    load_copybook,
    parse_record,
)
from banking_pipeline.expected import (
    FIVE_PERCENT_ON_100K,
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
    }


def test_copybook_record_lengths():
    loaded = books()
    assert loaded["acct"].record_length == 61
    assert loaded["txn"].record_length == 71
    assert loaded["exc"].record_length == 76
    assert loaded["interest"].record_length == 22
    assert loaded["stmt"].record_length == 76


def test_account_roundtrip():
    acct = books()["acct"]
    row = sample_accounts()[0]
    raw = format_record(acct, row)
    parsed = parse_record(acct, raw)
    assert parsed["ACCT-ID"] == "1000000001"
    assert parsed["ACCT-NAME"] == "MARIA GONZALEZ"
    assert parsed["ACCT-BALANCE"] == Decimal("15000.00")
    assert parsed["ACCT-RATE"] == Decimal("0.0500")


def test_seed_files_have_fixed_width():
    write_seed_files()
    from banking_pipeline.paths import data_dir

    accounts = (data_dir() / "accounts.in.dat").read_text(encoding="utf-8").splitlines()
    txns = (data_dir() / "transactions.dat").read_text(encoding="utf-8").splitlines()
    assert all(len(line) == 61 for line in accounts)
    assert all(len(line) == 71 for line in txns)


def test_oracle_balances_and_rejects():
    result = run_oracle(sample_accounts(), sample_transactions())
    by_id = {row["ACCT-ID"]: row for row in result["final"]}
    interest = {row["INT-ACCT-ID"]: row["INT-AMOUNT"] for row in result["interest"]}
    codes = {row["EXC-CODE"].strip() for row in result["exceptions"]}

    assert by_id[MARIA_ID]["ACCT-BALANCE"] == MARIA_FINAL
    assert by_id["1000000002"]["ACCT-BALANCE"] == Decimal("2000.00")
    assert by_id["1000000003"]["ACCT-BALANCE"] == Decimal("175.00")
    assert by_id["1000000004"]["ACCT-BALANCE"] == Decimal("800.00")
    assert by_id[LUCIA_ID]["ACCT-BALANCE"] == LUCIA_FINAL
    assert interest[MARIA_ID] == MARIA_INTEREST
    assert interest[LUCIA_ID] == LUCIA_INTEREST
    assert codes == {"NFND", "CLSD", "NSF", "ITYP", "IAMT"}
    assert len(result["exceptions"]) == 5


def test_interest_uses_each_accounts_rate_not_a_global_five_percent():
    by_id = {row["ACCT-ID"]: row for row in sample_accounts()}
    assert by_id[MARIA_ID]["ACCT-RATE"] == MARIA_RATE
    assert by_id[LUCIA_ID]["ACCT-RATE"] == LUCIA_RATE
    assert by_id[LUCIA_ID]["ACCT-RATE"] != MARIA_RATE

    five_on_100k = monthly_interest(Decimal("100000.00"), Decimal("0.0500"))
    assert five_on_100k == FIVE_PERCENT_ON_100K
    assert monthly_interest(LUCIA_POSTED, LUCIA_RATE) == LUCIA_INTEREST
    assert monthly_interest(MARIA_POSTED, MARIA_RATE) == MARIA_INTEREST
    assert five_on_100k != LUCIA_INTEREST


def test_readme_documents_rates_and_does_not_imply_lucia_is_five_percent():
    readme = (repo_root() / "README.md").read_text(encoding="utf-8")
    for marker in README_MARKERS:
        assert marker in readme, f"README missing documented figure {marker}"
    lucia_seed = next(a for a in sample_accounts() if a["ACCT-ID"] == LUCIA_ID)
    assert lucia_seed["ACCT-RATE"] == LUCIA_RATE


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

    cobol_codes = sorted(row["exc_code"].strip() for row in cobol["exceptions"])
    oracle_codes = sorted(row["EXC-CODE"].strip() for row in expected["exceptions"])
    assert cobol_codes == oracle_codes
