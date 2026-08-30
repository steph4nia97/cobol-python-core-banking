"""Run the COBOL job stream in order: POSTTXN -> CALCINT -> GENSTMT."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from banking_pipeline.compile_cobol import PROGRAMS, compile_all, executable_name
from banking_pipeline.convert import convert_work_files
from banking_pipeline.paths import data_dir, work_dir
from banking_pipeline.seed import write_seed_files


def _clear_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def prepare_work() -> Path:
    write_seed_files()
    work = work_dir()
    _clear_dir(work)
    shutil.copy2(data_dir() / "accounts.in.dat", work / "accounts.in.dat")
    shutil.copy2(data_dir() / "transactions.dat", work / "transactions.dat")
    return work


def run_program(program: str, work: Path) -> None:
    binary = executable_name(program)
    if not binary.exists():
        raise FileNotFoundError(f"Compiled program missing: {binary}")
    completed = subprocess.run(
        [str(binary)],
        cwd=work,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{program} failed with code {completed.returncode}:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def run_jobs(compile_first: bool = True) -> dict:
    if compile_first:
        compile_all()
    work = prepare_work()
    for program in PROGRAMS:
        run_program(program, work)
    converted = convert_work_files(work)
    summary = {
        "work_dir": str(work),
        "programs": list(PROGRAMS),
        "accounts": len(converted["final"]),
        "exceptions": len(converted["exceptions"]),
        "statements": len(converted["statements"]),
    }
    (work / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
