from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from banking_pipeline.auth import TokenUser, authenticate, create_token, get_current_user, require_admin
from banking_pipeline.compile_cobol import CobolNotInstalledError
from banking_pipeline.convert import load_json
from banking_pipeline.jobs import BatchStepError, run_jobs
from banking_pipeline.oracle import run_oracle
from banking_pipeline.paths import work_dir
from banking_pipeline.persist import (
    get_batch,
    list_batches,
    load_accounts,
    load_statements,
    load_transactions,
)
from banking_pipeline.seed import sample_accounts, sample_transactions

app = FastAPI(
    title="Andean Ledger",
    description="Legacy COBOL batch exposed as a modernization API. Demo users: admin/admin (run batch), operator/operator (read only).",
    version="2.0.0",
)


class LoginBody(BaseModel):
    username: str
    password: str


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


def _token_payload(user: TokenUser) -> dict:
    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@app.post("/api/auth/login")
def login_form(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> dict:
    user = authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _token_payload(user)


@app.post("/api/auth/login-json")
def login_json(body: LoginBody) -> dict:
    user = authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _token_payload(user)


@app.get("/api/accounts")
def accounts(_: Annotated[TokenUser, Depends(get_current_user)]) -> list[dict]:
    rows = load_accounts()
    return rows or load_json(work_dir(), "final")


@app.get("/api/accounts/{account_id}")
def account(account_id: str, _: Annotated[TokenUser, Depends(get_current_user)]) -> dict:
    rows = load_accounts() or load_json(work_dir(), "final")
    for row in rows:
        if row.get("acct_id") == account_id:
            journal = [
                item
                for item in load_json(work_dir(), "journal")
                if item.get("jrn_acct_id") == account_id
            ]
            return {**row, "activity": journal}
    raise HTTPException(status_code=404, detail="Account not found")


@app.get("/api/transactions")
def transactions(_: Annotated[TokenUser, Depends(get_current_user)]) -> list[dict]:
    return load_transactions()


@app.get("/api/transactions/rejected")
def rejected(_: Annotated[TokenUser, Depends(get_current_user)]) -> list[dict]:
    rows = load_transactions(rejected_only=True)
    return rows or load_json(work_dir(), "exceptions")


@app.get("/api/batches")
def batches(_: Annotated[TokenUser, Depends(get_current_user)]) -> list[dict]:
    return list_batches()


@app.get("/api/batches/{batch_id}")
def batch(batch_id: str, __: Annotated[TokenUser, Depends(get_current_user)]) -> dict:
    row = get_batch(batch_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return row


@app.get("/api/statements/{account_id}")
def statements(account_id: str, _: Annotated[TokenUser, Depends(get_current_user)]) -> list[dict]:
    return load_statements(account_id)


@app.get("/api/control")
def control(_: Annotated[TokenUser, Depends(get_current_user)]) -> dict:
    return load_json(work_dir(), "control") or {}


@app.get("/api/oracle")
def oracle_preview(_: Annotated[TokenUser, Depends(get_current_user)]) -> dict:
    result = run_oracle(sample_accounts(), sample_transactions())
    return {
        "accounts": len(result["final"]),
        "exceptions": len(result["exceptions"]),
        "journal": len(result["journal"]),
        "recon": result["recon"],
    }


@app.post("/api/batch/run")
def run_batch(_: Annotated[TokenUser, Depends(require_admin)]) -> dict:
    try:
        return run_jobs(compile_first=True)
    except CobolNotInstalledError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BatchStepError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "batchId": "see /api/batches",
                "step": exc.step,
                "status": "FAILED",
                "exitCode": exc.exit_code,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
