"""Read-only aggregate of this worktree's real evaluation DB; never reads message/source text."""
import json
import sqlite3
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
DB=ROOT/'data/runtime/real-model-20261008/ceres2.sqlite3'
now=time.time()
with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    runs={r['status']:r['n'] for r in db.execute('select status,count(*) n from guide_turn_receipts group by status')}
    jobs=[dict(r) for r in db.execute('''select kind,status,count(*) n from memory_jobs
        group by kind,status order by kind,status''')]
    errors=[dict(r) for r in db.execute('''select error_code,count(*) n from memory_jobs
        where error_code is not null group by error_code order by error_code''')]
    linked=[dict(r) for r in db.execute('''select j.kind,j.status,count(*) n from memory_jobs j
        join guide_turn_receipts g on g.owner_id=j.owner_id and g.run_id=j.source_id
        group by j.kind,j.status order by j.kind,j.status''')]
    owner_counts=[r[0] for r in db.execute('''select count(*) from shopping_memories
        where source='automatic' and deleted_at is null and expires_at>? group by owner_id''',(now,))]
    event_types=[dict(r) for r in db.execute('select type,count(*) n from guide_run_events group by type order by type')]
report={
 'snapshot_epoch_seconds':round(now,1),
 'guide_runs_by_status':runs,
 'memory_jobs_by_kind_status':jobs,
 'memory_error_codes':errors,
 'memory_jobs_linked_to_guide_runs':linked,
 'automatic_memory_owner_count':len(owner_counts),
 'automatic_memory_owner_max_effective':max(owner_counts,default=0),
 'dream_threshold_eligible_owner_count':sum(1 for count in owner_counts if count>=10),
 'guide_event_type_counts':event_types,
 'memory_provider_usage':'not persisted by memory_model; token usage unknown',
}
print(json.dumps(report,ensure_ascii=False,indent=2))
