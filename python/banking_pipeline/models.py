"""SQLAlchemy models: COBOL files remain the batch I/O; Postgres (or SQLite) is the modern store."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BatchRun(Base):
    __tablename__ = "batch_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    failed_step: Mapped[str | None] = mapped_column(String(16), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    nsf: Mapped[int] = mapped_column(Integer, default=0)
    nfnd: Mapped[int] = mapped_column(Integer, default=0)
    clsd: Mapped[int] = mapped_column(Integer, default=0)
    ityp: Mapped[int] = mapped_column(Integer, default=0)
    iamt: Mapped[int] = mapped_column(Integer, default=0)
    dup: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    recon_status: Mapped[str] = mapped_column(String(16), default="")


class AccountRow(Base):
    __tablename__ = "accounts"

    acct_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    acct_type: Mapped[str] = mapped_column(String(1))
    status: Mapped[str] = mapped_column(String(1))
    balance: Mapped[str] = mapped_column(String(20))
    rate: Mapped[str] = mapped_column(String(20))
    batch_id: Mapped[str] = mapped_column(String(32), default="")


class TransactionRow(Base):
    __tablename__ = "transactions"

    txn_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(10), index=True)
    txn_date: Mapped[int] = mapped_column(Integer)
    txn_type: Mapped[str] = mapped_column(String(1))
    amount: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), index=True)
    reject_code: Mapped[str] = mapped_column(String(4), default="")
    batch_id: Mapped[str] = mapped_column(String(32), index=True)


class RejectedTransaction(Base):
    __tablename__ = "rejected_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    txn_id: Mapped[str] = mapped_column(String(20), index=True)
    account_id: Mapped[str] = mapped_column(String(10))
    code: Mapped[str] = mapped_column(String(4))
    message: Mapped[str] = mapped_column(String(50))
    amount: Mapped[str] = mapped_column(String(20))
    batch_id: Mapped[str] = mapped_column(String(32), index=True)


class StatementRow(Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(30))
    acct_type: Mapped[str] = mapped_column(String(1))
    status: Mapped[str] = mapped_column(String(1))
    balance: Mapped[str] = mapped_column(String(20))
    interest: Mapped[str] = mapped_column(String(20))
    stmt_date: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[str] = mapped_column(String(32), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    level: Mapped[str] = mapped_column(String(8))
    step: Mapped[str] = mapped_column(String(16), default="")
    message: Mapped[str] = mapped_column(Text)
