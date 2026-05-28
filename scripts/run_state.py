#!/usr/bin/env python3
"""Small JSON state helper for throttling expensive job workflow checks."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "data" / "run-state.json"


def default_state() -> dict[str, Any]:
    return {
        "last_gmail_status_scan_at": "",
        "last_greenhouse_board_scan_at": "",
        "platform_status_scan_at": {},
    }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    state = default_state()
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return state
    if not isinstance(loaded, dict):
        return state
    state.update({key: loaded.get(key, value) for key, value in state.items()})
    if not isinstance(state["platform_status_scan_at"], dict):
        state["platform_status_scan_at"] = {}
    return state


def save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = default_state()
    merged.update(state)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def gmail_after_date(state: dict[str, Any], now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    last_scan = _parse_iso(str(state.get("last_gmail_status_scan_at", "")))
    after = last_scan or (current - timedelta(days=7))
    return after.strftime("%Y/%m/%d")


def greenhouse_scan_due(state: dict[str, Any], now: datetime | None = None, days: int = 7) -> bool:
    current = now or datetime.now(timezone.utc)
    last_scan = _parse_iso(str(state.get("last_greenhouse_board_scan_at", "")))
    if last_scan is None:
        return True
    return current - last_scan >= timedelta(days=days)


def next_greenhouse_scan_date(state: dict[str, Any], days: int = 7) -> str:
    last_scan = _parse_iso(str(state.get("last_greenhouse_board_scan_at", "")))
    if last_scan is None:
        return "now"
    return (last_scan + timedelta(days=days)).date().isoformat()


def mark(key: str, path: Path = STATE_PATH) -> dict[str, Any]:
    state = load_state(path)
    state[key] = now_utc_iso()
    save_state(state, path)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Read and update job workflow run-state.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show")
    sub.add_parser("gmail-after")
    sub.add_parser("greenhouse-due")

    p = sub.add_parser("mark")
    p.add_argument("key", choices=["last_gmail_status_scan_at", "last_greenhouse_board_scan_at"])

    args = parser.parse_args()
    state = load_state()

    if args.cmd == "show":
        print(json.dumps(state, indent=2, sort_keys=True))
    elif args.cmd == "gmail-after":
        print(gmail_after_date(state))
    elif args.cmd == "greenhouse-due":
        if greenhouse_scan_due(state):
            print("due")
        else:
            print(f"skip until {next_greenhouse_scan_date(state)}")
    elif args.cmd == "mark":
        print(json.dumps(mark(args.key), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
