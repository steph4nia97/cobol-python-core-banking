"""Command-line entry point for the banking batch pipeline."""

from __future__ import annotations

import argparse
import json

from banking_pipeline.compile_cobol import compile_all
from banking_pipeline.jobs import run_jobs
from banking_pipeline.seed import write_seed_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile and run the COBOL banking batch with Python orchestration."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=("seed", "compile", "run", "all"),
        help="seed files, compile COBOL, run jobs, or do everything (default: all)",
    )
    args = parser.parse_args(argv)

    if args.command == "seed":
        write_seed_files()
        print("Wrote cobol/data/accounts.in.dat and transactions.dat")
        return 0
    if args.command == "compile":
        paths = compile_all()
        for path in paths:
            print(f"Compiled {path}")
        return 0
    summary = run_jobs(compile_first=True)
    print(json.dumps(summary, indent=2))
    return 0
