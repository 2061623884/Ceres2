"""Owner-scoped local JSONL capture. Export hashes are not execution versions."""
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = 'ceres-eval-capture-v2'
# Diagnostics deliberately exclude raw SDK messages, tool arguments and provider
# output. User-visible history is exported separately to the local owner file.
DIAGNOSTIC_FIELDS = frozenset('''type kind call_id audit_id message_id outcome approved
origin elapsed_ms duration_ms model provider_host policy_ref source_name source_version
source_revision index_revision rules_version reason code name fingerprint length
input output cacheRead cacheWrite totalTokens success empty error count sequence
turn round tool_name model_calls status'''.split())
SUMMARY_FIELDS = frozenset('''policy_lookups policy_tool_lookups policy_reuses tool_starts
primary_pi_turns events_truncated interim_audit_attempts interim_messages'''.split())
VERSION_FIELDS = ('source_revision', 'build_revision', 'prompt_revision')


def diagnostic(value):
    """Project supported diagnostic data, never arbitrary provider payloads."""
    if value is None:
        return None
    if isinstance(value, list):
        return [diagnostic(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {key: diagnostic(item) for key, item in value.items()
            if key in DIAGNOSTIC_FIELDS or key in ('usage', 'cost', 'diagnostic')}


def summary(value):
    if value is None:
        return None
    result = {key: value[key] for key in SUMMARY_FIELDS if key in value}
    for key in ('policy_lookup_outcomes', 'policy_judgment', 'interim_audits'):
        if key in value:
            result[key] = diagnostic(value[key])
    return result


def export_runs(owner_id: str, output: Path):
    if not owner_id.strip():
        raise ValueError('owner_id must be explicit and nonempty')
    # Delayed imports make --help/argument errors independent of DB/config access.
    from sqlalchemy import select
    from app.core.config import ROOT_DIR
    from app.core.database import SessionLocal
    from app.models.guide import GuideTurnReceipt, GuideRunEvent, GuideMessage

    snapshot = {str(path.relative_to(ROOT_DIR)): hashlib.sha256(path.read_bytes()).hexdigest()
                for folder in ('backend/app', 'runtime/pi/src', 'data/fixtures')
                for path in sorted((ROOT_DIR / folder).rglob('*'))
                if path.is_file() and path.suffix in ('.py', '.ts', '.json')}
    records = []
    with SessionLocal() as db:
        receipts = db.scalars(select(GuideTurnReceipt).where(
            GuideTurnReceipt.owner_id == owner_id).order_by(GuideTurnReceipt.started_at, GuideTurnReceipt.run_id)).all()
        for receipt in receipts:
            result = json.loads(receipt.result_json) if receipt.result_json else {}
            runtime = result.get('runtime_events', [])
            version = result.get('runtime_version')
            events = db.scalars(select(GuideRunEvent).where(
                GuideRunEvent.run_id == receipt.run_id).order_by(GuideRunEvent.sequence)).all()
            messages = db.scalars(select(GuideMessage).where(
                GuideMessage.owner_id == owner_id, GuideMessage.session_id == receipt.session_id,
                GuideMessage.request_id == receipt.request_id).order_by(GuideMessage.sequence)).all()
            start = receipt.started_at * 1000 if receipt.started_at is not None else None
            records.append({
                'schema_version': SCHEMA_VERSION, 'owner_id': owner_id,
                'session_id': receipt.session_id, 'run_id': receipt.run_id,
                'request_id': receipt.request_id, 'status': receipt.status,
                'execution_id': receipt.execution_id, 'run_started_at_ms': start,
                'runtime_summary': summary(result.get('runtime_summary')),
                'runtime_events': diagnostic(runtime),
                'runtime_events_note': 'Diagnostic tail only; never complete run counts or usage totals.',
                'runtime_version': {key: version[key] for key in VERSION_FIELDS if key in version} if version is not None else None,
                # No stored exact navigation linkage exists in this capture stage.
                'entry_judgment': None,
                'events': [{'sequence': event.sequence, 'type': event.type,
                            'recorded_at_ms': event.recorded_at_ms,
                            'elapsed_ms': event.recorded_at_ms - start if event.recorded_at_ms is not None and start is not None else None}
                           for event in events],
                'messages': [{'message_id': message.message_id, 'role': message.role,
                              'kind': message.kind, 'content': message.content, 'sequence': message.sequence}
                             for message in messages],
                'labels': None, 'export_source_snapshot': snapshot,
                'version_note': 'Hashes describe export-time source only. Missing runtime versions, timing and usage remain unknown.',
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records), encoding='utf-8')
    return {'records': len(records), 'output': str(output), 'schema_version': SCHEMA_VERSION}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_runs(args.owner_id, args.output), ensure_ascii=False))
