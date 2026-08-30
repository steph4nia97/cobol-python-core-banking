from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from banking_pipeline.config import load_settings
from banking_pipeline.models import Base

_engine: Engine | None = None
_Session: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _Session
    if _engine is None:
        settings = load_settings()
        url = settings.database_url
        parsed = make_url(url)
        if parsed.drivername.startswith("sqlite") and parsed.database and parsed.database != ":memory:":
            Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False} if parsed.drivername.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, connect_args=connect_args)
        Base.metadata.create_all(_engine)
        _Session = sessionmaker(_engine, expire_on_commit=False, future=True)
    return _engine


def session() -> Session:
    get_engine()
    assert _Session is not None
    return _Session()


def reset_engine() -> None:
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None
