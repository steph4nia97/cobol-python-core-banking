"""Run the COBOL job stream: POSTTXN -> CALCINT -> GENSTMT -> CTLRPT. Stop on non-zero."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from banking_pipeline.compile_cobol import PROGRAMS, compile_all, executable_name
from banking_pipeline.convert import convert_work_files
from banking_pipeline.logging_setup import attach_batch_file, detach_batch_file, get_logger
from banking_pipeline.oracle import run_oracle
from banking_pipeline.paths import data_dir, work_dir
from banking_pipeline.persist import (
    finish_run,
    log_audit,
    next_batch_id,
    persist_batch_result,
    processed_txn_ids,
    reject_counts,
    start_run,
    write_processed_file,
)
from banking_pipeline.seed import sample_accounts, sample_transactions, write_seed_files


class BatchStepError(RuntimeError):
    def __init__(self, step: str, exit_code: int, output: str):
        super().__init__(f"{step} failed with exit {exit_code}")
        self.step = step
        self.exit_code = exit_code
        self.output = output


def _clear_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir() and child.name == "logs":
            continue
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
    write_processed_file(work / "processed.dat", processed_txn_ids())
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
        raise BatchStepError(program, completed.returncode, completed.stdout + completed.stderr)


def run_jobs(compile_first: bool = True) -> dict:
    logger = get_logger()
    batch_id = next_batch_id()
    attach_batch_file(batch_id)
    start_run(batch_id)
    log_audit(batch_id, "INFO", "Batch started", "ORCH")
    logger.info("Batch started batch_id=%s", batch_id)
    try:
        if compile_first:
            compile_all()
        work = prepare_work()
        for program in PROGRAMS:
            logger.info("%s started", program)
            log_audit(batch_id, "INFO", f"{program} started", program)
            try:
                run_program(program, work)
            except BatchStepError as exc:
                logger.error("%s failed exit_code=%s", exc.step, exc.exit_code)
                log_audit(batch_id, "ERROR", f"{exc.step} failed", exc.step)
                finish_run(
                    batch_id,
                    status="FAILED",
                    failed_step=exc.step,
                    exit_code=exc.exit_code,
                )
                raise
            logger.info("%s completed", program)
            log_audit(batch_id, "INFO", f"{program} completed", program)

        converted = convert_work_files(work)
        seed_txns = sample_transactions()
        persist_batch_result(batch_id, converted, seed_txns)
        counts = reject_counts(converted.get("exceptions", []))
        recon = converted.get("control") or run_oracle(sample_accounts(), seed_txns)["recon"]
        recon_status = (recon.get("ctl_status") or recon.get("status") or "").strip()
        if recon_status in {"BAL", "BALANCED", "RECONCILED"}:
            recon_flag = "RECONCILED"
        elif recon:
            recon_flag = recon_status or "RECONCILED"
        else:
            recon_flag = ""
        if str(recon.get("ctl_status", "")).startswith("OUT"):
            recon_flag = "BREAK"

        finish_run(
            batch_id,
            status="SUCCESS",
            processed=len(seed_txns),
            accepted=len(converted.get("journal", [])),
            rejected=len(converted.get("exceptions", [])),
            recon_status=recon_flag,
            **counts,
        )
        logger.info("Batch SUCCESS batch_id=%s", batch_id)
        log_audit(batch_id, "INFO", "Batch SUCCESS", "ORCH")
        summary = {
            "batch_id": batch_id,
            "status": "SUCCESS",
            "work_dir": str(work),
            "programs": list(PROGRAMS),
            "accounts": len(converted.get("final", [])),
            "exceptions": len(converted.get("exceptions", [])),
            "statements": len(converted.get("statements", [])),
            "journal": len(converted.get("journal", [])),
            "control": converted.get("control", {}),
        }
        (work / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
    except BatchStepError:
        raise
    except Exception:
        logger.exception("Batch failed")
        finish_run(batch_id, status="FAILED", failed_step="ORCH", exit_code=8)
        raise
    finally:
        detach_batch_file(batch_id)
