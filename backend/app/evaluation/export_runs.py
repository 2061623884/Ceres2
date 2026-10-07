"""Export observed runs; unknown usage/version values are never inferred."""
import argparse
import hashlib
import json
from pathlib import Path
from sqlalchemy import select
from app.core.config import ROOT_DIR
from app.core.database import SessionLocal
from app.models.guide import GuideTurnReceipt, GuideRunEvent, GuideMessage


def export_runs(owner_id: str, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {str(path.relative_to(ROOT_DIR)):hashlib.sha256(path.read_bytes()).hexdigest()
        for folder in ('backend/app','runtime/pi/src','data/fixtures','evals')
        for path in sorted((ROOT_DIR/folder).rglob('*')) if path.is_file() and path.suffix in ('.py','.ts','.json')}
    count = 0
    with SessionLocal() as db, output.open('w') as stream:
        receipts = db.scalars(select(GuideTurnReceipt).where(GuideTurnReceipt.owner_id == owner_id).order_by(GuideTurnReceipt.started_at)).all()
        for receipt in receipts:
            result = json.loads(receipt.result_json) if receipt.result_json else None
            events = db.scalars(select(GuideRunEvent).where(GuideRunEvent.run_id == receipt.run_id).order_by(GuideRunEvent.sequence)).all()
            history = db.scalars(select(GuideMessage).where(GuideMessage.owner_id == owner_id,
                GuideMessage.session_id == receipt.session_id, GuideMessage.request_id == receipt.request_id).order_by(GuideMessage.sequence)).all()
            runtime = result.get('runtime_events', []) if result else []
            captured = {'schema_version':'ceres-eval-capture-v1', 'run_id':receipt.run_id,
                'request_id':receipt.request_id, 'status':receipt.status,
                'run_started_at_ms':receipt.started_at*1000 if receipt.started_at is not None else None,
                'input':json.loads(receipt.input_json),
                'anchor':json.loads(receipt.anchor_json), 'result':result,
                'events':[{'sequence':event.sequence,'type':event.type,'recorded_at_ms':event.recorded_at_ms,
                    'elapsed_ms':event.recorded_at_ms-receipt.started_at*1000 if event.recorded_at_ms is not None and receipt.started_at is not None else None,
                    'payload':json.loads(event.payload_json)} for event in events],
                'messages':[{'message_id':message.message_id,'role':message.role,'kind':message.kind,'content':message.content,'sequence':message.sequence} for message in history],
                'observed_usage':[event for event in runtime if event['type']=='model_usage'],
                'retrieval':[event for event in runtime if event['type'] in ('retrieval','graph_retrieval')],
                'labels':None,
                'export_source_snapshot':snapshot,
                'version_note':'Hashes describe export-time source; observed run/index versions only come from stored events. Missing versions/usage remain unknown.'}
            stream.write(json.dumps(captured, ensure_ascii=False)+'\n')
            count += 1
    return {'records':count, 'output':str(output), 'schema_version':'ceres-eval-capture-v1'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_runs(args.owner_id, args.output), ensure_ascii=False))
