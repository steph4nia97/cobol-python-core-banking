"""Convert COBOL fixed-width outputs into JSON using the copybooks."""

from __future__ import annotations

import json
from pathlib import Path

from banking_pipeline.copybook import load_copybook, pythonize, read_records
from banking_pipeline.paths import copybook_dir


def convert_work_files(work: Path) -> dict:
    books = copybook_dir()
    acct = load_copybook(books / "ACCTREC.cpy")
    exc = load_copybook(books / "EXCREC.cpy")
    interest = load_copybook(books / "INTREC.cpy")
    stmt = load_copybook(books / "STMTREC.cpy")
    journal = load_copybook(books / "JRNREC.cpy")
    control = load_copybook(books / "CTLREC.cpy")

    control_rows = [pythonize(r) for r in read_records(control, work / "control.dat")]
    payload: dict = {
        "posted": [pythonize(r) for r in read_records(acct, work / "accounts.posted.dat")],
        "final": [pythonize(r) for r in read_records(acct, work / "accounts.final.dat")],
        "exceptions": [pythonize(r) for r in read_records(exc, work / "exceptions.dat")],
        "interest": [pythonize(r) for r in read_records(interest, work / "interest.dat")],
        "statements": [pythonize(r) for r in read_records(stmt, work / "statements.dat")],
        "journal": [pythonize(r) for r in read_records(journal, work / "journal.dat")],
        "control": control_rows[0] if control_rows else {},
    }
    json_dir = work / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in payload.items():
        (json_dir / f"{name}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return payload


def load_json(work: Path, name: str):
    path = work / "json" / f"{name}.json"
    if not path.exists():
        return [] if name != "control" else {}
    return json.loads(path.read_text(encoding="utf-8"))
