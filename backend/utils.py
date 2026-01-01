from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, Any

LOG_ROOT = Path("backend/logs")

def ensure_log_dirs() -> None:
    for d in ["LITE", "PRO", "ADVISOR", "EVALUATED"]:
        (LOG_ROOT / d).mkdir(parents=True, exist_ok=True)

def log_row(mode: str, token: str, row: Dict[str, Any]) -> str:
    ensure_log_dirs()
    path = LOG_ROOT / mode.upper() / f"{token.lower()}.csv"
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)
    return str(path)

def stream_csv(mode: str, token: str) -> str:
    path = LOG_ROOT / mode.upper() / f"{token.lower()}.csv"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
