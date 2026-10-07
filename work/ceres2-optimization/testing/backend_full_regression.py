"""Run the frozen-source complete backend suite and save an auditable result."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
TESTING = Path(__file__).resolve().parent
RUN_ID = os.environ.get("BACKEND_SUITE_RUN_ID", "current")
LOG = TESTING / f"backend-full-regression-{RUN_ID}-2026-10-07.log"
REPORT = TESTING / f"backend-full-regression-{RUN_ID}-2026-10-07.json"


def main() -> int:
    source = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    versioned_roots = ("backend/", "frontend/", "runtime/pi/", "data/fixtures/", "evals/")
    source_records = []
    for row in status:
        relative = row[3:]
        if not relative.startswith(versioned_roots):
            continue
        path = ROOT / relative
        if path.is_file():
            source_records.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    source_snapshot = hashlib.sha256(
        json.dumps(source_records, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    command = [str(ROOT / ".venv/bin/python"), "-m", "pytest", "tests", "-q"]
    started = datetime.now(timezone.utc).isoformat()
    with LOG.open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=BACKEND, stdout=log, stderr=subprocess.STDOUT, check=False)
    content = LOG.read_bytes()
    lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    report = {
        "command": "../.venv/bin/python -m pytest tests -q (cwd=backend)",
        "exit_code": result.returncode,
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "head_commit": source,
        "source_snapshot_sha256": source_snapshot,
        "source_snapshot_file_count": len(source_records),
        "log_sha256": hashlib.sha256(content).hexdigest(),
        "log_path": str(LOG),
        "tail": lines[-50:],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "tail"}, ensure_ascii=False, indent=2))
    print("\n".join(lines[-20:]))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
