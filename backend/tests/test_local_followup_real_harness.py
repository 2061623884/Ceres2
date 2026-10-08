"""Synthetic boundary tests for the isolated real-model evaluation harness."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


HARNESS_DIR = Path(__file__).resolve().parents[2] / 'work/local-followup/04/real-model-20261008'
sys.path.insert(0, str(HARNESS_DIR))
import provider_job


def _run_graph_audit(tmp_path, result):
    audit_dir = tmp_path / 'work/local-followup/04/real-model-20261008'
    audit_dir.mkdir(parents=True)
    shutil.copyfile(HARNESS_DIR / 'graph_audit.py', audit_dir / 'graph_audit.py')

    fixture_dir = tmp_path / 'data/fixtures'
    fixture_dir.mkdir(parents=True)
    (fixture_dir / 'recipes.json').write_text(json.dumps({'dishes': [{
        'dish_id': 'egg-toast', 'name': '鸡蛋吐司', 'base_people': 1,
        'required_items': [{'ingredient_id': 'egg', 'quantity_pc': 1}],
        'pantry_items': [],
    }]}), encoding='utf-8')
    (fixture_dir / 'ingredients.json').write_text(json.dumps({'ingredients': [
        {'ingredient_id': 'egg', 'kind': 'protein'},
    ]}), encoding='utf-8')

    manifest_dir = tmp_path / 'data/indexes/graphrag'
    manifest_dir.mkdir(parents=True)
    (manifest_dir / 'manifest.json').write_text(json.dumps({
        'artifacts': {}, 'output_counts': {},
    }), encoding='utf-8')
    result_dir = audit_dir / 'tmp'
    result_dir.mkdir()
    (result_dir / 'graph-global.stdout.json').write_text(json.dumps(result), encoding='utf-8')

    command_env = {
        'HOME': os.environ['HOME'],
        'PATH': os.environ.get('PATH', ''),
        'LANG': os.environ.get('LANG', 'C.UTF-8'),
    }
    return subprocess.run(
        [sys.executable, str(audit_dir / 'graph_audit.py')],
        cwd=tmp_path, env=command_env, capture_output=True, text=True, timeout=10,
    )


def test_provider_call_summary_keeps_unobserved_unknown_and_actual_zero_distinct():
    unobserved = provider_job._call_summary(None)
    assert unobserved == {
        'count': None,
        'kind_status': None,
        'provider_total_tokens_by_model': None,
    }

    unknown_usage = provider_job._call_summary([
        {'kind': 'completion', 'status': 'success', 'usage_source': 'provider',
         'model': 'fixture-model', 'usage': None},
        {'kind': 'completion', 'status': 'success', 'usage_source': 'provider',
         'model': 'fixture-model', 'usage': {}},
    ])
    assert unknown_usage['count'] == 2
    assert unknown_usage['provider_total_tokens_by_model'] == {'fixture-model': None}

    actual_zero = provider_job._call_summary([
        {'kind': 'completion', 'status': 'success', 'usage_source': 'provider',
         'model': 'fixture-model', 'usage': {'total_tokens': 0}},
    ])
    assert actual_zero['count'] == 1
    assert actual_zero['provider_total_tokens_by_model'] == {'fixture-model': 0}


def test_graph_audit_keeps_unobserved_failure_unknown_instead_of_zero(tmp_path):
    process = _run_graph_audit(tmp_path, {
        'graph_status': 'not_executed', 'error': 'KNOWLEDGE_TIMEOUT',
    })

    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report['query_wall_ms'] is None
    assert report['canonical_fact_count'] is None
    assert report['recipe_scope_exact'] is None
    assert report['required_pairs_actual'] is None
    assert report['required_pairs_exact'] is None
    assert report['quantity_source_mismatches'] is None
    assert report['egg_recipe_ids_actual'] is None
    assert report['egg_recipe_map_exact'] is None
    assert report['ingredient_kind_checks'] is None
    assert report['ingredient_kind_mismatches'] is None


def test_graph_audit_keeps_observed_empty_success_as_zero_and_evaluates_it(tmp_path):
    process = _run_graph_audit(tmp_path, {
        'graph_status': 'success',
        'query_revision': 'fixture-query-v1',
        'duration_ms': 0,
        'official_graph_calls': 0,
        'model_selected_entity_ids': [],
        'canonical_facts': [],
        'ingredient_recipes': {},
        'manifest': {'artifacts': {}, 'output_counts': {}},
    })

    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report['query_wall_ms'] == 0
    assert report['canonical_fact_count'] == 0
    assert report['recipe_scope_exact'] is False
    assert report['required_pairs_actual'] == 0
    assert report['required_pairs_exact'] is False
    assert report['quantity_source_mismatches'] == ['egg/egg-toast']


def test_graph_audit_does_not_default_missing_success_facts_to_empty(tmp_path):
    process = _run_graph_audit(tmp_path, {
        'graph_status': 'success',
        'query_revision': 'fixture-query-v1',
        'duration_ms': 10,
        'official_graph_calls': 1,
        'model_selected_entity_ids': [],
        'ingredient_recipes': {},
        'manifest': {'artifacts': {}, 'output_counts': {}},
    })

    assert process.returncode != 0


def test_provider_serve_drops_inherited_operator_settings_before_settings_load(tmp_path, monkeypatch):
    from app.core.config import Settings

    original_environment = os.environ.copy()
    fake_env_path = tmp_path / 'synthetic.env'
    fake_env_path.write_text(
        'OPENAI_BASE_URL=https://model.fixture.invalid/v1\n'
        'OPENAI_API_KEY=synthetic-test-key\n'
        'LLM_MODEL=synthetic-test-model\n'
        'LLM_MODE=live\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(provider_job, 'SOURCE_ENV', fake_env_path)
    monkeypatch.setattr(provider_job, 'RUNTIME', tmp_path / 'runtime')
    monkeypatch.setattr(provider_job, 'TMP', tmp_path / 'tmp')
    monkeypatch.setattr(provider_job, 'BOOTSTRAP', tmp_path / 'runtime-bootstrap')

    observed = {}

    def inspect_server_settings(_env):
        settings = Settings(_env_file=None)
        observed.update({
            'operator_token_configured': bool(settings.human_operator_token),
            'shopping_writes_paused': settings.shopping_writes_paused,
            'kev_configured': bool(settings.kev_base_url),
            'home': os.environ.get('HOME'),
            'http_proxy': os.environ.get('HTTP_PROXY'),
            'database_url': settings.database_url,
        })
        return 0

    monkeypatch.setattr(provider_job, 'serve', inspect_server_settings)
    monkeypatch.setattr(sys, 'argv', ['provider_job.py', 'serve'])
    expected_home = original_environment['HOME']
    try:
        os.environ.update({
            'HUMAN_OPERATOR_TOKEN': 'synthetic-host-operator-token',
            'SHOPPING_WRITES_PAUSED': 'true',
            'KEV_BASE_URL': 'https://host-setting.fixture.invalid',
            'human_operator_token': 'synthetic-lower-host-token',
            'Shopping_Writes_Paused': 'true',
            'kev_base_url': 'https://lower-host-setting.fixture.invalid',
            'HTTP_PROXY': 'http://proxy.fixture.invalid:8080',
            'HOME': expected_home,
        })
        exit_code = provider_job.main()
    finally:
        os.environ.clear()
        os.environ.update(original_environment)

    assert exit_code == 0
    assert observed == {
        'operator_token_configured': False,
        'shopping_writes_paused': False,
        'kev_configured': False,
        'home': expected_home,
        'http_proxy': 'http://proxy.fixture.invalid:8080',
        'database_url': f"sqlite:///{(tmp_path / 'runtime/ceres2.sqlite3')}",
    }
