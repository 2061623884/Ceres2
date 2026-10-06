"""Offline public harness seams only: no app import, dotenv, provider or sockets.
Dedicated Tester runs this file in a minimal env. Never runs the live entrypoint.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('live_batch', Path(__file__).with_name('run_live_batch.py'))
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)


class Response:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status
    def json(self):
        return self.body


class HarnessTests(unittest.TestCase):
    def test_named_snapshot_preserves_job_and_original_source_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.sqlite3'
            with sqlite3.connect(path) as db:
                for table in ('catalog_products','offers','stores','owners','carts','simulated_orders','aftersales_applications','aftersales_receipts'):
                    db.execute('CREATE TABLE ' + table + ' (id TEXT)')
                db.execute('CREATE TABLE memory_jobs (job_id TEXT, kind TEXT, source_id TEXT, source_json TEXT, status TEXT, error_code TEXT, created_at REAL, completed_at REAL)')
                db.execute('INSERT INTO memory_jobs VALUES (?,?,?,?,?,?,?,?)', ('job-real','extract','turn-real',json.dumps({'role':'keke','text':'synthetic preference'}),'completed',None,1,2))
                db.execute('CREATE TABLE shopping_memories (memory_id TEXT,category TEXT,domain TEXT,key TEXT,content TEXT,source TEXT,origin_role TEXT,source_id TEXT,source_quote TEXT,revision INTEGER,created_at REAL,updated_at REAL,expires_at REAL,deleted_at REAL)')
            result = batch.sanitize(batch.snapshot(path))
            self.assertEqual(result['jobs'][0]['job_id'],'job-real')
            self.assertEqual(result['jobs'][0]['source_id'],'turn-real')

    def test_coverage_results_and_untested_gates_survive_allowlist(self):
        coverage = {'purchase_refund_replay':'passed','extraction':'blocked_no_matching_automatic_record','browser':'untested','historical_repurchase':'untested','memory_correction_deletion_restart':'untested','independent_second_run':'untested'}
        self.assertEqual(batch.sanitize({'coverage':coverage}),{'coverage':coverage})

    def test_provider_diagnostic_retains_actual_status_separate_from_app_status(self):
        payload = {'http_status':502,'diagnostic':{'upstream_http_status':401,'transport_phase':'response','transport_error_class':None,'transport_error_code':None,'code':'HTTP_401','kind':'ProviderError'}}
        self.assertEqual(batch.sanitize(payload), payload)

    def test_allowlist_omits_headers_unknown_keys_and_reflected_secret(self):
        result = batch.sanitize({'message':'provider echoed synthetic-secret-value', 'headers':{'Authorization':'Bearer synthetic-secret-value'}, 'unexpected':'synthetic-secret-value', 'content':'api_key=secret-other-value', 'events':[{'type':'completed','payload':{'status':'ok'}}]}, ['synthetic-secret-value'])
        encoded = json.dumps(result)
        self.assertNotIn('synthetic-secret-value', encoded)
        self.assertNotIn('secret-other-value', encoded)
        self.assertNotIn('Authorization', encoded)
        self.assertEqual(result['omitted_fields_count'], 2)
        self.assertEqual(result['events'][0]['payload']['status'], 'ok')

    def test_run_paths_unique_and_do_not_touch_existing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'business.sqlite3'
            old.write_text('preserve')
            first, second = batch.create_run(root), batch.create_run(root)
            self.assertNotEqual(first, second)
            self.assertTrue((first / 'private-state').is_dir())
            self.assertTrue((first / 'evidence').is_dir())
            self.assertEqual(old.read_text(), 'preserve')
            self.assertFalse((first / 'private-state/business.sqlite3').exists())

    def test_inventory_excludes_env_private_state_symlinks_and_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / 'backend/app'
            app.mkdir(parents=True)
            (app / 'main.py').write_text('source')
            (app / '.env').write_text('synthetic-secret')
            (app / 'alias.py').symlink_to(app / '.env')
            private = root / 'work/live-validation/tmp/private'
            private.mkdir(parents=True)
            (private / 'sensitive.json').write_text('synthetic-secret')
            with patch.object(batch.subprocess, 'run', return_value=Mock(stdout='a'*40)):
                result = batch.inventory(root)
            self.assertEqual([r['path'] for r in result['source_inventory']], ['backend/app/main.py'])
            self.assertNotIn('synthetic-secret', json.dumps(result))

    def test_failed_check_preserves_specific_code_and_never_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            e = batch.Evidence(directory)
            e.stage = 'pi_comparison'
            with self.assertRaises(batch.BatchFailure) as caught:
                e.check('COMPARISON_NATURAL_COMPLETION', False, 'protected', 'completed')
            self.assertEqual(caught.exception.code, 'COMPARISON_NATURAL_COMPLETION')
            row = json.loads((Path(directory) / 'events.jsonl').read_text())
            self.assertEqual(row['stage'], 'pi_comparison')
            self.assertEqual(row['actual'], 'protected')
            self.assertFalse(row['passed'])

    def test_http_error_preserves_status_and_redacts_body(self):
        with tempfile.TemporaryDirectory() as directory:
            e = batch.Evidence(directory, ('synthetic-secret-value',))
            client = Mock()
            client.request.return_value = Response({'error':{'code':'PI_PROVIDER_ERROR','message':'synthetic-secret-value'}}, 502)
            journey = batch.Journey(client,e)
            with self.assertRaises(batch.BatchFailure) as caught:
                journey.call('GET','/health')
            self.assertEqual(caught.exception.code,'HTTP_502')
            evidence = (Path(directory) / 'events.jsonl').read_text()
            self.assertIn('PI_PROVIDER_ERROR', evidence)
            self.assertNotIn('synthetic-secret-value', evidence)

    def test_guide_turn_uses_actual_returned_ids_and_records_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            responses = [
                {'task_id':'task-real','state_version':3,'session_version':4,'product_cards':[{'ref':'candidate-real'}], 'plan':None},
                {'run_id':'run-real','request_id':'request-real'},
                {'events':[{'sequence':1,'type':'error','payload':{'code':'TIME_BUDGET'}}], 'status':'protected'},
                {'run_id':'run-real','status':'protected','result':{'runtime_status':'deadline'}},
                {'events':[],'status':'protected'},
            ]
            client = Mock()
            client.request.side_effect = [Response(row) for row in responses]
            journey = batch.Journey(client,batch.Evidence(directory))
            receipt = journey.turn('session-real','synthetic shopping prompt')
            self.assertEqual(receipt['status'],'protected')
            args = client.request.call_args_list
            self.assertEqual(args[1].kwargs['json']['displayed_candidate_refs'],['candidate-real'])
            self.assertEqual(args[1].kwargs['json']['expected_state_version'],3)
            self.assertIn('run-real/events',args[2].args[1])
            self.assertTrue(args[4].args[1].endswith('after_sequence=1'))

    def test_turn_budget_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Mock()
            journey = batch.Journey(client,batch.Evidence(directory))
            journey.pi_turns = 5
            with self.assertRaises(batch.BatchFailure) as caught:
                journey.turn('session-real','synthetic prompt')
            self.assertEqual(caught.exception.code,'PI_TURN_LIMIT')
            client.request.assert_not_called()

    def test_owned_cleanup_targets_only_group_created_by_supervisor(self):
        child = Mock(pid=98765)
        child.wait.side_effect = [subprocess.TimeoutExpired('synthetic',3),0]
        with patch.object(batch.os,'killpg') as kill:
            batch.terminate_owned_group(child)
        self.assertEqual([call.args[0] for call in kill.call_args_list],[98765,98765])
        self.assertEqual([call.args[1] for call in kill.call_args_list],[batch.signal.SIGTERM,batch.signal.SIGKILL])

    def test_supervisor_timeout_has_no_real_process_or_live_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Mock(pid=98765)
            child.wait.side_effect = subprocess.TimeoutExpired('synthetic',240)
            with patch.object(batch.subprocess,'Popen',return_value=child) as popen, patch.object(batch,'terminate_owned_group') as cleanup:
                code = batch.run_supervised(Path(directory))
            self.assertEqual(code,124)
            self.assertTrue(popen.call_args.kwargs['start_new_session'])
            self.assertIs(popen.call_args.kwargs['stdout'],subprocess.DEVNULL)
            self.assertIs(popen.call_args.kwargs['stderr'],subprocess.DEVNULL)
            cleanup.assert_called_once_with(child)
            report = next(Path(directory).rglob('supervisor.json'))
            self.assertEqual(json.loads(report.read_text())['status'],'timed_out')


if __name__ == '__main__':
    unittest.main()
