"""Reconstruct and retain the source set hashed by a completed backend run.

The full-suite run recorded an aggregate digest only. The sole source-tree
change after its snapshot was the v1-to-v2 metadata edit in the failure intake
file: changing its version string and appending the fifth case. This script
reverses exactly those two text edits in memory, verifies the original
aggregate, and only then writes a source copy and path-to-SHA manifest.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TESTING = Path(__file__).resolve().parent
EVALS_RELATIVE = "evals/ceres2-optimization-failure-regressions.json"
EXPECTED_SNAPSHOT = "4e87c6b746f70f3dd4ce3fa6066e143775e2df9274b5e584cd317b7193195525"
EXPECTED_COUNT = 66
FREEZE_NAME = "backend-full-regression-source-freeze-current-prompt-v2-2026-10-07"
MANIFEST_NAME = "backend-full-regression-source-manifest-current-prompt-v2-2026-10-07.json"


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def reconstructed_eval_bytes(current: bytes) -> bytes:
    text = current.decode("utf-8")
    old_version = '"version": "optimization-failure-regressions-v2"'
    if text.count(old_version) != 1:
        raise RuntimeError("Expected exactly one v2 version string in failure intake")

    fifth_case = re.compile(
        r',\n    \{\n      "case_id": "interim-recipe-fact-audit",.*?\n    \}\n  \]\n\}\n\Z',
        re.DOTALL,
    )
    text, removed = fifth_case.subn("\n  ]\n}\n", text)
    if removed != 1:
        raise RuntimeError("Expected exactly one appended fifth case at end of failure intake")

    return text.replace(old_version, '"version": "optimization-failure-regressions-v1"').encode("utf-8")


def main() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    versioned_roots = ("backend/", "frontend/", "runtime/pi/", "data/fixtures/", "evals/")
    paths: list[str] = []
    for row in status:
        relative = row[3:]
        if relative.startswith(versioned_roots) and (ROOT / relative).is_file():
            paths.append(relative)

    if len(paths) != EXPECTED_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_COUNT} source files; found {len(paths)}")
    if paths.count(EVALS_RELATIVE) != 1:
        raise RuntimeError("Failure intake must occur exactly once in source records")

    eval_path = ROOT / EVALS_RELATIVE
    reconstructed_eval = reconstructed_eval_bytes(eval_path.read_bytes())
    records: list[tuple[str, str]] = []
    source_contents: dict[str, bytes] = {}
    for relative in paths:
        content = reconstructed_eval if relative == EVALS_RELATIVE else (ROOT / relative).read_bytes()
        source_contents[relative] = content
        records.append((relative, sha256(content)))

    aggregate = sha256(json.dumps(records, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    print(json.dumps({"source_count": len(records), "reconstructed_snapshot_sha256": aggregate}, indent=2))
    if aggregate != EXPECTED_SNAPSHOT:
        raise RuntimeError(
            "Reconstructed aggregate did not match the run record; no source freeze was written"
        )

    freeze_root = TESTING / "tmp" / FREEZE_NAME
    if freeze_root.exists():
        shutil.rmtree(freeze_root)
    for relative, content in source_contents.items():
        destination = freeze_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    manifest = {
        "run_report": "work/ceres2-optimization/testing/backend-full-regression-current-prompt-v2-2026-10-07.json",
        "head_commit": "b118dbea3852026c6a04c790b1e27df67c3c9c18",
        "source_snapshot_sha256": aggregate,
        "source_snapshot_file_count": len(records),
        "reconstruction": (
            "Reconstructed after the run from the current changed-file set. "
            "In a temporary copy only, reverted the failure-intake version string "
            "from v2 to v1 and removed the appended fifth interim-recipe-fact-audit case. "
            "The aggregate matched the run report exactly; current source was untouched."
        ),
        "frozen_source_copy": f"work/ceres2-optimization/testing/tmp/{FREEZE_NAME}/",
        "files": [{"path": path, "sha256": digest} for path, digest in records],
    }
    (TESTING / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"freeze_root": str(freeze_root), "manifest": MANIFEST_NAME}, indent=2))


if __name__ == "__main__":
    main()
