"""Reproduce first-use local BGE initialization across concurrent worker threads."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Barrier

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.bge import encoder  # noqa: E402

OUTPUT = Path(__file__).with_name("bge-concurrent-init-retest-2026-10-07.json")


def main() -> None:
    barrier = Barrier(2)

    def load() -> dict:
        barrier.wait()
        try:
            model = encoder()
            return {"success": True, "dimensions": model.model.config.hidden_size, "identity": id(model)}
        except Exception as exc:
            return {"success": False, "error_type": type(exc).__name__, "error_message": str(exc)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result() for future in as_completed([pool.submit(load), pool.submit(load)])]
    report = {
        "worker_count": 2,
        "success_count": sum(row["success"] for row in results),
        "single_instance": len({row.get("identity") for row in results if row["success"]}) == 1,
        "results": results,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["success_count"] != 2 or not report["single_instance"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
