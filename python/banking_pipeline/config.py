"""Load application.yaml with environment overrides. Rates live on the account master."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from banking_pipeline.paths import repo_root


@dataclass(frozen=True)
class AuthUser:
    username: str
    password: str
    role: str


@dataclass(frozen=True)
class Settings:
    months_in_year: int
    currency: str
    statement_generation: bool
    database_url: str
    jwt_secret: str
    access_minutes: int
    users: tuple[AuthUser, ...]


def _config_path() -> Path:
    override = os.environ.get("LEDGER_CONFIG")
    if override:
        return Path(override)
    return repo_root() / "config" / "application.yaml"


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    raw = yaml.safe_load(_config_path().read_text(encoding="utf-8")) or {}
    interest = raw.get("interest") or {}
    batch = raw.get("batch") or {}
    database = raw.get("database") or {}
    auth = raw.get("auth") or {}
    users = tuple(
        AuthUser(
            username=str(row["username"]),
            password=str(row["password"]),
            role=str(row["role"]).upper(),
        )
        for row in auth.get("users") or []
    )
    return Settings(
        months_in_year=int(interest.get("monthsInYear", 12)),
        currency=str(batch.get("currency", "USD")),
        statement_generation=bool(batch.get("statementGeneration", True)),
        database_url=os.environ.get("DATABASE_URL", str(database.get("url", "sqlite:///./work/ledger.db"))),
        jwt_secret=os.environ.get("JWT_SECRET", str(auth.get("jwtSecret", "change-me"))),
        access_minutes=int(auth.get("accessMinutes", 120)),
        users=users,
    )


def reset_settings_cache() -> None:
    load_settings.cache_clear()
