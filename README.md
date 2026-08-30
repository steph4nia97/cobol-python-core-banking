# Legacy Banking Modernization Lab

COBOL + Python + FastAPI + PostgreSQL + Docker

[![CI](https://github.com/steph4nia97/cobol-python-core-banking/actions/workflows/ci.yml/badge.svg)](https://github.com/steph4nia97/cobol-python-core-banking/actions/workflows/ci.yml)

**Build | Tests | Docker | Python | COBOL**

GnuCOBOL end-of-day batch (posting, interest, statements, reconciliation) orchestrated by Python, persisted in PostgreSQL, and exposed through a JWT-protected FastAPI dashboard.

Lab logins (never use these patterns in production): `admin` / `admin` (run batch), `operator` / `operator` (read only).

## About

This repo keeps **fixed-width files as the legacy contract** and adds a modernization layer around them: job orchestration, copybook-to-JSON, a Python oracle, PostgreSQL, REST, and CI.

```text
transactions.dat
       ↓
     COBOL
       ↓
Resultado batch
       ↓
    Python
       ↓
 PostgreSQL
       ↓
   FastAPI
       ↓
 Dashboard
```

## Architecture

```text
             ┌──────────────┐
             │   Dashboard  │
             └──────┬───────┘
                    │
                REST API (JWT)
                    │
             ┌──────▼───────┐
             │   FastAPI    │
             └──────┬───────┘
                    │
          Python Orchestrator
                    │
       ┌────────────┼────────────┬──────────┐
       ▼            ▼            ▼          ▼
    POSTTXN       CALCINT      GENSTMT    CTLRPT
     COBOL         COBOL        COBOL      COBOL
       │            │            │          │
       └────────────┼────────────┴──────────┘
                    ▼
              Fixed-width files
                    │
                    ▼
              PostgreSQL
```

Rates are **not** hardcoded as `0.05` in COBOL. Each account carries `ACCT-RATE`; `config/application.yaml` holds `interest.monthsInYear` (12) used by the Python oracle.

## Business problem

A bank still posts the day in batch: a master file plus a transaction file. Rejects must not change balances. Savings interest is monthly. The operator needs a proof that opening + credits − debits + interest = closing.

## Batch processing

| Job | Program | Role |
| --- | --- | --- |
| Post | `POSTTXN` | Credits/debits, journal, rejects (`NFND` `CLSD` `NSF` `ITYP` `IAMT` `DUP`) |
| Interest | `CALCINT` | Active savings only: `balance × rate / monthsInYear` |
| Statements | `GENSTMT` | Statement extract |
| Proof | `CTLRPT` | Reconciliation; **RETURN-CODE 8** if out of balance |

Python runs them in order. A non-zero COBOL exit **stops the stream** (CALCINT does not run if POSTTXN fails) and stores:

```json
{ "step": "POSTTXN", "status": "FAILED", "exitCode": 8 }
```

Idempotency: each movement has `TXN-YYYYMMDD-NNNNNN`. A second **Run end-of-day** with the same ids is `ALREADY PROCESSED` (`DUP`).

Logs record batch id, step, and exception **codes** — not amounts or personal data.

## COBOL programs

- `cobol/src/POSTTXN.cbl` — posting + journal + duplicate check against `processed.dat`
- `cobol/src/CALCINT.cbl` — interest from the account master rate
- `cobol/src/GENSTMT.cbl` — statements
- `cobol/src/CTLRPT.cbl` — daily proof / **RECONCILED** control record

## API

Swagger: `/docs`

| Method | Path | Role |
| --- | --- | --- |
| POST | `/api/auth/login` | public |
| GET | `/api/accounts` | OPERATOR, ADMIN |
| GET | `/api/accounts/{id}` | OPERATOR, ADMIN |
| GET | `/api/transactions` | OPERATOR, ADMIN |
| GET | `/api/transactions/rejected` | OPERATOR, ADMIN |
| GET | `/api/batches` | OPERATOR, ADMIN |
| GET | `/api/batches/{id}` | OPERATOR, ADMIN |
| GET | `/api/statements/{account}` | OPERATOR, ADMIN |
| POST | `/api/batch/run` | **ADMIN** |

## Testing

Three layers:

1. **Unit** — copybooks, rates, reject codes, duplicate ids, reconciliation math  
2. **Integration** — FastAPI auth (operator cannot run the batch)  
3. **E2E** — GnuCOBOL output vs Python oracle when `cobc` is installed  

`pytest -v --cov=banking_pipeline`  

Interest check (do not mix Maria’s 5.00% with Lucia’s $100,000):

- `$100,000 × 5.00% / 12 = $416.67` (not Lucia)
- `$100,000 × 4.25% / 12 = $354.17` → **100,354.17**
- `$15,300 × 5.00% / 12 = $63.75` → **15,363.75**

## Running with Docker

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), sign in as **admin**, click **Run end-of-day**.

Without Docker: Python 3.11+, GnuCOBOL, then:

```bash
pip install -e "./python[dev]"
python -m pytest -v --cov=banking_pipeline
python -m uvicorn banking_pipeline.api:app --app-dir python --port 8000
```

SQLite is the default in `config/application.yaml`. Docker Compose uses **PostgreSQL**.

## Project structure

```text
cobol/copybooks/     ACCT TXN EXC JRN INT STMT CTL
cobol/src/           POSTTXN CALCINT GENSTMT CTLRPT
config/application.yaml
python/banking_pipeline/
python/tests/
.github/workflows/ci.yml
```

PostgreSQL tables: `accounts`, `transactions`, `batch_runs`, `rejected_transactions`, `statements`, `audit_logs`.

## Architecture decisions

- Legacy files stay the COBOL I/O; SQL is the system of record after each successful batch.  
- Fatal COBOL errors use RETURN-CODE 8 so the orchestrator can halt.  
- JWT roles separate **operator** (read) from **admin** (run).  
- Logs never include balances or transaction amounts.

## Sample results

| Account | Rate | After posting | Interest | Final |
| --- | ---: | ---: | ---: | ---: |
| Maria Gonzalez | 5.00% | 15,300.00 | 63.75 | 15,363.75 |
| Carlos Ramirez | 0% | 2,000.00 | 0.00 | 2,000.00 |
| Sofia Herrera | 0% | 175.00 | 0.00 | 175.00 |
| Pedro Alvarez (closed) | 3.00% | 800.00 | 0.00 | 800.00 |
| Lucia Fernandez | 4.25% | 100,000.00 | 354.17 | 100,354.17 |

Daily proof: opening 118,400.00 + credits 575.00 − debits 700.00 + interest 417.92 = **118,692.92 RECONCILED**.

## Future improvements

- Restart from the failed step only  
- Statement PDF export  
- Hash-based passwords instead of lab YAML users  
