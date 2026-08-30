from __future__ import annotations

from collections import Counter
from datetime import datetime

from banking_pipeline.db import session
from banking_pipeline.models import (
    AccountRow,
    AuditLog,
    BatchRun,
    RejectedTransaction,
    StatementRow,
    TransactionRow,
)


def next_batch_id(when: datetime | None = None) -> str:
    stamp = (when or datetime.now()).strftime("%Y%m%d")
    prefix = f"{stamp}-"
    db = session()
    try:
        count = db.query(BatchRun).filter(BatchRun.batch_id.startswith(prefix)).count()
        return f"{prefix}{count + 1:03d}"
    finally:
        db.close()


def processed_txn_ids() -> set[str]:
    db = session()
    try:
        rows = db.query(TransactionRow.txn_id).filter(TransactionRow.status == "POSTED").all()
        return {row[0] for row in rows}
    finally:
        db.close()


def write_processed_file(path, ids: set[str]) -> None:
    path.write_text("".join(f"{item}\n" for item in sorted(ids)), encoding="utf-8")


def log_audit(batch_id: str, level: str, message: str, step: str = "") -> None:
    db = session()
    try:
        db.add(
            AuditLog(
                batch_id=batch_id,
                created_at=datetime.now(),
                level=level,
                step=step,
                message=message,
            )
        )
        db.commit()
    finally:
        db.close()


def start_run(batch_id: str) -> BatchRun:
    db = session()
    try:
        run = BatchRun(
            batch_id=batch_id,
            started_at=datetime.now(),
            status="RUNNING",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    finally:
        db.close()


def finish_run(batch_id: str, **fields) -> None:
    db = session()
    try:
        run = db.query(BatchRun).filter_by(batch_id=batch_id).one()
        for key, value in fields.items():
            setattr(run, key, value)
        run.ended_at = datetime.now()
        started = run.started_at
        if started and run.ended_at:
            run.duration_ms = int((run.ended_at - started).total_seconds() * 1000)
        db.commit()
    finally:
        db.close()


def persist_batch_result(batch_id: str, converted: dict, seed_txns: list[dict]) -> None:
    posted_ids = {row.get("jrn_txn_id") for row in converted.get("journal", [])}
    rejected_by_id = {row.get("exc_txn_id"): row for row in converted.get("exceptions", [])}
    db = session()
    try:
        db.query(AccountRow).delete()
        for row in converted.get("final", []):
            db.merge(
                AccountRow(
                    acct_id=row["acct_id"],
                    name=row["acct_name"],
                    acct_type=row["acct_type"],
                    status=row["acct_status"],
                    balance=str(row["acct_balance"]),
                    rate=str(row["acct_rate"]),
                    batch_id=batch_id,
                )
            )
        for txn in seed_txns:
            txn_id = txn["TXN-ID"]
            rejected = rejected_by_id.get(txn_id)
            status = "REJECTED" if rejected else ("POSTED" if txn_id in posted_ids else "SKIPPED")
            db.merge(
                TransactionRow(
                    txn_id=txn_id,
                    account_id=txn["TXN-ACCT-ID"],
                    txn_date=int(txn["TXN-DATE"]),
                    txn_type=txn["TXN-TYPE"],
                    amount=str(txn["TXN-AMOUNT"]),
                    description=txn["TXN-DESC"],
                    status=status,
                    reject_code=(rejected.get("exc_code") or "") if rejected else "",
                    batch_id=batch_id,
                )
            )
        for row in converted.get("exceptions", []):
            db.add(
                RejectedTransaction(
                    txn_id=row.get("exc_txn_id", ""),
                    account_id=row.get("exc_acct_id", ""),
                    code=row.get("exc_code", ""),
                    message=row.get("exc_message", ""),
                    amount=str(row.get("exc_amount", "")),
                    batch_id=batch_id,
                )
            )
        for row in converted.get("statements", []):
            db.add(
                StatementRow(
                    account_id=row["stmt_acct_id"],
                    name=row["stmt_name"],
                    acct_type=row["stmt_type"],
                    status=row["stmt_status"],
                    balance=str(row["stmt_balance"]),
                    interest=str(row["stmt_interest"]),
                    stmt_date=int(row["stmt_date"]),
                    batch_id=batch_id,
                )
            )
        db.commit()
    finally:
        db.close()


def reject_counts(exceptions: list[dict]) -> dict[str, int]:
    codes = Counter((row.get("exc_code") or "").strip() for row in exceptions)
    return {
        "nsf": codes.get("NSF", 0),
        "nfnd": codes.get("NFND", 0),
        "clsd": codes.get("CLSD", 0),
        "ityp": codes.get("ITYP", 0),
        "iamt": codes.get("IAMT", 0),
        "dup": codes.get("DUP", 0),
    }


def list_batches(limit: int = 20) -> list[dict]:
    db = session()
    try:
        rows = db.query(BatchRun).order_by(BatchRun.id.desc()).limit(limit).all()
        return [_batch_dict(row) for row in rows]
    finally:
        db.close()


def get_batch(batch_id: str) -> dict | None:
    db = session()
    try:
        run = db.query(BatchRun).filter_by(batch_id=batch_id).one_or_none()
        if run is None:
            return None
        logs = db.query(AuditLog).filter_by(batch_id=batch_id).order_by(AuditLog.id).all()
        payload = _batch_dict(run)
        payload["logs"] = [
            {"level": item.level, "step": item.step, "message": item.message} for item in logs
        ]
        return payload
    finally:
        db.close()


def load_accounts() -> list[dict]:
    db = session()
    try:
        return [
            {
                "acct_id": row.acct_id,
                "acct_name": row.name,
                "acct_type": row.acct_type,
                "acct_status": row.status,
                "acct_balance": row.balance,
                "acct_rate": row.rate,
            }
            for row in db.query(AccountRow).order_by(AccountRow.acct_id)
        ]
    finally:
        db.close()


def load_transactions(rejected_only: bool = False) -> list[dict]:
    db = session()
    try:
        query = db.query(TransactionRow)
        if rejected_only:
            query = query.filter(TransactionRow.status == "REJECTED")
        return [
            {
                "txn_id": row.txn_id,
                "account_id": row.account_id,
                "txn_date": row.txn_date,
                "txn_type": row.txn_type,
                "amount": row.amount,
                "description": row.description,
                "status": row.status,
                "reject_code": row.reject_code,
                "batch_id": row.batch_id,
            }
            for row in query.order_by(TransactionRow.txn_id)
        ]
    finally:
        db.close()


def load_statements(account_id: str | None = None) -> list[dict]:
    db = session()
    try:
        query = db.query(StatementRow)
        if account_id:
            query = query.filter_by(account_id=account_id)
        return [
            {
                "account_id": row.account_id,
                "name": row.name,
                "acct_type": row.acct_type,
                "status": row.status,
                "balance": row.balance,
                "interest": row.interest,
                "stmt_date": row.stmt_date,
                "batch_id": row.batch_id,
            }
            for row in query.order_by(StatementRow.account_id)
        ]
    finally:
        db.close()


def _batch_dict(run: BatchRun) -> dict:
    return {
        "batch_id": run.batch_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "status": run.status,
        "failed_step": run.failed_step,
        "exit_code": run.exit_code,
        "processed": run.processed,
        "accepted": run.accepted,
        "rejected": run.rejected,
        "nsf": run.nsf,
        "nfnd": run.nfnd,
        "clsd": run.clsd,
        "ityp": run.ityp,
        "iamt": run.iamt,
        "dup": run.dup,
        "duration_ms": run.duration_ms,
        "recon_status": run.recon_status,
    }
