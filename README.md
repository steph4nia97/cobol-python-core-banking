# Andean Ledger

COBOL core-banking **batch** (posting, interest, statements) orchestrated by **Python**: job runner, copybook-to-JSON conversion, regression oracle, REST API, and CI.

This is the kind of work banks hire for when they say *mainframe modernization* — keep the COBOL business rules, wrap them with tests and APIs instead of rewriting everything.

```text
accounts.in.dat + transactions.dat
        │
        ▼
   POSTTXN.cbl  →  posted master + exceptions
        │
   CALCINT.cbl  →  final master + interest
        │
   GENSTMT.cbl  →  statement extract
        │
   Python convert / FastAPI / pytest oracle
```

## What the COBOL jobs do

| Job | Program | Input | Output |
| --- | --- | --- | --- |
| Post transactions | `POSTTXN` | account master, transactions | posted master, rejects |
| Accrue interest | `CALCINT` | posted master | final master, interest applied |
| Statements | `GENSTMT` | final master, interest | statement extract |

Business rules in the batch:

- Credits and debits against an in-memory account table (classic COBOL `OCCURS`)
- Rejects: unknown account (`NFND`), closed (`CLSD`), NSF (`NSF`), bad type (`ITYP`), bad amount (`IAMT`)
- Monthly interest on **active savings** only: `balance * annual_rate / 12`, rounded to cents
- Fixed-width records defined in **copybooks** (`SIGN IS LEADING SEPARATE`)

## What Python does

- Compiles GnuCOBOL (`cobc`) and runs the three programs in order
- Parses copybooks and turns `.dat` files into JSON
- A **Python oracle** implements the same rules so tests can prove COBOL output matches
- FastAPI dashboard + JSON API (`/api/accounts`, `/api/exceptions`, `/api/statements`, `POST /api/run`)

## CV bullet

> Built a COBOL (GnuCOBOL) core-banking batch for transaction posting, interest accrual and statement extract, with Python job orchestration, copybook-to-JSON conversion, a dual-implementation regression oracle, FastAPI, and GitHub Actions CI.

Spanish:

> Batch bancario en COBOL (GnuCOBOL): posting de transacciones, interés y extractos; orquestación Python, conversión copybook→JSON, oracle de regresión, API REST y CI.

## Project layout

```text
cobol/copybooks/     record layouts (ACCT, TXN, EXC, INT, STMT)
cobol/src/           POSTTXN, CALCINT, GENSTMT
cobol/data/          generated fixed-width sample files
python/banking_pipeline/  compile, jobs, copybook parser, oracle, API
python/tests/        copybook, oracle, and COBOL-vs-oracle tests
.github/workflows/ci.yml
```

## Prerequisites

- Python 3.11+
- [GnuCOBOL](https://gnucobol.sourceforge.io/) (`cobc` on your PATH)

Windows: install a GnuCOBOL build so `cobc -V` works (or use WSL). Ubuntu/CI: `sudo apt-get install gnucobol`.

## Run

From the repo root (works even if Python Scripts is not on PATH):

```bash
pip install -e "./python[dev]"
python -m banking_pipeline all
python -m pytest -v
```

API and dashboard:

```bash
python -m uvicorn banking_pipeline.api:app --app-dir python --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). “Run COBOL batch” compiles and executes the job stream. OpenAPI is at `/docs`.

Windows helper: `.\run.ps1 all`, `.\run.ps1 test`, `.\run.ps1 api`.

### Docker (no local GnuCOBOL)

```bash
docker compose up --build
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) and click **Run COBOL batch**. The image already has `cobc`.

Useful commands:

```bash
python -m banking_pipeline seed       # write cobol/data/*.dat
python -m banking_pipeline compile    # cobc -x the three programs into bin/
python -m banking_pipeline run        # compile + run + JSON in work/json/
```

## Sample results (oracle)

Interest is `posted_balance × that account's annual rate / 12`, not one rate for the whole bank.

The easy check that is **not** Lucia:

- `$100,000.00 × 5.00% / 12 = $416.67`

Lucia’s savings rate in the seed file is **4.25%**. Maria is the 5.00% account, and her balance after posting is $15,300, not $100,000.

| Account | Rate | After posting | Interest | Final |
| --- | ---: | ---: | ---: | ---: |
| 1000000001 Maria Gonzalez (savings) | 5.00% | 15,300.00 | 63.75 | 15,363.75 |
| 1000000002 Carlos Ramirez (checking) | 0% | 2,000.00 | 0.00 | 2,000.00 |
| 1000000003 Sofia Herrera (NSF then credit) | 0% | 175.00 | 0.00 | 175.00 |
| 1000000004 Pedro Alvarez (closed savings) | 3.00% | 800.00 | 0.00 | 800.00 |
| 1000000005 Lucia Fernandez (savings, no txns) | 4.25% | 100,000.00 | 354.17 | 100,354.17 |

Worked interest:

- Maria: `$15,300.00 × 5.00% / 12 = $63.75` → 15,363.75
- Lucia: `$100,000.00 × 4.25% / 12 = $354.17` → 100,354.17

`test_interest_uses_each_accounts_rate_not_a_global_five_percent` and `test_readme_documents_rates_and_does_not_imply_lucia_is_five_percent` lock this down. If GnuCOBOL is installed, `test_cobol_matches_oracle_when_compiled` also checks COBOL output against the same oracle.

Five exceptions: NSF, closed, unknown account, invalid type, zero amount.
