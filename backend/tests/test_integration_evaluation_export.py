"""Public CLI capture contract; synthetic databases, never a running service."""
import json
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy.orm import Session
from app.core.database import Base, create_db_engine
from app.models.identity import Owner
from app.models.guide import GuideSession, GuideTurnReceipt, GuideRunEvent, GuideMessage


def cli(module, args, database=None):
    # Disable dotenv before CLI imports. Inherit Tester's offline child guard.
    bootstrap = "from app.core.config import Settings; Settings.model_config['env_file']=None; import runpy; runpy.run_module(%r,run_name='__main__')" % module
    env = dict(os.environ, DATABASE_URL='sqlite:///'+str(database) if database else 'sqlite:///:memory:')
    return subprocess.run([sys.executable, '-c', bootstrap, *args], env=env,
                          cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)


def seed(path):
    engine = create_db_engine('sqlite:///'+str(path))
    Base.metadata.create_all(engine)
    summary = {'policy_lookups': 1, 'policy_reuses': 48, 'policy_tool_lookups': 0,
               'policy_lookup_outcomes': {'success': 1, 'empty': 0, 'error': 0},
               'tool_starts': 49, 'primary_pi_turns': 5, 'policy_judgment': None,
               'events_truncated': True, 'interim_audit_attempts': 1, 'interim_messages': 0,
               'interim_audits': [{'audit_id': 'audit-1', 'outcome': 'error', 'usage': None, 'cost': None}]}
    with Session(engine) as db:
        db.add_all([Owner(id='alice'), Owner(id='bob')]); db.flush()
        db.add_all([GuideSession(session_id='a', owner_id='alice'), GuideSession(session_id='b', owner_id='bob'), GuideSession(session_id='a2', owner_id='alice')]); db.flush()
        for run, owner, session, result in [
            ('run-a', 'alice', 'a', {'runtime_summary': summary, 'runtime_events': [
                {'type': 'policy_reuse', 'outcome': 'success'},
                {'type': 'model_usage', 'kind': 'main', 'usage': None, 'cost': None,
                 'reasoning': 'SECRET_REASONING', 'api_key': 'SECRET_KEY', 'provider_output': 'SECRET_RAW'}],
                'runtime_version': {'source_revision': 'observed-old-source', 'build_revision': None}}),
            ('run-b', 'bob', 'b', {}), ('run-old', 'alice', 'a2', None)]:
            db.add(GuideTurnReceipt(run_id=run, session_id=session, owner_id=owner,
                request_id='same-request', digest='fixture', status='failed' if result is None else 'completed',
                result_json=json.dumps(result) if result is not None else None, started_at=100 if result else None))
        db.flush()
        db.add_all([GuideRunEvent(run_id='run-a', sequence=1, type='completed', recorded_at_ms=100250,
                                  payload_json=json.dumps({'runtime_summary': summary, 'provider_output':'SECRET_EVENT_RAW'})),
                    GuideRunEvent(run_id='run-old', sequence=1, type='error', recorded_at_ms=None, payload_json='{}')])
        for index, owner, session, request, content in [(1,'alice','a','same-request','Alice public answer'),
            (2,'bob','b','same-request','Bob private answer'), (3,'alice','a','other-request','Other request')]:
            db.add(GuideMessage(message_id=str(index), owner_id=owner, session_id=session,
                request_id=request, sequence=index, role='assistant', content=content))
        db.commit()
    engine.dispose()
    return summary


def test_export_cli_owner_summary_unknown_and_provenance(tmp_path):
    database = tmp_path/'synthetic.sqlite'; summary = seed(database)
    output = tmp_path/'capture.jsonl'
    result = cli('app.evaluation.export_runs', ['--owner-id','alice','--output',str(output)], database)
    assert result.returncode == 0, result.stderr
    records = {row['run_id']: row for row in map(json.loads, output.read_text().splitlines())}
    assert set(records) == {'run-a', 'run-old'}
    row = records['run-a']
    assert row['owner_id'] == 'alice' and row['session_id'] == 'a'
    assert row['runtime_summary'] == summary
    assert row['runtime_summary']['policy_reuses'] == 48
    assert len(row['runtime_events']) == 2
    assert row['runtime_version'] == {'source_revision':'observed-old-source','build_revision':None}
    assert row['export_source_snapshot'] and row['runtime_version'] != row['export_source_snapshot']
    assert row['labels'] is None and row['entry_judgment'] is None
    assert [m['content'] for m in row['messages']] == ['Alice public answer']
    assert row['events'][0]['elapsed_ms'] == 250
    old = records['run-old']
    assert old['runtime_summary'] is None and old['runtime_version'] is None
    assert old['run_started_at_ms'] is None and old['events'][0]['elapsed_ms'] is None
    assert old['labels'] is None
    text = output.read_text()
    assert 'SECRET_' not in text and 'Bob private' not in text and 'Other request' not in text


def test_export_cli_requires_explicit_owner(tmp_path):
    output = tmp_path/'capture.jsonl'
    result = cli('app.evaluation.export_runs', ['--output',str(output)])
    assert result.returncode != 0 and '--owner-id' in result.stderr
    assert not output.exists()
