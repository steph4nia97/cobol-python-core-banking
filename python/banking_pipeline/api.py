from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from banking_pipeline.compile_cobol import CobolNotInstalledError
from banking_pipeline.convert import load_json
from banking_pipeline.jobs import run_jobs
from banking_pipeline.oracle import run_oracle
from banking_pipeline.paths import work_dir
from banking_pipeline.seed import sample_accounts, sample_transactions

app = FastAPI(
    title="Andean Ledger",
    description="COBOL banking batch exposed through a Python API.",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    html_path = Path(__file__).with_name("dashboard.html")
    return html_path.read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    work = work_dir()
    return {
        "status": "ok",
        "batch_ran": (work / "json" / "final.json").exists(),
    }


@app.get("/api/accounts")
def accounts() -> list[dict]:
    return load_json(work_dir(), "final")


@app.get("/api/accounts/{account_id}")
def account(account_id: str) -> dict:
    for row in load_json(work_dir(), "final"):
        if row.get("acct_id") == account_id:
            return row
    raise HTTPException(status_code=404, detail="Account not found")


@app.get("/api/exceptions")
def exceptions() -> list[dict]:
    return load_json(work_dir(), "exceptions")


@app.get("/api/statements")
def statements() -> list[dict]:
    return load_json(work_dir(), "statements")


@app.get("/api/oracle")
def oracle_preview() -> dict:
    result = run_oracle(sample_accounts(), sample_transactions())
    return {
        "accounts": len(result["final"]),
        "exceptions": len(result["exceptions"]),
        "interest_rows": len(result["interest"]),
    }


@app.post("/api/run")
def run_batch() -> dict:
    try:
        return run_jobs(compile_first=True)
    except CobolNotInstalledError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
