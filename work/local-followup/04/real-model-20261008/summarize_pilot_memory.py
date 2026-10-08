"""Read-only aggregates for the first 20 Guide runs; never reads prose or emits IDs."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DB = ROOT / "data/runtime/real-model-20261008/ceres2.sqlite3"


def grouped(db, sql, params=()):
    return {
        str(row[0]) if row[0] is not None else "null": int(row[1])
        for row in db.execute(sql, params)
    }


def main() -> None:
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as db:
        pilot = list(db.execute(
            "select run_id,owner_id,status from guide_turn_receipts "
            "order by started_at asc,rowid asc limit 20"
        ))
        runs = [row[0] for row in pilot]
        owners = sorted({row[1] for row in pilot})
        run_marks = ",".join("?" for _ in runs)
        owner_marks = ",".join("?" for _ in owners)
        pilot_owner_auto = [row[0] for row in db.execute(
            "select count(*) from shopping_memories where owner_id in (" + owner_marks + ") "
            "and source='automatic' and deleted_at is null and expires_at>? group by owner_id",
            (*owners, time.time()),
        )]
        columns = {row[1] for row in db.execute("pragma table_info('memory_jobs')")}
        report = {
            "pilot_run_count": len(runs),
            "pilot_owner_count": len(owners),
            "pilot_guide_status": grouped(
                db,
                "select status,count(*) from guide_turn_receipts where run_id in (" + run_marks + ") group by status",
                runs,
            ),
            "pilot_extract_status": grouped(
                db,
                "select status,count(*) from memory_jobs where kind='extract' and source_id in (" + run_marks + ") group by status",
                runs,
            ),
            "pilot_extract_error_codes": grouped(
                db,
                "select error_code,count(*) from memory_jobs where kind='extract' and source_id in (" + run_marks + ") and error_code is not null group by error_code",
                runs,
            ),
            "pilot_dream_status": grouped(
                db,
                "select status,count(*) from memory_jobs where kind='dream' and owner_id in (" + owner_marks + ") group by status",
                owners,
            ),
            "pilot_active_automatic_memory": {
                "owners_with_records": len(pilot_owner_auto),
                "owners_at_or_above_10": sum(count >= 10 for count in pilot_owner_auto),
                "max_per_owner": max(pilot_owner_auto, default=0),
                "record_count": sum(pilot_owner_auto),
            },
            "all_memory_job_status": grouped(
                db, "select kind || ':' || status,count(*) from memory_jobs group by kind,status"
            ),
            "all_memory_pending_or_running": db.execute(
                "select count(*) from memory_jobs where status in ('pending','running')"
            ).fetchone()[0],
            "memory_usage_fields_persisted": bool(
                columns & {"usage", "input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens"}
            ),
            "pilot_dream_eligible_owners": sum(count >= 10 for count in pilot_owner_auto),
        }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
