"""Compile GnuCOBOL programs into repo-local binaries."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from banking_pipeline.paths import bin_dir, cobol_src, copybook_dir

PROGRAMS = ("POSTTXN", "CALCINT", "GENSTMT")


class CobolNotInstalledError(RuntimeError):
    pass


def cobc_path() -> str:
    found = shutil.which("cobc")
    if not found:
        raise CobolNotInstalledError(
            "GnuCOBOL (cobc) is not on PATH. Install it, then re-run compile."
        )
    return found


def executable_name(program: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return bin_dir() / f"{program}{suffix}"


def compile_program(program: str) -> Path:
    source = cobol_src() / f"{program}.cbl"
    if not source.exists():
        raise FileNotFoundError(source)
    out = executable_name(program)
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [
        cobc_path(),
        "-x",
        "-free",
        "-I",
        str(copybook_dir()),
        "-o",
        str(out),
        str(source),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"cobc failed for {program}:\n{completed.stdout}\n{completed.stderr}"
        )
    return out


def compile_all() -> list[Path]:
    return [compile_program(name) for name in PROGRAMS]
