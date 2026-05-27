#!/usr/bin/env python3
"""Safe SQLite access for mounted workspaces.

The job repo often lives on a mount where direct SQLite writes can fail with
`sqlite3.OperationalError: disk I/O error`. This module serializes access,
copies the DB to a writable temp directory, runs SQLite there, then copies the
result back for write transactions.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "applications.db"


def db_path() -> Path:
    return Path(os.environ.get("JOB_DB_PATH", DEFAULT_DB_PATH)).expanduser().resolve()


def _work_root() -> Path:
    candidates = []
    if os.environ.get("JOB_DB_TMP_DIR"):
        candidates.append(Path(os.environ["JOB_DB_TMP_DIR"]))
    candidates.extend([
        Path("/var/tmp/jobdb"),
        Path("/tmp/jobdb"),
        Path(tempfile.gettempdir()) / "jobdb",
    ])

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except OSError:
            continue
    raise RuntimeError("No writable temp directory available for SQLite work DB")


def _key(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]


@contextlib.contextmanager
def safe_connection(write: bool = False) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection against a temp copy of the real DB.

    A process-wide file lock prevents concurrent agent writes from overwriting
    each other during copy-back.
    """
    source = db_path()
    root = _work_root()
    key = _key(source)
    lock_path = root / f"{key}.lock"
    work_path = root / f"{key}-{os.getpid()}.db"

    source.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        raise FileNotFoundError(f"Database not found: {source}")

    lock_mode = fcntl.LOCK_EX if write else fcntl.LOCK_SH
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), lock_mode)
        try:
            shutil.copy2(source, work_path)
            con = sqlite3.connect(work_path)
            con.row_factory = sqlite3.Row
            try:
                yield con
                if write:
                    con.commit()
            except Exception:
                if write:
                    con.rollback()
                raise
            finally:
                con.close()

            if write:
                shutil.copy2(work_path, source)
        finally:
            work_path.unlink(missing_ok=True)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
