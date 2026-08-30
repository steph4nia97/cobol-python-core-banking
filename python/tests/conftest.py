import pytest

from banking_pipeline.config import reset_settings_cache
from banking_pipeline.db import reset_engine


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'ledger.db'}")
    reset_settings_cache()
    reset_engine()
    yield
    reset_engine()
