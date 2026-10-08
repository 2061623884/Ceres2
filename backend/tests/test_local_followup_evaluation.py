"""Public CLI comparison of owner-scoped captures in explicit batch JSON."""
import json
import os
from pathlib import Path
import subprocess
import sys


def capture(owner_id, run_id, session_id, request_id, runtime_version, labels):
    return {
        'schema_version': 'ceres-eval-capture-v2',
        'owner_id': owner_id,
        'session_id': session_id,
        'run_id': run_id,
        'request_id': request_id,
        'status': 'completed',
        'execution_id': f'execution-{run_id}',
        'run_started_at_ms': None,
        'runtime_summary': None,
        'runtime_events': [],
        'runtime_version': runtime_version,
        'entry_judgment': None,
        'events': [],
        'messages': [],
        'labels': labels,
        'export_source_snapshot': {'backend/app/example.py': f'export-only-{run_id}'},
    }


def annotation(owner_id, run_id, verdict):
    return {
        'schema_version': 'ceres-run-annotation-v2',
        'owner_id': owner_id,
        'run_id': run_id,
        'verdict': verdict,
        'error_type': 'dialogue' if verdict == 'fail' else 'none',
        'severity': 'major' if verdict == 'fail' else 'none',
        'expected_behavior': 'Follow the public scenario contract',
        'rationale': 'Explicit human review for the public development case',
        'reviewer': 'evaluation-reviewer',
        'reviewed_at': '2026-10-08T00:00:00Z',
    }


def batch(case_set, cases):
    return {
        'schema_version': 'ceres-local-followup-batch-v1',
        'case_set': case_set,
        'cases': cases,
    }


def test_compare_batch_cli_pairs_cases_and_keeps_unreviewed_quality_unknown(tmp_path):
    baseline_version = {
        'source_revision': 'source-baseline',
        'build_revision': None,
        'prompt_revision': 'prompt-baseline',
        'source_scope': 'disk_at_admission',
        'build_scope': None,
        'captured_at_ms': None,
        'loaded_code_equivalence': 'unknown',
    }
    candidate_version = {
        'source_revision': 'source-candidate',
        'build_revision': 'build-candidate',
        'prompt_revision': None,
        'source_scope': 'disk_at_admission',
        'build_scope': None,
        'captured_at_ms': None,
        'loaded_code_equivalence': 'unknown',
    }
    baseline = tmp_path / 'baseline.json'
    candidate = tmp_path / 'candidate.json'
    report_path = tmp_path / 'comparison.json'

    baseline_set = {'version': 'public-dev-v1', 'sha256': 'baseline-case-set-sha'}
    candidate_set = {'version': 'public-dev-v1', 'sha256': 'candidate-case-set-sha'}
    baseline.write_text(json.dumps(batch(baseline_set, [
        {'case_id': 'dev-case-01', 'capture': capture('baseline-owner-01', 'base-01',
            'baseline-session-01', 'baseline-request-01', baseline_version,
            annotation('baseline-owner-01', 'base-01', 'pass'))},
        {'case_id': 'dev-case-02', 'capture': capture('baseline-owner-02', 'base-02',
            'baseline-session-02', 'baseline-request-02', baseline_version, None)},
    ])), encoding='utf-8')
    candidate.write_text(json.dumps(batch(candidate_set, [
        {'case_id': 'dev-case-01', 'capture': capture('candidate-owner-01', 'candidate-01',
            'candidate-session-01', 'candidate-request-01', candidate_version,
            annotation('candidate-owner-01', 'candidate-01', 'fail'))},
        # Completion is a business/run status, not evidence of response quality.
        {'case_id': 'dev-case-02', 'capture': capture('candidate-owner-02', 'candidate-02',
            'candidate-session-02', 'candidate-request-02', candidate_version, None)},
    ])), encoding='utf-8')

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.compare_runs',
         '--baseline', str(baseline),
         '--candidate', str(candidate),
         '--output', str(report_path)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert report['schema_version'] == 'ceres-eval-comparison-v1'
    assert report['case_sets'] == {'baseline': baseline_set, 'candidate': candidate_set}
    pairs = {row['case_id']: row for row in report['pairs']}
    assert set(pairs) == {'dev-case-01', 'dev-case-02'}
    reviewed = pairs['dev-case-01']
    assert reviewed['baseline']['run_id'] == 'base-01'
    assert reviewed['baseline']['owner_id'] == 'baseline-owner-01'
    assert reviewed['baseline']['quality_verdict'] == 'pass'
    assert reviewed['candidate']['run_id'] == 'candidate-01'
    assert reviewed['candidate']['owner_id'] == 'candidate-owner-01'
    assert reviewed['candidate']['quality_verdict'] == 'fail'
    unreviewed = pairs['dev-case-02']
    assert unreviewed['baseline']['quality_verdict'] == 'unknown'
    assert unreviewed['candidate']['quality_verdict'] == 'unknown'
    assert unreviewed['candidate']['runtime_version'] == candidate_version
    assert 'export-only-' not in report_path.read_text(encoding='utf-8')


def test_compare_batch_cli_pairs_trials_and_preserves_null_capture_outcomes(tmp_path):
    baseline_path = tmp_path / 'baseline.json'
    candidate_path = tmp_path / 'candidate.json'
    output = tmp_path / 'comparison.json'
    baseline_set = {'version': 'public-v1', 'sha256': 'baseline-input-sha'}
    candidate_set = {'version': 'public-v1', 'sha256': 'candidate-input-sha'}
    execution_ids = [
        'dev-case-01:trial:1', 'dev-case-01:trial:2', 'dev-case-02:trial:1',
    ]
    plan = [
        {'case_id': case_id, 'trial': trial, 'execution_id': execution_id}
        for case_id, trial, execution_id in (
            ('dev-case-01', 1, execution_ids[0]),
            ('dev-case-01', 2, execution_ids[1]),
            ('dev-case-02', 1, execution_ids[2]),
        )
    ]
    baseline_version = {
        'source_revision': 'baseline-source', 'build_revision': None,
        'prompt_revision': None, 'source_scope': 'disk_at_admission',
        'build_scope': None, 'captured_at_ms': None,
        'loaded_code_equivalence': 'unknown',
    }
    candidate_version = {**baseline_version, 'source_revision': 'candidate-source'}
    baseline_batch = batch(baseline_set, [
        {'case_id': 'dev-case-01', 'trial': 1, 'execution_id': execution_ids[0],
         'outcome': 'guide_run', 'capture': capture(
             'base-owner-1', 'base-run-1', 'base-session-1', execution_ids[0],
             baseline_version, annotation('base-owner-1', 'base-run-1', 'pass'))},
        {'case_id': 'dev-case-01', 'trial': 2, 'execution_id': execution_ids[1],
         'outcome': 'runner_failed', 'capture': None},
        {'case_id': 'dev-case-02', 'trial': 1, 'execution_id': execution_ids[2],
         'outcome': 'role_choice_required', 'capture': None,
         'navigation': {'status': 'switch'}},
    ])
    candidate_batch = batch(candidate_set, [
        {'case_id': 'dev-case-01', 'trial': 1, 'execution_id': execution_ids[0],
         'outcome': 'guide_run', 'capture': capture(
             'candidate-owner-1', 'candidate-run-1', 'candidate-session-1', execution_ids[0],
             candidate_version, annotation('candidate-owner-1', 'candidate-run-1', 'fail'))},
        {'case_id': 'dev-case-01', 'trial': 2, 'execution_id': execution_ids[1],
         'outcome': 'not_run', 'capture': None},
        {'case_id': 'dev-case-02', 'trial': 1, 'execution_id': execution_ids[2],
         'outcome': 'role_choice_required', 'capture': None,
         'navigation': {'status': 'switch'}},
    ])
    baseline_batch['plan'] = plan
    candidate_batch['plan'] = plan
    baseline_path.write_text(json.dumps(baseline_batch, ensure_ascii=False), encoding='utf-8')
    candidate_path.write_text(json.dumps(candidate_batch, ensure_ascii=False), encoding='utf-8')

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.compare_runs',
         '--baseline', str(baseline_path), '--candidate', str(candidate_path),
         '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['same_input'] is False
    assert report['case_sets'] == {'baseline': baseline_set, 'candidate': candidate_set}
    pairs = {row['execution_id']: row for row in report['pairs']}
    assert set(pairs) == set(execution_ids)
    reviewed = pairs[execution_ids[0]]
    assert reviewed['case_id'] == 'dev-case-01' and reviewed['trial'] == 1
    assert reviewed['baseline']['owner_id'] == 'base-owner-1'
    assert reviewed['baseline']['run_id'] == 'base-run-1'
    assert reviewed['baseline']['quality_verdict'] == 'pass'
    assert reviewed['candidate']['owner_id'] == 'candidate-owner-1'
    assert reviewed['candidate']['run_id'] == 'candidate-run-1'
    assert reviewed['candidate']['quality_verdict'] == 'fail'
    failed = pairs[execution_ids[1]]
    assert failed['baseline']['outcome'] == 'runner_failed'
    assert failed['baseline']['quality_verdict'] == 'unknown'
    assert failed['candidate']['outcome'] == 'not_run'
    assert failed['candidate']['quality_verdict'] == 'unknown'
    waiting = pairs[execution_ids[2]]
    assert waiting['baseline']['outcome'] == 'role_choice_required'
    assert waiting['baseline']['owner_id'] is None and waiting['baseline']['run_id'] is None
    assert waiting['baseline']['quality_verdict'] == 'unknown'


def test_compare_batch_cli_exposes_all_run_labels_and_last_run_quality_scope(tmp_path):
    baseline_path = tmp_path / 'baseline.json'
    candidate_path = tmp_path / 'candidate.json'
    output = tmp_path / 'comparison.json'
    case_set = {'version': 'public-v2', 'sha256': 'same-public-case-set-sha'}
    baseline_version = {
        'source_revision': 'baseline-source', 'build_revision': None,
        'prompt_revision': None, 'source_scope': 'disk_at_admission',
        'build_scope': None, 'captured_at_ms': None,
        'loaded_code_equivalence': 'unknown',
    }
    candidate_version = {**baseline_version, 'source_revision': 'candidate-source'}

    def multirun_row(owner_id, prefix, runtime_version, verdicts):
        runs = [
            capture(owner_id, f'{prefix}-first', f'{owner_id}-session', 'turn-1',
                    runtime_version, annotation(owner_id, f'{prefix}-first', verdicts[0])),
            capture(owner_id, f'{prefix}-middle', f'{owner_id}-session', 'turn-2',
                    runtime_version, None),
            capture(owner_id, f'{prefix}-last', f'{owner_id}-session', 'turn-3',
                    runtime_version, annotation(owner_id, f'{prefix}-last', verdicts[1])),
        ]
        return {
            'case_id': 'multi-turn-case', 'outcome': 'guide_run',
            'capture': runs[-1], 'captures': runs,
        }

    baseline_path.write_text(json.dumps(batch(case_set, [
        multirun_row('baseline-multi-owner', 'baseline', baseline_version, ('fail', 'pass')),
    ]), ensure_ascii=False), encoding='utf-8')
    candidate_path.write_text(json.dumps(batch(case_set, [
        multirun_row('candidate-multi-owner', 'candidate', candidate_version, ('pass', 'fail')),
    ]), ensure_ascii=False), encoding='utf-8')

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.compare_runs',
         '--baseline', str(baseline_path), '--candidate', str(candidate_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    pair = json.loads(output.read_text(encoding='utf-8'))['pairs'][0]
    assert pair['baseline']['quality_verdict'] == 'pass'
    assert pair['baseline']['quality_scope'] == 'last_guide_run'
    assert pair['baseline']['human_run_labels'] == [
        {'owner_id': 'baseline-multi-owner', 'run_id': 'baseline-first', 'verdict': 'fail'},
        {'owner_id': 'baseline-multi-owner', 'run_id': 'baseline-middle', 'verdict': None},
        {'owner_id': 'baseline-multi-owner', 'run_id': 'baseline-last', 'verdict': 'pass'},
    ]
    assert pair['candidate']['quality_verdict'] == 'fail'
    assert pair['candidate']['human_run_labels'][-1] == {
        'owner_id': 'candidate-multi-owner', 'run_id': 'candidate-last', 'verdict': 'fail',
    }


def test_evaluation_report_cli_keeps_denominators_multirun_timing_and_usage_unknown(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'report-aggregation-v1',
        'cases': [
            {
                'case_id': 'core-multiturn', 'message': '先看当前方案。',
                'category': 'purchase_planning', 'scenario_family': 'core-multiturn',
                'split': 'regression', 'core': True,
                'expected_behavior': '逐轮检查明确动作与计划。',
                'fact_sources': ['data/fixtures/products.json#demo:snack-original-potato-chips-70g-bag'],
                'steps': [{'op': 'turn', 'message': '继续检查当前方案。'}],
                'checks': [],
            },
            {
                'case_id': 'policy-not-run', 'message': '一般价格以什么为准？',
                'category': 'policy', 'scenario_family': 'planned-not-run',
                'split': 'regression', 'core': False,
                'expected_behavior': '按当前Offer说明价格依据。',
                'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
                'checks': [],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    plan = [
        {'case_id': 'core-multiturn', 'trial': trial,
         'execution_id': f'core-multiturn:trial:{trial}'}
        for trial in (1, 2, 3)
    ] + [
        {'case_id': 'policy-not-run', 'trial': 1, 'execution_id': 'policy-not-run:trial:1'},
    ]
    timings = [
        [
            {'first_interim_ms': 100, 'first_final_ms': 200, 'stream_complete_ms': 300},
            {'first_interim_ms': 400, 'first_final_ms': 500, 'stream_complete_ms': 600},
        ],
        [
            {'first_interim_ms': 200, 'first_final_ms': 250, 'stream_complete_ms': 350},
            {'first_interim_ms': 800, 'first_final_ms': 850, 'stream_complete_ms': 900},
        ],
        [
            {'first_interim_ms': 1000, 'first_final_ms': 1100, 'stream_complete_ms': 1300},
            {'first_interim_ms': 1200, 'first_final_ms': 1300, 'stream_complete_ms': 1500},
        ],
    ]

    def complete_summary(total_tokens):
        return {
            'provider_calls_complete': True,
            'provider_records_truncated': False,
            'provider_calls': {
                'primary_pi': {
                    'started': 1, 'completed': 1, 'usage_observed': 1,
                    'usage_missing': 0,
                    'observed_usage': {
                        'promptTokens': total_tokens - 5,
                        'completionTokens': 5,
                        'totalTokens': total_tokens,
                    },
                    'usage_complete': True, 'cost': None,
                },
            },
        }

    core_rows = []
    score_rows = []
    for trial, step_timings in enumerate(timings, start=1):
        execution_id = f'core-multiturn:trial:{trial}'
        owner_id = f'owner-trial-{trial}'
        run_captures = [
            capture(owner_id, f'{execution_id}-run-{step_index}', f'{owner_id}-session',
                    f'{execution_id}:step:{step_index}', None, None)
            for step_index in (0, 1)
        ]
        run_captures[0]['status'] = run_captures[1]['status'] = 'waiting_confirmation'
        if trial == 1:
            run_captures[0]['labels'] = annotation(owner_id, run_captures[0]['run_id'], 'fail')
            run_captures[1]['labels'] = annotation(owner_id, run_captures[1]['run_id'], 'pass')
            run_captures[0]['runtime_summary'] = complete_summary(10)
            run_captures[1]['runtime_summary'] = complete_summary(15)
            human_verdict = 'pass'
            human_labels = [
                {'owner_id': owner_id, 'run_id': run_captures[0]['run_id'], 'verdict': 'fail'},
                {'owner_id': owner_id, 'run_id': run_captures[1]['run_id'], 'verdict': 'pass'},
            ]
            business_verdict = 'pass'
        elif trial == 2:
            run_captures[0]['runtime_summary'] = {
                'provider_calls_complete': False,
                'provider_records_truncated': True,
                'provider_calls': {
                    'primary_pi': {
                        'started': 1, 'completed': 1, 'usage_observed': 0,
                        'usage_missing': 1, 'observed_usage': None,
                        'usage_complete': False, 'cost': None,
                    },
                },
            }
            human_verdict = None
            human_labels = [
                {'owner_id': owner_id, 'run_id': row['run_id'], 'verdict': None}
                for row in run_captures
            ]
            business_verdict = 'unknown'
        else:
            run_captures[0]['labels'] = annotation(owner_id, run_captures[0]['run_id'], 'needs_review')
            run_captures[0]['runtime_events'] = [{'provider_calls': 99, 'observed_usage': {'totalTokens': 999}}]
            run_captures[1]['runtime_events'] = [{'provider_calls': 99, 'observed_usage': {'totalTokens': 999}}]
            human_verdict = None
            human_labels = [
                {'owner_id': owner_id, 'run_id': run_captures[0]['run_id'], 'verdict': 'needs_review'},
                {'owner_id': owner_id, 'run_id': run_captures[1]['run_id'], 'verdict': None},
            ]
            business_verdict = 'pass'

        step_rows = [
            {
                'index': step_index, 'op': 'turn',
                'before': {'cart': {'items': []}}, 'after': {'cart': {'items': []}},
                'capture': run_captures[step_index], 'timing': step_timings[step_index],
                'timing_source': 'client_monotonic_from_run_post_start',
                'timing_run_id': run_captures[step_index]['run_id'],
            }
            for step_index in (0, 1)
        ]
        core_rows.append({
            'case_id': 'core-multiturn', 'trial': trial, 'execution_id': execution_id,
            'outcome': 'guide_run', 'capture': json.loads(json.dumps(run_captures[-1])),
            'captures': run_captures, 'steps': step_rows,
            'timing': step_timings[0], 'timing_run_id': run_captures[0]['run_id'],
        })
        score_rows.append({
            'case_id': 'core-multiturn', 'trial': trial, 'execution_id': execution_id,
            'outcome': 'guide_run', 'business_verdict': business_verdict,
            'human_quality': human_verdict, 'human_quality_scope': 'last_guide_run',
            'human_run_labels': human_labels,
        })

    missing = {
        'case_id': 'policy-not-run', 'trial': 1, 'execution_id': 'policy-not-run:trial:1',
        'outcome': 'not_run', 'capture': None, 'captures': [], 'before': None, 'after': None,
        'timing': None,
    }
    source_batch = batch(case_set, [*core_rows, missing])
    source_batch['plan'] = plan
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    scores_path = tmp_path / 'score.json'
    scores_path.write_text(json.dumps({
        'schema_version': 'ceres-local-followup-score-v1',
        'case_set': case_set,
        'batch_sha256': hashlib.sha256(batch_path.read_bytes()).hexdigest(),
        'counts': {
            'planned': 4, 'attempted': 3, 'guide_run': 3, 'role_wait': 0,
            'preparation_failed': 0, 'runner_failed': 0, 'not_run': 1,
        },
        'cases': [*score_rows, {
            'case_id': 'policy-not-run', 'trial': 1,
            'execution_id': 'policy-not-run:trial:1', 'outcome': 'not_run',
            'business_verdict': 'unknown', 'human_quality': None,
            'human_quality_scope': 'last_guide_run', 'human_run_labels': [],
        }],
    }, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'report.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.report_batch',
         '--cases', str(cases_path), '--batch', str(batch_path),
         '--score', str(scores_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['counts']['planned'] == 4 and report['counts']['not_run'] == 1
    assert report['business_verdicts'] == {'pass': 2, 'fail': 0, 'unknown': 2}
    assert report['categories']['purchase_planning'] == {
        'planned': 3, 'attempted': 3,
        'business_verdicts': {'pass': 2, 'fail': 0, 'unknown': 1},
    }
    assert report['categories']['policy'] == {
        'planned': 1, 'attempted': 0,
        'business_verdicts': {'pass': 0, 'fail': 0, 'unknown': 1},
    }
    assert report['core_cases'] == [{
        'case_id': 'core-multiturn', 'planned': 3, 'attempted': 3,
        'business_verdicts': {'pass': 2, 'fail': 0, 'unknown': 1},
        'three_trials_business_pass': False,
    }]
    assert report['latency_ms']['first_interim_ms'] == {
        'samples': 6, 'p50': 400, 'p95': 1200,
    }
    assert report['latency_ms']['first_final_ms'] == {
        'samples': 6, 'p50': 500, 'p95': 1300,
    }
    assert report['latency_ms']['stream_complete_ms'] == {
        'samples': 6, 'p50': 600, 'p95': 1500,
    }
    assert report['human_runs'] == {
        'reviewed': 3, 'unreviewed': 3,
        'verdicts': {'pass': 1, 'fail': 1, 'needs_review': 1},
        'failed_error_types': {'dialogue': 1},
    }
    assert report['provider_usage'] == {
        'coverage': {
            'guide_runs': 6, 'provider_call_summary_complete_runs': 2,
            'observed_usage_complete_runs': 2,
        },
        'provider_call_counts_complete': False,
        'calls_by_stage': None,
        'observed_usage_complete': False,
        'observed_usage': None,
        'cost': None,
    }


def test_report_cli_separates_run_status_critical_deadline_and_unannotated_usefulness(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'report-terminal-metrics-v1',
        'cases': [
            {
                'case_id': 'core-three-trials', 'message': '请给出购买方案。',
                'category': 'purchase_planning', 'scenario_family': 'core-three-trials',
                'split': 'regression', 'core': True,
                'expected_behavior': '逐次保留业务、运行状态和各轮时延证据。',
                'fact_sources': [], 'steps': [{'op': 'turn', 'message': '继续说明。'}],
                'checks': [],
            },
            {
                'case_id': 'legacy-single-turn', 'message': '价格依据是什么？',
                'category': 'policy', 'scenario_family': 'legacy-timing',
                'split': 'regression', 'core': False,
                'expected_behavior': '保留旧版单轮顶层 timing。',
                'fact_sources': [], 'checks': [],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }

    plan = [
        {'case_id': 'core-three-trials', 'trial': trial,
         'execution_id': f'core-three-trials:trial:{trial}'}
        for trial in (1, 2, 3)
    ] + [
        {'case_id': 'legacy-single-turn', 'trial': 1,
         'execution_id': 'legacy-single-turn:trial:1'},
    ]
    trial_turns = {
        1: [
            ('completed', {'first_interim_ms': 30, 'first_final_ms': 60, 'stream_complete_ms': 100}),
            ('waiting_confirmation', {'first_interim_ms': 500, 'first_final_ms': 900, 'stream_complete_ms': 16000}),
        ],
        2: [
            ('protected', None),
            ('waiting_clarification', {'first_interim_ms': 120, 'first_final_ms': 200, 'stream_complete_ms': 14999}),
        ],
        3: [
            ('stopped', {'first_interim_ms': 250, 'first_final_ms': 400, 'stream_complete_ms': 15000}),
            ('failed', {'first_interim_ms': 260, 'first_final_ms': 410, 'stream_complete_ms': 15001}),
        ],
    }
    batch_rows = []
    score_rows = []
    business_verdicts = {1: 'pass', 2: 'unknown', 3: 'fail'}
    for trial, turn_specs in trial_turns.items():
        execution_id = f'core-three-trials:trial:{trial}'
        run_captures = []
        steps = []
        for index, (status, timing) in enumerate(turn_specs):
            run = capture(
                f'owner-trial-{trial}', f'{execution_id}-run-{index}',
                f'owner-trial-{trial}-session', f'{execution_id}:step:{index}', None, None,
            )
            run['status'] = status
            run_captures.append(run)
            steps.append({
                'index': index, 'op': 'turn', 'capture': run, 'timing': timing,
                'timing_source': 'client_monotonic_from_run_post_start',
                'timing_run_id': run['run_id'],
            })
        batch_rows.append({
            'case_id': 'core-three-trials', 'trial': trial, 'execution_id': execution_id,
            'outcome': 'guide_run', 'capture': run_captures[-1],
            'captures': run_captures, 'steps': steps,
            # Top-level timing aliases the first turn for legacy consumers; it must not add a sample.
            'timing': turn_specs[0][1], 'timing_run_id': run_captures[0]['run_id'],
        })
        violations = ([{
            'code': 'unauthorized_confirmation_cart_change', 'severity': 'critical',
            'source': 'steps.1.after.cart',
        }] if trial == 3 else [])
        score_rows.append({
            'case_id': 'core-three-trials', 'trial': trial, 'execution_id': execution_id,
            'outcome': 'guide_run', 'business_verdict': business_verdicts[trial],
            'human_quality': None, 'human_quality_scope': 'last_guide_run',
            'human_run_labels': [], 'violations': violations,
        })

    legacy_run = capture('owner-legacy', 'legacy-run', 'legacy-session', 'legacy-request', None, None)
    legacy_timing = {
        'first_interim_ms': 40, 'first_final_ms': 80, 'stream_complete_ms': 250,
    }
    batch_rows.append({
        'case_id': 'legacy-single-turn', 'trial': 1,
        'execution_id': 'legacy-single-turn:trial:1', 'outcome': 'guide_run',
        'capture': legacy_run, 'timing': legacy_timing,
    })
    score_rows.append({
        'case_id': 'legacy-single-turn', 'trial': 1,
        'execution_id': 'legacy-single-turn:trial:1', 'outcome': 'guide_run',
        'business_verdict': 'pass', 'human_quality': None,
        'human_quality_scope': 'last_guide_run', 'human_run_labels': [], 'violations': [],
    })

    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps({
        'schema_version': 'ceres-local-followup-batch-v1',
        'case_set': case_set, 'plan': plan, 'cases': batch_rows,
    }, ensure_ascii=False), encoding='utf-8')
    score_path = tmp_path / 'score.json'
    score_path.write_text(json.dumps({
        'schema_version': 'ceres-local-followup-score-v1',
        'case_set': case_set,
        'batch_sha256': hashlib.sha256(batch_path.read_bytes()).hexdigest(),
        'counts': {
            'planned': 4, 'attempted': 4, 'guide_run': 4, 'role_wait': 0,
            'preparation_failed': 0, 'runner_failed': 0, 'not_run': 0,
        },
        'cases': score_rows,
    }, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'report.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.report_batch',
         '--cases', str(cases_path), '--batch', str(batch_path),
         '--score', str(score_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['business_verdicts'] == {'pass': 2, 'fail': 1, 'unknown': 1}
    assert report['guide_runs'] == {
        'observed': 7,
        'terminal_statuses': {
            'completed': 2, 'waiting_clarification': 1, 'waiting_confirmation': 1,
            'protected': 1, 'stopped': 1, 'failed': 1, 'interrupted': 0, 'unknown': 0,
        },
    }
    assert report['critical_violations'] == {
        'executions_with_findings': 1, 'findings': 1, 'execution_denominator': 4,
        'details': [{
            'case_id': 'core-three-trials',
            'execution_id': 'core-three-trials:trial:3',
            'code': 'unauthorized_confirmation_cart_change',
            'severity': 'critical', 'source': 'steps.1.after.cart',
        }],
    }
    assert report['turn_deadline_15s'] == {
        'limit_ms': 15000, 'samples': 7, 'pass': 4, 'timeout': 2, 'unknown': 1,
    }
    assert report['first_useful_result_ms'] == {
        'samples': 7, 'observed': 0, 'unknown': 7,
        'p50': None, 'p95': None, 'human_annotated': False,
        'definition': (
            'Not measured in the current batch contract; tool progress and first interim/final bytes '
            'are not evidence of a useful result.'
        ),
    }
    assert report['latency_ms']['stream_complete_ms'] == {
        'samples': 6, 'p50': 14999, 'p95': 16000,
    }
    core = report['core_trial_stability'][0]
    assert core['three_trials_business_pass'] is False
    assert core['three_trials_performance_pass'] is False
    assert core['three_trials_combined_pass'] is False
    assert [trial['turn_deadline_15s'] for trial in core['trials']] == [
        {'samples': 2, 'pass': 1, 'timeout': 1, 'unknown': 0},
        {'samples': 2, 'pass': 1, 'timeout': 0, 'unknown': 1},
        {'samples': 2, 'pass': 1, 'timeout': 1, 'unknown': 0},
    ]


def test_annotate_batch_cli_joins_v2_labels_and_preserves_unrun_outcomes(tmp_path):
    source = tmp_path / 'captures.json'
    annotations_path = tmp_path / 'annotations.jsonl'
    output = tmp_path / 'annotated.json'
    case_set = {'version': 'public-dev-v1', 'sha256': 'public-case-set-sha'}
    cases = [
        {'case_id': 'reviewed', 'outcome': 'guide_run',
         'capture': capture('owner-reviewed', 'run-reviewed', 'session-reviewed',
                            'request-reviewed', None, None)},
        {'case_id': 'unreviewed', 'outcome': 'guide_run',
         'capture': capture('owner-unreviewed', 'run-unreviewed', 'session-unreviewed',
                            'request-unreviewed', None, None)},
        {'case_id': 'role-choice', 'outcome': 'role_choice_required', 'capture': None},
        {'case_id': 'runner-failed', 'outcome': 'runner_failed', 'capture': None},
        # A previously captured v2 batch has no outcome field; its run stays unreviewed.
        {'case_id': 'legacy-capture',
         'capture': capture('owner-legacy', 'run-legacy', 'session-legacy',
                            'request-legacy', None, None)},
    ]
    source.write_text(json.dumps(batch(case_set, cases), ensure_ascii=False), encoding='utf-8')
    human_label = annotation('owner-reviewed', 'run-reviewed', 'fail')
    human_label.pop('schema_version')
    annotations_path.write_text(json.dumps(human_label, ensure_ascii=False) + '\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.annotate_batch',
         '--captures', str(source),
         '--annotations', str(annotations_path),
         '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    reviewed_batch = json.loads(output.read_text(encoding='utf-8'))
    assert reviewed_batch['schema_version'] == 'ceres-local-followup-batch-v1'
    assert reviewed_batch['case_set'] == case_set
    rows = {row['case_id']: row for row in reviewed_batch['cases']}
    reviewed = rows['reviewed']['capture']['labels']
    assert reviewed['schema_version'] == 'ceres-run-annotation-v2'
    assert reviewed['owner_id'] == 'owner-reviewed' and reviewed['run_id'] == 'run-reviewed'
    assert reviewed['verdict'] == 'fail' and reviewed['reviewer'] == 'evaluation-reviewer'
    assert rows['unreviewed']['capture']['labels'] is None
    assert rows['legacy-capture']['capture']['labels'] is None
    assert 'outcome' not in rows['legacy-capture']
    assert rows['role-choice'] == {'case_id': 'role-choice', 'outcome': 'role_choice_required', 'capture': None}
    assert rows['runner-failed'] == {'case_id': 'runner-failed', 'outcome': 'runner_failed', 'capture': None}


def test_annotate_batch_cli_labels_every_capture_and_final_capture_alias(tmp_path):
    from copy import deepcopy

    source = tmp_path / 'captures.json'
    annotations_path = tmp_path / 'annotations.jsonl'
    output = tmp_path / 'annotated.json'
    case_set = {'version': 'public-dev-v2', 'sha256': 'public-case-set-sha'}
    first = capture('multi-owner', 'first-run', 'multi-session', 'execution:trial:1:step:0', None, None)
    final = capture('multi-owner', 'final-run', 'multi-session', 'execution:trial:1:step:1', None, None)
    source.write_text(json.dumps(batch(case_set, [{
        'case_id': 'multi-turn', 'trial': 1, 'execution_id': 'multi-turn:trial:1',
        'outcome': 'guide_run', 'capture': deepcopy(final),
        'captures': [first, final],
    }]), ensure_ascii=False), encoding='utf-8')
    labels = [
        annotation('multi-owner', 'first-run', 'fail'),
        annotation('multi-owner', 'final-run', 'pass'),
    ]
    for label in labels:
        label.pop('schema_version')
    annotations_path.write_text(
        ''.join(json.dumps(label, ensure_ascii=False) + '\n' for label in labels),
        encoding='utf-8',
    )

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.annotate_batch',
         '--captures', str(source), '--annotations', str(annotations_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    annotated = json.loads(output.read_text(encoding='utf-8'))['cases'][0]
    assert [row['run_id'] for row in annotated['captures']] == ['first-run', 'final-run']
    assert annotated['captures'][0]['labels']['verdict'] == 'fail'
    assert annotated['captures'][0]['labels']['run_id'] == 'first-run'
    assert annotated['captures'][1]['labels']['verdict'] == 'pass'
    assert annotated['capture']['labels']['verdict'] == 'pass'
    assert annotated['capture'] == annotated['captures'][-1]


def test_annotate_batch_cli_rejects_capture_identity_reused_across_rows(tmp_path):
    from copy import deepcopy

    source = tmp_path / 'captures.json'
    annotations_path = tmp_path / 'annotations.jsonl'
    output = tmp_path / 'annotated.json'
    case_set = {'version': 'public-dev-v2', 'sha256': 'public-case-set-sha'}
    shared = capture('same-owner', 'shared-run', 'shared-session', 'shared-request', None, None)
    first_final = capture('same-owner', 'first-final-run', 'shared-session', 'first-request', None, None)
    second_final = capture('same-owner', 'second-final-run', 'shared-session', 'second-request', None, None)
    source.write_text(json.dumps(batch(case_set, [
        {'case_id': 'first-case', 'capture': first_final, 'captures': [shared, first_final]},
        {'case_id': 'second-case', 'capture': second_final, 'captures': [deepcopy(shared), second_final]},
    ]), ensure_ascii=False), encoding='utf-8')
    annotations_path.write_text('', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.annotate_batch',
         '--captures', str(source), '--annotations', str(annotations_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert 'Duplicate capture owner/run' in result.stderr


def test_failure_intake_cli_emits_only_explicitly_failed_captures_with_source_steps(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'source-case-set-v3',
        'cases': [
            {
                'case_id': 'dev-source-01', 'message': '给我两盒牛奶的待确认方案。',
                'category': 'purchase_planning', 'scenario_family': 'milk-plan',
                'split': 'regression', 'core': True,
                'expected_behavior': '原始方案保留两盒数量，初轮不加购。',
                'fact_sources': ['data/fixtures/products.json#demo:cn-yili-whole-250ml-carton'],
                'steps': [{'op': 'confirm_plan'}, {'op': 'repeat_confirmation'}],
                'checks': [{'path': 'after.cart.items.0.quantity', 'operator': 'eq', 'expected': 2}],
            },
            {
                'case_id': 'dev-source-02', 'message': '一般商品价格以什么为准？',
                'category': 'policy', 'scenario_family': 'unreviewed-policy',
                'split': 'regression', 'core': False,
                'expected_behavior': '说明当前门店Offer是演示依据。',
                'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
                'checks': [],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    first = capture('failed-owner', 'failed-first-run', 'failed-session', 'dev-source-01:trial:1', None,
                    annotation('failed-owner', 'failed-first-run', 'fail'))
    first['labels']['expected_behavior'] = '明确商品数量并在用户确认前保持购物车不变。'
    first['labels']['rationale'] = '初轮回复把未确认方案直接写入购物车。'
    final = capture('failed-owner', 'failed-final-run', 'failed-session', 'dev-source-01:trial:1:step:1', None,
                    annotation('failed-owner', 'failed-final-run', 'pass'))
    final['labels']['schema_version'] = 'ceres-run-annotation-v2'
    first['labels']['schema_version'] = 'ceres-run-annotation-v2'
    unreviewed = capture('unreviewed-owner', 'unreviewed-run', 'unreviewed-session',
                         'dev-source-02:trial:1', None, None)
    source_batch = batch(case_set, [
        {
            'case_id': 'dev-source-01', 'trial': 1,
            'execution_id': 'dev-source-01:trial:1', 'outcome': 'guide_run',
            'capture': json.loads(json.dumps(final)), 'captures': [first, final],
        },
        {
            'case_id': 'dev-source-02', 'trial': 1,
            'execution_id': 'dev-source-02:trial:1', 'outcome': 'guide_run',
            'capture': unreviewed, 'captures': [unreviewed],
        },
    ])
    source_batch['plan'] = [
        {'case_id': 'dev-source-01', 'trial': 1, 'execution_id': 'dev-source-01:trial:1'},
        {'case_id': 'dev-source-02', 'trial': 1, 'execution_id': 'dev-source-02:trial:1'},
    ]
    batch_path = tmp_path / 'annotated-batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'failure-cases.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.failure_intake',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    failure_set = json.loads(output.read_text(encoding='utf-8'))
    assert failure_set['schema_version'] == 'ceres-local-followup-dev-cases-v1'
    assert len(failure_set['cases']) == 1
    failed = failure_set['cases'][0]
    assert failed['case_id'].startswith('failure-dev-source-01-')
    assert failed['message'] == cases['cases'][0]['message']
    assert failed['steps'] == cases['cases'][0]['steps']
    assert failed['checks'] == cases['cases'][0]['checks']
    assert failed['expected_behavior'] == first['labels']['expected_behavior']
    assert failed['failure_source']['case_set'] == case_set
    assert failed['failure_source']['case_id'] == 'dev-source-01'
    assert failed['failure_source']['execution_id'] == 'dev-source-01:trial:1'
    assert failed['failure_source']['trial'] == 1
    assert failed['failure_source']['owner_id'] == 'failed-owner'
    assert failed['failure_source']['run_id'] == 'failed-first-run'
    assert failed['failure_source']['verdict'] == 'fail'
    assert failed['failure_source']['rationale'] == first['labels']['rationale']
    assert failed['failure_source']['source_batch_sha256'] == hashlib.sha256(batch_path.read_bytes()).hexdigest()


def test_failure_intake_cli_excludes_non_regression_acceptance_cases(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'acceptance-source-v1',
        'cases': [{
            'case_id': 'acceptance-only', 'message': '我想比较两种商品。',
            'category': 'product_selection', 'scenario_family': 'acceptance-only',
            'split': 'acceptance', 'core': False,
            'expected_behavior': '只比较商品，不加购。',
            'fact_sources': ['data/fixtures/products.json#demo:cn-yili-whole-250ml-carton'],
            'checks': [],
        }],
    }
    cases_path = tmp_path / 'acceptance-cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    reviewed = capture(
        'acceptance-owner', 'acceptance-run', 'acceptance-session',
        'acceptance-only:trial:1', None,
        annotation('acceptance-owner', 'acceptance-run', 'fail'),
    )
    reviewed['labels']['schema_version'] = 'ceres-run-annotation-v2'
    source_batch = batch(case_set, [{
        'case_id': 'acceptance-only', 'trial': 1,
        'execution_id': 'acceptance-only:trial:1', 'outcome': 'guide_run',
        'capture': reviewed, 'captures': [reviewed],
    }])
    source_batch['plan'] = [{
        'case_id': 'acceptance-only', 'trial': 1,
        'execution_id': 'acceptance-only:trial:1',
    }]
    batch_path = tmp_path / 'acceptance-batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'failure-cases.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.failure_intake',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    failure_set = json.loads(output.read_text(encoding='utf-8'))
    assert failure_set['cases'] == []
    assert failure_set['source']['excluded_cases_by_split'] == {'acceptance': 1}
    assert failure_set['source']['exclusion_reason'] == 'only_regression_cases_are_eligible_for_failure_intake'


def test_public_dev_case_set_has_forty_regression_cases_and_current_fact_pointers():
    cases_path = Path(__file__).resolve().parents[2] / 'evals' / 'ceres2-local-followup-dev.json'
    case_set = json.loads(cases_path.read_text(encoding='utf-8'))
    required = {
        'case_id', 'message', 'category', 'scenario_family', 'split', 'core',
        'expected_behavior', 'fact_sources', 'checks',
    }

    assert case_set['schema_version'] == 'ceres-local-followup-dev-cases-v1'
    assert case_set['version']
    cases = case_set['cases']
    assert len(cases) == 40
    assert len({case['case_id'] for case in cases}) == 40
    assert sum(case['core'] is True for case in cases) == 20
    assert all(case['split'] == 'regression' for case in cases)
    assert all(required <= set(case) <= required | {'steps'} for case in cases)
    assert all('setup' not in case for case in cases)
    stepped_cases = [case for case in cases if 'steps' in case]
    assert [case['case_id'] for case in stepped_cases] == ['dev-01']
    for case in stepped_cases:
        assert all(
            (set(step) == {'op'} and step['op'] in {'confirm_plan', 'repeat_confirmation'})
            or (set(step) == {'op', 'message'} and step['op'] == 'turn' and step['message'])
            for step in case['steps']
        )
    for case in cases:
        assert case['message'] and case['expected_behavior'] and case['fact_sources']
        assert all(check['operator'] in {'eq', 'contains', 'min', 'max', 'length', 'min_length'}
                   for check in case['checks'])
        for pointer in case['fact_sources']:
            path, anchor = pointer.split('#', 1)
            source = cases_path.parents[1] / path
            assert source.is_file(), pointer
            if source.suffix == '.json' and '.' in anchor:
                selected = json.loads(source.read_text(encoding='utf-8'))
                for part in anchor.split('.'):
                    assert isinstance(selected, dict) and part in selected, pointer
                    selected = selected[part]
                assert selected is not None, pointer
            else:
                assert anchor in source.read_text(encoding='utf-8'), pointer


def test_score_batch_cli_marks_self_consistent_wrong_offer_price_critical_and_keeps_denominator(tmp_path):
    import hashlib

    sku_id = 'demo:cn-pepsi-original-330ml-can'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'public-dev-v1',
        'cases': [
            {
                'case_id': 'current-offer-price',
                'message': '买两罐百事可乐原味汽水330ml罐装。',
                'category': 'purchase_planning',
                'scenario_family': 'offer-price-source',
                'split': 'regression',
                'core': True,
                'expected_behavior': 'Use the current Offer price and leave an unstated budget unknown.',
                'fact_sources': [
                    'data/fixtures/products.json#demo:cn-pepsi-original-330ml-can',
                    'data/fixtures/offers.json#demo:cn-pepsi-original-330ml-can',
                ],
                'checks': [
                    {'path': 'after.guide.plan.selected_total_fen', 'operator': 'eq', 'expected': 600},
                ],
            },
            {
                'case_id': 'planned-but-not-run',
                'message': '买一盒苏打饼干100克盒装。',
                'category': 'purchase_planning',
                'scenario_family': 'planned-denominator',
                'split': 'regression',
                'core': False,
                'expected_behavior': 'The planned case remains visible when no execution occurred.',
                'fact_sources': ['data/fixtures/products.json#demo:snack-soda-crackers-100g-box'],
                'checks': [
                    {'path': 'after.guide.plan', 'operator': 'eq', 'expected': True},
                ],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {'version': cases['version'], 'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest()}

    line = {
        'sku_id': sku_id,
        'quantity': 2,
        'unit_price_fen': 400,
        'line_total_fen': 800,
        'selected': True,
    }
    assert line['unit_price_fen'] * line['quantity'] == line['line_total_fen']
    before = {
        'guide': {'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'keke'},
    }
    after = {
        'guide': {
            'plan': {'items': [line], 'selected_total_fen': 800, 'total_price_fen': 800},
            'conditions': {},
        },
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'keke'},
    }
    batch_path = tmp_path / 'batch.json'
    execution_ids = {
        'current-offer-price': 'current-offer-price:trial:1',
        'planned-but-not-run': 'planned-but-not-run:trial:1',
    }
    price_capture = capture('score-owner', 'price-run', 'score-session', 'price-request', None, None)
    price_capture['status'] = 'waiting_confirmation'
    scored_batch = batch(case_set, [
        {
            'case_id': 'current-offer-price',
            'trial': 1,
            'execution_id': execution_ids['current-offer-price'],
            'outcome': 'guide_run',
            'capture': price_capture,
            'before': before,
            'after': after,
            'catalog_facts': {
                'items': [{'sku_id': sku_id, 'price_fen': 300, 'sellable': True, 'available_qty': 36}],
                'total': 1,
                'page': 1,
                'page_size': 20,
            },
        },
        {
            'case_id': 'planned-but-not-run',
            'trial': 1,
            'execution_id': execution_ids['planned-but-not-run'],
            'outcome': 'not_run',
            'capture': None,
            'before': None,
            'after': None,
            'catalog_facts': None,
        },
    ])
    scored_batch['plan'] = [
        {'case_id': case_id, 'trial': 1, 'execution_id': execution_id}
        for case_id, execution_id in execution_ids.items()
    ]
    batch_path.write_text(json.dumps(scored_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path),
         '--batch', str(batch_path),
         '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))
    assert scored['counts']['planned'] == 2
    assert scored['counts']['attempted'] == 1
    assert scored['counts']['guide_run'] == 1
    assert scored['counts']['not_run'] == 1
    rows = {row['execution_id']: row for row in scored['cases']}
    price_result = rows[execution_ids['current-offer-price']]
    assert price_result['business_verdict'] == 'fail'
    assert price_result['human_quality'] is None
    assert price_result['budget_fen'] is None
    assert any(row['code'] == 'catalog_offer_price_mismatch' and row['severity'] == 'critical'
               for row in price_result['violations'])
    assert rows[execution_ids['planned-but-not-run']]['case_id'] == 'planned-but-not-run'
    assert rows[execution_ids['planned-but-not-run']]['outcome'] == 'not_run'
    assert rows[execution_ids['planned-but-not-run']]['business_verdict'] == 'unknown'


def test_score_batch_cli_keeps_noncomparable_checks_unknown_and_continues(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'noncomparable-checks-v1',
        'cases': [
            {
                'case_id': 'noncomparable-checks', 'message': '请给出当前待确认方案。',
                'category': 'purchase_planning', 'scenario_family': 'noncomparable-check-values',
                'split': 'regression', 'core': False,
                'expected_behavior': '非可比较证据保持unknown，不阻断批次或本题后续检查。',
                'fact_sources': [],
                'checks': [
                    {'path': 'after.guide.plan.note', 'operator': 'min', 'expected': 100},
                    {'path': 'after.guide.plan.note', 'operator': 'contains', 'expected': 1},
                    {'path': 'after.guide.plan.can_confirm', 'operator': 'length', 'expected': 1},
                    {'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'},
                ],
            },
            {
                'case_id': 'later-valid-case', 'message': '一般政策问题是什么？',
                'category': 'policy', 'scenario_family': 'later-valid-case',
                'split': 'regression', 'core': False,
                'expected_behavior': '非可比较检查不能中断后续合法案例评分。',
                'fact_sources': [],
                'checks': [
                    {'path': 'capture.status', 'operator': 'eq', 'expected': 'completed'},
                    {'path': 'after.guide.plan', 'operator': 'eq', 'expected': None},
                ],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    before = {
        'guide': {'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    noncomparable_after = {
        'guide': {
            'plan': {
                'items': [], 'selected_total_fen': 0, 'note': 'bad-string',
                'can_confirm': False,
            },
            'conditions': {},
        },
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    valid_after = {
        'guide': {'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    waiting_capture = capture('check-owner', 'waiting-run', 'check-session', 'request-1', None, None)
    waiting_capture['status'] = 'waiting_confirmation'
    completed_capture = capture('check-owner-2', 'completed-run', 'check-session-2', 'request-2', None, None)
    batch_rows = [
        {
            'case_id': 'noncomparable-checks', 'outcome': 'guide_run',
            'capture': waiting_capture, 'before': before, 'after': noncomparable_after,
        },
        {
            'case_id': 'later-valid-case', 'outcome': 'guide_run',
            'capture': completed_capture, 'before': valid_after, 'after': valid_after,
        },
    ]
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps({
        'schema_version': 'ceres-local-followup-batch-v1',
        'case_set': case_set, 'cases': batch_rows,
    }, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))
    assert scored['counts'] == {
        'planned': 2, 'attempted': 2, 'guide_run': 2, 'role_wait': 0,
        'preparation_failed': 0, 'runner_failed': 0, 'not_run': 0,
    }
    rows = {row['case_id']: row for row in scored['cases']}
    noncomparable = rows['noncomparable-checks']
    assert noncomparable['business_verdict'] == 'unknown'
    assert noncomparable['violations'] == []
    gaps = noncomparable['evidence_gaps']
    assert [gap['path'] for gap in gaps] == [
        'after.guide.plan.note',
        'after.guide.plan.note',
        'after.guide.plan.can_confirm',
    ]
    assert [gap['actual_type'] for gap in gaps] == ['str', 'str', 'bool']
    assert all(gap['code'] == 'check_value_not_comparable' for gap in gaps)
    assert all(gap['exception_type'] == 'TypeError' and gap['reason'] for gap in gaps)
    assert rows['later-valid-case']['business_verdict'] == 'pass'
    assert rows['later-valid-case']['evidence_gaps'] == []

    cases['cases'][0]['checks'][0]['operator'] = 'typo'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    wrong_operator_case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    wrong_operator_batch = {
        'schema_version': 'ceres-local-followup-batch-v1',
        'case_set': wrong_operator_case_set, 'cases': batch_rows,
    }
    batch_path.write_text(json.dumps(wrong_operator_batch, ensure_ascii=False), encoding='utf-8')
    wrong_operator = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path),
         '--output', str(tmp_path / 'wrong-operator-score.json')],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )
    assert wrong_operator.returncode != 0
    assert 'Unsupported check operator: typo' in wrong_operator.stderr


def test_score_batch_cli_checks_plan_and_confirmed_cart_amounts(tmp_path):
    import hashlib

    sku_id = 'demo:cn-pepsi-original-330ml-can'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'money-closure-v1',
        'cases': [
            {
                'case_id': 'wrong-selected-total', 'message': '买两罐百事可乐。',
                'category': 'purchase_planning', 'scenario_family': 'selected-total-sum',
                'split': 'regression', 'core': False,
                'expected_behavior': 'selected_total_fen等于已选行金额合计。',
                'fact_sources': [f'data/fixtures/offers.json#{sku_id}'],
                'checks': [{'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'}],
            },
            {
                'case_id': 'wrong-confirmed-cart-money', 'message': '确认将两罐加入购物车。',
                'category': 'purchase_planning', 'scenario_family': 'confirmed-cart-money',
                'split': 'regression', 'core': False,
                'expected_behavior': '确认回执后的购物车价格、行金额和总额与Offer及数量一致。',
                'fact_sources': [f'data/fixtures/offers.json#{sku_id}'],
                'steps': [{'op': 'confirm_plan'}],
                'checks': [
                    {'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'},
                    {'path': 'steps.1.confirmation_receipt.status', 'operator': 'eq', 'expected': 'success'},
                    {'path': 'after.cart.total_price_fen', 'operator': 'eq', 'expected': 600},
                ],
            },
            {
                'case_id': 'missing-plan-amount', 'message': '给两罐百事可乐方案。',
                'category': 'purchase_planning', 'scenario_family': 'missing-plan-amount',
                'split': 'regression', 'core': False,
                'expected_behavior': '缺少行金额或selected_total时保持unknown，不补成0。',
                'fact_sources': [f'data/fixtures/offers.json#{sku_id}'],
                'checks': [{'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'}],
            },
            {
                'case_id': 'selected-total-without-catalog', 'message': '给出自洽的两罐方案。',
                'category': 'purchase_planning', 'scenario_family': 'selected-total-without-catalog',
                'split': 'regression', 'core': False,
                'expected_behavior': '即使Offer证据缺失，仍按已知选中行金额核对selected_total。',
                'fact_sources': [],
                'checks': [{'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'}],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    empty_cart = {'items': [], 'total_price_fen': 0}
    initial = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        'cart': empty_cart, 'orders': [], 'opening': {'role': 'keke'},
    }

    def plan_item(line_total=600):
        item = {
            'sku_id': sku_id, 'quantity': 2, 'remaining_quantity': 2,
            'unit_price_fen': 300, 'selected': True,
        }
        if line_total is not None:
            item['line_total_fen'] = line_total
        return item

    def snapshot(plan, cart=None):
        return {
            'guide': {'task_id': 'task-money', 'plan': plan, 'conditions': {}},
            'cart': cart or empty_cart,
            'orders': [], 'opening': {'role': 'keke'},
        }

    def plan(plan_id, selected_total=600, line_total=600):
        result = {
            'plan_id': plan_id, 'plan_version': 1,
            'items': [plan_item(line_total)],
        }
        if selected_total is not None:
            result['selected_total_fen'] = selected_total
        return result

    wrong_total_plan = plan('plan-wrong-total', selected_total=601)
    missing_amount_plan = plan('plan-missing-amount', selected_total=None, line_total=None)
    no_catalog_plan = plan('plan-no-catalog', selected_total=601, line_total=600)
    wrong_total_after = snapshot(wrong_total_plan)
    missing_amount_after = snapshot(missing_amount_plan)
    no_catalog_after = snapshot(no_catalog_plan)
    confirmed_plan = plan('plan-confirmed-cart')
    turn_after = snapshot(confirmed_plan)
    wrong_cart = {
        'items': [{
            'sku_id': sku_id, 'quantity': 2, 'unit_price_fen': 301,
            'line_total_fen': 601,
        }],
        'total_price_fen': 600,
    }
    confirmed_after = snapshot(confirmed_plan, wrong_cart)

    wrong_plan_capture = capture('money-owner-1', 'wrong-total-run', 'money-session-1', 'wrong-total', None, None)
    wrong_plan_capture['status'] = 'waiting_confirmation'
    cart_capture = capture('money-owner-2', 'cart-money-run', 'money-session-2', 'cart-money', None, None)
    cart_capture['status'] = 'waiting_confirmation'
    missing_capture = capture('money-owner-3', 'missing-money-run', 'money-session-3', 'missing-money', None, None)
    missing_capture['status'] = 'waiting_confirmation'
    no_catalog_capture = capture('money-owner-4', 'no-catalog-run', 'money-session-4', 'no-catalog', None, None)
    no_catalog_capture['status'] = 'waiting_confirmation'

    body = {
        'plan_id': 'plan-confirmed-cart', 'plan_version': 1,
        'expected_state_version': 1, 'expected_session_version': 0,
        'selected_items': [{'sku_id': sku_id, 'quantity': 2}],
    }
    receipt = {
        'status': 'success', 'operation_id': 'money-operation',
        'confirmation_id': 'money-confirmation',
        'items_added': [{'sku_id': sku_id, 'quantity': 2}],
        'cart_version': 2, 'task_id': 'task-money',
        'state_version': 2, 'session_version': 0,
    }
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(batch(case_set, [
        {
            'case_id': 'wrong-selected-total', 'outcome': 'guide_run',
            'capture': wrong_plan_capture, 'before': initial, 'after': wrong_total_after,
            'catalog_facts': {'items': [{'sku_id': sku_id, 'price_fen': 300}]},
        },
        {
            'case_id': 'wrong-confirmed-cart-money', 'outcome': 'guide_run',
            'capture': cart_capture, 'captures': [cart_capture],
            'before': initial, 'after': confirmed_after,
            'catalog_facts': {'items': [{'sku_id': sku_id, 'price_fen': 300}]},
            'steps': [
                {
                    'index': 0, 'op': 'turn', 'before': initial, 'after': turn_after,
                    'capture': cart_capture,
                },
                {
                    'index': 1, 'op': 'confirm_plan', 'before': turn_after,
                    'after': confirmed_after, 'idempotency_key': 'money-confirm-key',
                    'confirmation_body': body, 'confirmation_receipt': receipt, 'capture': None,
                },
            ],
        },
        {
            'case_id': 'missing-plan-amount', 'outcome': 'guide_run',
            'capture': missing_capture, 'before': initial, 'after': missing_amount_after,
            'catalog_facts': {'items': [{'sku_id': sku_id, 'price_fen': 300}]},
        },
        {
            'case_id': 'selected-total-without-catalog', 'outcome': 'guide_run',
            'capture': no_catalog_capture, 'before': initial, 'after': no_catalog_after,
        },
    ]), ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))
    assert scored['counts'] == {
        'planned': 4, 'attempted': 4, 'guide_run': 4, 'role_wait': 0,
        'preparation_failed': 0, 'runner_failed': 0, 'not_run': 0,
    }
    rows = {row['case_id']: row for row in scored['cases']}
    wrong_total = rows['wrong-selected-total']
    assert wrong_total['business_verdict'] == 'fail'
    assert any(
        row['code'] == 'selected_total_mismatch' and row['severity'] == 'critical'
        and row['expected'] == 600 and row['actual'] == 601
        for row in wrong_total['violations']
    )
    wrong_cart = rows['wrong-confirmed-cart-money']
    assert wrong_cart['business_verdict'] == 'fail'
    assert {
        row['code'] for row in wrong_cart['violations'] if row['severity'] == 'critical'
    } >= {
        'cart_catalog_price_mismatch', 'cart_line_total_mismatch', 'cart_total_mismatch',
    }
    missing = rows['missing-plan-amount']
    assert missing['business_verdict'] == 'unknown'
    assert missing['budget_fen'] is None
    assert {
        row['code'] for row in missing['evidence_gaps']
    } >= {'selected_total_missing', 'plan_line_amount_missing'}
    no_catalog = rows['selected-total-without-catalog']
    assert no_catalog['business_verdict'] == 'fail'
    assert any(
        row['code'] == 'selected_total_mismatch' and row['severity'] == 'critical'
        and row['expected'] == 600 and row['actual'] == 601
        for row in no_catalog['violations']
    )
    assert any(
        gap['code'] == 'catalog_offer_missing' and gap['sku_id'] == sku_id
        for gap in no_catalog['evidence_gaps']
    )


def test_score_batch_treats_unconfirmable_budget_quote_as_pending_not_critical(tmp_path):
    import hashlib

    sku_id = 'demo:cn-pepsi-original-330ml-can'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'budget-quote-score-v1',
        'cases': [{
            'case_id': 'budget-quote', 'message': '预算10元，给我百事可乐方案。',
            'category': 'purchase_planning', 'scenario_family': 'over-budget-quote',
            'split': 'regression', 'core': False,
            'expected_behavior': '保留预算；超预算报价等待用户决定，不提前加购。',
            'fact_sources': ['data/fixtures/offers.json#demo:cn-pepsi-original-330ml-can'],
            'checks': [
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'},
                {'path': 'after.guide.plan.can_confirm', 'operator': 'eq', 'expected': False},
                {'path': 'after.guide.plan.budget_quote.total_fen', 'operator': 'eq', 'expected': 1500},
                {'path': 'after.guide.conditions.budget_fen', 'operator': 'eq', 'expected': 1000},
            ],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    item = {
        'sku_id': sku_id, 'quantity': 5, 'unit_price_fen': 300,
        'line_total_fen': 1500, 'selected': True,
    }
    before = {
        'guide': {'plan': None, 'conditions': {'budget_fen': 1000}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    after = {
        'guide': {
            'plan': {
                'items': [item], 'selected_total_fen': 1500, 'total_price_fen': 1500,
                'can_confirm': False, 'budget_quote': {'budget_fen': 1000, 'total_fen': 1500},
            },
            'conditions': {'budget_fen': 1000},
        },
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    run = capture('quote-owner', 'quote-run', 'quote-session', 'budget-quote:trial:1', None, None)
    run['status'] = 'waiting_confirmation'
    source_batch = batch(case_set, [{
        'case_id': 'budget-quote', 'trial': 1,
        'execution_id': 'budget-quote:trial:1', 'outcome': 'guide_run',
        'capture': run, 'before': before, 'after': after,
        'catalog_facts': {'items': [{'sku_id': sku_id, 'price_fen': 300, 'sellable': True,
                                     'available_qty': 20}]},
    }])
    source_batch['plan'] = [{
        'case_id': 'budget-quote', 'trial': 1, 'execution_id': 'budget-quote:trial:1',
    }]
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))['cases'][0]
    assert scored['business_verdict'] == 'unknown'
    assert not any(row['code'] == 'budget_exceeded' and row['severity'] == 'critical'
                   for row in scored['violations'])
    assert any(row['code'] == 'budget_quote_pending_decision'
               for row in scored['evidence_gaps'])


def test_score_batch_keeps_unexecuted_rows_unknown_and_scores_actual_role_wait(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'unexecuted-outcome-scoring-v1',
        'cases': [
            {
                'case_id': 'not-run', 'message': '查询我的订单物流。',
                'category': 'routing', 'scenario_family': 'planned-not-run-role-choice',
                'split': 'regression', 'core': False,
                'expected_behavior': '计划保留在分母中，未执行不作质量结论。',
                'fact_sources': ['data/fixtures/policies.json#P-DEL-01'],
                'checks': [
                    {'path': 'outcome', 'operator': 'eq', 'expected': 'role_choice_required'},
                ],
            },
            {
                'case_id': 'preparation-failed', 'message': '一般商品价格以什么为准？',
                'category': 'policy', 'scenario_family': 'preparation-failed',
                'split': 'regression', 'core': False,
                'expected_behavior': '准备失败不作为业务回答失败或通过。',
                'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
                'checks': [
                    {'path': 'outcome', 'operator': 'eq', 'expected': 'guide_run'},
                ],
            },
            {
                'case_id': 'actual-role-wait', 'message': '查询我的订单物流。',
                'category': 'routing', 'scenario_family': 'actual-role-choice',
                'split': 'regression', 'core': False,
                'expected_behavior': '等待用户选择售后角色，保持可可角色。',
                'fact_sources': ['data/fixtures/policies.json#P-DEL-01'],
                'checks': [
                    {'path': 'outcome', 'operator': 'eq', 'expected': 'role_choice_required'},
                    {'path': 'navigation.status', 'operator': 'eq', 'expected': 'switch'},
                    {'path': 'after.opening.role', 'operator': 'eq', 'expected': 'keke'},
                ],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    state = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    execution_ids = {
        case_id: f'{case_id}:trial:1'
        for case_id in ('not-run', 'preparation-failed', 'actual-role-wait')
    }
    source_batch = batch(case_set, [
        {
            'case_id': 'not-run', 'trial': 1, 'execution_id': execution_ids['not-run'],
            'outcome': 'not_run', 'capture': None, 'before': None, 'after': None,
        },
        {
            'case_id': 'preparation-failed', 'trial': 1,
            'execution_id': execution_ids['preparation-failed'],
            'outcome': 'preparation_failed', 'capture': None,
            'before': None, 'after': None,
        },
        {
            'case_id': 'actual-role-wait', 'trial': 1,
            'execution_id': execution_ids['actual-role-wait'],
            'outcome': 'role_choice_required', 'capture': None,
            'navigation': {'status': 'switch'}, 'before': state, 'after': state,
        },
    ])
    source_batch['plan'] = [
        {'case_id': case_id, 'trial': 1, 'execution_id': execution_id}
        for case_id, execution_id in execution_ids.items()
    ]
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))
    assert scored['counts'] == {
        'planned': 3, 'attempted': 2, 'guide_run': 0, 'role_wait': 1,
        'preparation_failed': 1, 'runner_failed': 0, 'not_run': 1,
    }
    rows = {row['case_id']: row for row in scored['cases']}
    for case_id in ('not-run', 'preparation-failed'):
        assert rows[case_id]['business_verdict'] == 'unknown'
        assert rows[case_id]['violations'] == []
    assert rows['actual-role-wait']['business_verdict'] == 'pass'
    assert rows['actual-role-wait']['violations'] == []


def test_evaluation_report_rejects_score_from_different_batch_bytes(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'report-source-binding-v1',
        'cases': [{
            'case_id': 'policy-case', 'message': '一般商品价格以什么为准？',
            'category': 'policy', 'scenario_family': 'report-source-binding',
            'split': 'regression', 'core': False,
            'expected_behavior': '根据当前Offer解释一般价格依据。',
            'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
            'checks': [
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'completed'},
                {'path': 'after.guide.plan', 'operator': 'eq', 'expected': None},
            ],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    state = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    run = capture('source-owner', 'source-run', 'source-session', 'policy-case', None, None)
    source_batch = batch(case_set, [{
        'case_id': 'policy-case', 'outcome': 'guide_run', 'capture': run,
        'before': state, 'after': state,
        'timing': {'first_interim_ms': 100, 'first_final_ms': 200, 'stream_complete_ms': 300},
    }])
    original_batch_path = tmp_path / 'original-batch.json'
    original_batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    score_path = tmp_path / 'score.json'
    scored = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(original_batch_path), '--output', str(score_path)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )
    assert scored.returncode == 0, scored.stderr

    different_batch = json.loads(json.dumps(source_batch, ensure_ascii=False))
    different_batch['cases'][0]['timing']['first_final_ms'] = 201
    candidate_batch_path = tmp_path / 'different-batch.json'
    candidate_batch_path.write_text(json.dumps(different_batch, ensure_ascii=False), encoding='utf-8')
    report_path = tmp_path / 'report.json'
    report_result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.report_batch',
         '--cases', str(cases_path), '--batch', str(candidate_batch_path),
         '--score', str(score_path), '--output', str(report_path)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert report_result.returncode != 0
    assert 'Score batch_sha256 does not match the supplied batch' in report_result.stderr
    assert not report_path.exists()


def test_score_batch_preserves_wait_policy_unknown_and_every_planned_execution(tmp_path):
    import hashlib

    checks = lambda *rows: list(rows)
    case_rows = [
        {
            'case_id': 'policy-no-plan', 'message': '一般退款政策是什么？',
            'category': 'policy', 'scenario_family': 'general-policy',
            'split': 'regression', 'core': True,
            'expected_behavior': '回答一般政策，不创建购买计划。',
            'fact_sources': ['data/fixtures/policies.json#P-REF-01'],
            'checks': checks(
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'completed'},
                {'path': 'after.guide.plan', 'operator': 'eq', 'expected': None},
            ),
        },
        {
            'case_id': 'role-wait-no-switch', 'message': '查询我的订单物流。',
            'category': 'routing', 'scenario_family': 'specific-order-role-choice',
            'split': 'regression', 'core': True,
            'expected_behavior': '等待用户明确选择，角色保持可可。',
            'fact_sources': ['data/fixtures/policies.json#P-DEL-01'],
            'checks': checks(
                {'path': 'outcome', 'operator': 'eq', 'expected': 'role_choice_required'},
                {'path': 'navigation.status', 'operator': 'eq', 'expected': 'switch'},
                {'path': 'after.opening.role', 'operator': 'eq', 'expected': 'keke'},
            ),
        },
        {
            'case_id': 'null-budget-check', 'message': '给我一个预算内方案。',
            'category': 'purchase_planning', 'scenario_family': 'missing-budget-evidence',
            'split': 'regression', 'core': True,
            'expected_behavior': '缺失预算值不得按零或任意数字判定。',
            'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
            'checks': checks(
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_clarification'},
                {'path': 'after.guide.conditions.budget_fen', 'operator': 'max', 'expected': 500},
            ),
        },
        {
            'case_id': 'later-policy-no-plan', 'message': '模拟配送信息以什么为准？',
            'category': 'policy', 'scenario_family': 'later-case-after-unknown',
            'split': 'regression', 'core': False,
            'expected_behavior': '保留政策说明，不需要购买方案。',
            'fact_sources': ['data/fixtures/policies.json#P-DEL-01'],
            'checks': checks(
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'completed'},
                {'path': 'after.guide.plan', 'operator': 'eq', 'expected': None},
            ),
        },
        {
            'case_id': 'planned-row-omitted', 'message': '只看一盒苏打饼干报价。',
            'category': 'product_selection', 'scenario_family': 'omitted-planned-row',
            'split': 'regression', 'core': False,
            'expected_behavior': '即使执行记录缺失，计划项仍在批次分母中。',
            'fact_sources': ['data/fixtures/products.json#demo:snack-soda-crackers-100g-box'],
            'checks': [],
        },
    ]
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'score-negative-v2',
        'cases': case_rows,
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }

    unchanged = {
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'keke'},
    }
    policy_state = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        **unchanged,
    }
    role_wait_after = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'momo'},
    }
    null_budget_state = {
        'guide': {'task_id': 'task-budget', 'plan': None, 'conditions': {'budget_fen': None}},
        **unchanged,
    }
    batch_path = tmp_path / 'batch.json'
    executions = {
        'policy-no-plan': 'policy-no-plan:trial:1',
        'role-wait-no-switch': 'role-wait-no-switch:trial:1',
        'null-budget-check': 'null-budget-check:trial:1',
        'later-policy-no-plan': 'later-policy-no-plan:trial:1',
        'planned-row-omitted': 'planned-row-omitted:trial:1',
    }
    budget_capture = capture('budget-owner', 'budget-run', 'budget-session', 'budget-request', None, None)
    budget_capture['status'] = 'waiting_clarification'
    entries = [
        {
            'case_id': 'policy-no-plan', 'trial': 1,
            'execution_id': executions['policy-no-plan'], 'outcome': 'guide_run',
            'capture': capture('policy-owner', 'policy-run', 'policy-session', 'policy-request', None, None),
            'before': policy_state, 'after': policy_state, 'catalog_facts': {'items': []},
        },
        {
            'case_id': 'role-wait-no-switch', 'trial': 1,
            'execution_id': executions['role-wait-no-switch'], 'outcome': 'role_choice_required',
            'capture': None,
            'navigation': {'status': 'switch'},
            'before': policy_state, 'after': role_wait_after, 'catalog_facts': None,
        },
        {
            'case_id': 'null-budget-check', 'trial': 1,
            'execution_id': executions['null-budget-check'], 'outcome': 'guide_run',
            'capture': budget_capture,
            'before': null_budget_state, 'after': null_budget_state, 'catalog_facts': {'items': []},
        },
        {
            'case_id': 'later-policy-no-plan', 'trial': 1,
            'execution_id': executions['later-policy-no-plan'], 'outcome': 'guide_run',
            'capture': capture('later-owner', 'later-run', 'later-session', 'later-request', None, None),
            'before': policy_state, 'after': policy_state, 'catalog_facts': {'items': []},
        },
    ]
    scored_batch = batch(case_set, entries)
    scored_batch['plan'] = [
        {'case_id': case_id, 'trial': 1, 'execution_id': execution_id}
        for case_id, execution_id in executions.items()
    ]
    batch_path.write_text(json.dumps(scored_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(), capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))
    assert scored['counts'] == {
        'planned': 5, 'attempted': 4, 'guide_run': 3, 'role_wait': 1,
        'preparation_failed': 0, 'runner_failed': 0, 'not_run': 1,
    }
    rows = {row['execution_id']: row for row in scored['cases']}
    assert rows[executions['policy-no-plan']]['business_verdict'] == 'pass'
    assert rows[executions['policy-no-plan']]['human_quality'] is None
    role_wait = rows[executions['role-wait-no-switch']]
    assert role_wait['business_verdict'] == 'fail'
    assert role_wait['human_quality'] is None
    assert any(row['code'] == 'unauthorized_role_change' and row['severity'] == 'critical'
               for row in role_wait['violations'])
    null_check = rows[executions['null-budget-check']]
    assert null_check['business_verdict'] == 'unknown'
    assert null_check['budget_fen'] is None
    assert null_check['evidence_gaps']
    assert rows[executions['later-policy-no-plan']]['business_verdict'] == 'pass'
    omitted = rows[executions['planned-row-omitted']]
    assert omitted['outcome'] == 'not_run'
    assert omitted['business_verdict'] == 'unknown'


def test_score_batch_min_length_check_handles_public_plan_item_arrays(tmp_path):
    import hashlib

    sku_id = 'demo:snack-soda-crackers-100g-box'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'score-min-length-v1',
        'cases': [{
            'case_id': 'one-plan-item', 'message': '买一盒苏打饼干。',
            'category': 'purchase_planning', 'scenario_family': 'plan-list-minimum',
            'split': 'regression', 'core': True,
            'expected_behavior': '至少有一项与当前Offer相符的待确认方案。',
            'fact_sources': [
                'data/fixtures/products.json#demo:snack-soda-crackers-100g-box',
                'data/fixtures/offers.json#demo:snack-soda-crackers-100g-box',
            ],
            'checks': [
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'},
                {'path': 'after.guide.plan.items', 'operator': 'min_length', 'expected': 1},
            ],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    before = {
        'guide': {'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'keke'},
    }
    item = {
        'sku_id': sku_id, 'quantity': 1, 'unit_price_fen': 690,
        'line_total_fen': 690, 'selected': True,
    }
    after = {
        'guide': {
            'plan': {'items': [item], 'selected_total_fen': 690, 'total_price_fen': 690},
            'conditions': {},
        },
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [],
        'opening': {'role': 'keke'},
    }
    execution_id = 'one-plan-item:trial:1'
    plan_capture = capture('plan-owner', 'plan-run', 'plan-session', 'plan-request', None, None)
    plan_capture['status'] = 'waiting_confirmation'
    scored_batch = batch(case_set, [{
        'case_id': 'one-plan-item', 'trial': 1, 'execution_id': execution_id,
        'outcome': 'guide_run',
        'capture': plan_capture,
        'before': before, 'after': after,
        'catalog_facts': {'items': [{'sku_id': sku_id, 'price_fen': 690, 'sellable': True}]},
    }])
    scored_batch['plan'] = [{'case_id': 'one-plan-item', 'trial': 1, 'execution_id': execution_id}]
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(scored_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(), capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['cases'][0]['business_verdict'] == 'pass'
    assert report['cases'][0]['violations'] == []
    assert report['cases'][0]['evidence_gaps'] == []


def test_score_batch_checks_turn_confirmation_and_replay_at_each_step(tmp_path):
    import hashlib

    sku_id = 'demo:snack-original-potato-chips-70g-bag'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'score-confirm-replay-v1',
        'cases': [
            {
                'case_id': 'valid-confirm-replay',
                'message': '想买两袋70克原味薯片，请先给我一份待确认的购买方案。',
                'category': 'purchase_planning',
                'scenario_family': 'confirm-replay-step-boundary',
                'split': 'regression',
                'core': True,
                'expected_behavior': '只在明确确认步骤加购；相同确认重放不重复加购。',
                'fact_sources': [
                    'data/fixtures/products.json#demo:snack-original-potato-chips-70g-bag',
                    'data/fixtures/offers.json#demo:snack-original-potato-chips-70g-bag',
                ],
                'steps': [{'op': 'confirm_plan'}, {'op': 'repeat_confirmation'}],
                'checks': [
                    {'path': 'steps.0.capture.status', 'operator': 'eq', 'expected': 'waiting_confirmation'},
                    {'path': 'steps.1.confirmation_receipt.status', 'operator': 'eq', 'expected': 'success'},
                    {'path': 'steps.2.confirmation_receipt.status', 'operator': 'eq', 'expected': 'success'},
                    {'path': 'after.cart.items.0.quantity', 'operator': 'eq', 'expected': 2},
                ],
            },
            {
                'case_id': 'turn-write-and-replay-write',
                'message': '想买两袋70克原味薯片，请先给我一份待确认的购买方案。',
                'category': 'purchase_planning',
                'scenario_family': 'confirm-replay-step-boundary',
                'split': 'regression',
                'core': True,
                'expected_behavior': '首轮不得加购；重放确认不得再次增加购物车数量。',
                'fact_sources': [
                    'data/fixtures/products.json#demo:snack-original-potato-chips-70g-bag',
                    'data/fixtures/offers.json#demo:snack-original-potato-chips-70g-bag',
                ],
                'steps': [{'op': 'confirm_plan'}, {'op': 'repeat_confirmation'}],
                'checks': [
                    {'path': 'steps.1.confirmation_receipt.status', 'operator': 'eq', 'expected': 'success'},
                    {'path': 'steps.2.confirmation_receipt.status', 'operator': 'eq', 'expected': 'success'},
                ],
            },
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }

    plan_item = {
        'sku_id': sku_id, 'quantity': 2, 'remaining_quantity': 2,
        'unit_price_fen': 590, 'line_total_fen': 1180, 'selected': True,
    }
    plan = {
        'plan_id': 'plan-confirm-replay', 'plan_version': 1,
        'items': [plan_item], 'selected_total_fen': 1180, 'total_price_fen': 1180,
    }
    confirmation_body = {
        'plan_id': 'plan-confirm-replay', 'plan_version': 1,
        'expected_state_version': 1, 'expected_session_version': 0,
        'selected_items': [{'sku_id': sku_id, 'quantity': 2}],
    }

    def state(cart_quantity, with_plan):
        cart_items = [] if cart_quantity == 0 else [{
            'sku_id': sku_id, 'quantity': cart_quantity,
            'unit_price_fen': 590, 'line_total_fen': cart_quantity * 590,
        }]
        return {
            'guide': {
                'task_id': 'task-confirm-replay' if with_plan else None,
                'plan': plan if with_plan else None,
                'conditions': {},
            },
            'cart': {
                'items': cart_items, 'total_price_fen': cart_quantity * 590,
                'version': 1 if cart_quantity == 0 else 2,
            },
            'orders': [], 'opening': {'role': 'keke'},
        }

    def execution(case_id, owner_id, run_id, initial_cart_quantity, replay_cart_quantity):
        execution_id = f'{case_id}:trial:1'
        initial = state(0, False)
        turn_after = state(initial_cart_quantity, True)
        confirmed = state(initial_cart_quantity + 2, True)
        replayed = state(replay_cart_quantity, True)
        final_capture = capture(owner_id, run_id, f'{owner_id}-session', execution_id, None, None)
        final_capture['status'] = 'waiting_confirmation'
        receipt = {
            'status': 'success', 'operation_id': f'{run_id}-operation',
            'confirmation_id': f'{run_id}-confirmation',
            'items_added': [{'sku_id': sku_id, 'quantity': 2}],
            'cart_version': 2, 'task_id': 'task-confirm-replay',
            'state_version': 2, 'session_version': 0,
        }
        return {
            'case_id': case_id, 'trial': 1, 'execution_id': execution_id,
            'outcome': 'guide_run', 'before': initial, 'after': replayed,
            'capture': final_capture, 'captures': [final_capture],
            'catalog_facts': {'items': [{
                'sku_id': sku_id, 'price_fen': 590, 'sellable': True, 'available_qty': 30,
            }]},
            'steps': [
                {
                    'index': 0, 'op': 'turn', 'request_id': execution_id,
                    'message': cases['cases'][0]['message'],
                    'before': initial, 'after': turn_after, 'capture': final_capture,
                },
                {
                    'index': 1, 'op': 'confirm_plan',
                    'idempotency_key': f'{run_id}-confirm-key',
                    'confirmation_body': confirmation_body,
                    'confirmation_receipt': receipt,
                    'before': turn_after, 'after': confirmed, 'capture': None,
                },
                {
                    'index': 2, 'op': 'repeat_confirmation',
                    'idempotency_key': f'{run_id}-confirm-key',
                    'confirmation_body': confirmation_body,
                    'confirmation_receipt': receipt,
                    'before': confirmed, 'after': replayed, 'capture': None,
                },
            ],
        }

    executions = {
        'valid-confirm-replay': 'valid-confirm-replay:trial:1',
        'turn-write-and-replay-write': 'turn-write-and-replay-write:trial:1',
    }
    scored_batch = batch(case_set, [
        execution('valid-confirm-replay', 'owner-valid', 'run-valid', 0, 2),
        # The first turn has already added one item; replay incorrectly adds two more.
        execution('turn-write-and-replay-write', 'owner-invalid', 'run-invalid', 1, 5),
    ])
    scored_batch['plan'] = [
        {'case_id': case_id, 'trial': 1, 'execution_id': execution_id}
        for case_id, execution_id in executions.items()
    ]
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(scored_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(), capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding='utf-8'))
    rows = {row['execution_id']: row for row in report['cases']}
    valid = rows[executions['valid-confirm-replay']]
    assert valid['business_verdict'] == 'pass'
    assert valid['human_quality'] is None
    assert valid['violations'] == []

    invalid = rows[executions['turn-write-and-replay-write']]
    assert invalid['business_verdict'] == 'fail'
    assert invalid['human_quality'] is None
    assert any(row['code'] == 'unauthorized_step_cart_change' and row['severity'] == 'critical'
               for row in invalid['violations'])
    assert any(row['code'] == 'repeat_confirmation_changed_cart' and row['severity'] == 'critical'
               for row in invalid['violations'])


def test_score_batch_reports_all_run_labels_and_scopes_quality_to_last_guide_run(tmp_path):
    import hashlib

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'score-run-labels-v1',
        'cases': [{
            'case_id': 'multi-run-labels', 'message': '一般商品价格以什么为准？',
            'category': 'policy', 'scenario_family': 'multi-run-label-scope',
            'split': 'regression', 'core': False,
            'expected_behavior': '根据当前Offer说明价格依据。',
            'fact_sources': ['data/fixtures/policies.json#P-PRI-01'],
            'checks': [
                {'path': 'capture.status', 'operator': 'eq', 'expected': 'completed'},
                {'path': 'after.guide.plan', 'operator': 'eq', 'expected': None},
            ],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    case_set = {
        'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
    }
    first = capture(
        'label-owner', 'first-guide-run', 'label-session', 'multi-run:trial:1', None,
        annotation('label-owner', 'first-guide-run', 'fail'),
    )
    last = capture(
        'label-owner', 'last-guide-run', 'label-session', 'multi-run:trial:1:step:1', None,
        annotation('label-owner', 'last-guide-run', 'pass'),
    )
    initial = {
        'guide': {'task_id': None, 'plan': None, 'conditions': {}},
        'cart': {'items': [], 'total_price_fen': 0},
        'orders': [], 'opening': {'role': 'keke'},
    }
    source_batch = batch(case_set, [{
        'case_id': 'multi-run-labels', 'outcome': 'guide_run',
        'before': initial, 'after': initial,
        'capture': last, 'captures': [first, last],
        'catalog_facts': {'items': []},
    }])
    batch_path = tmp_path / 'batch.json'
    batch_path.write_text(json.dumps(source_batch, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'score.json'

    result = subprocess.run(
        [sys.executable, '-m', 'app.evaluation.score_batch',
         '--cases', str(cases_path), '--batch', str(batch_path), '--output', str(output)],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    scored = json.loads(output.read_text(encoding='utf-8'))['cases'][0]
    assert scored['business_verdict'] == 'pass'
    assert scored['human_quality'] == 'pass'
    assert scored['human_quality_scope'] == 'last_guide_run'
    assert scored['human_run_labels'] == [
        {'owner_id': 'label-owner', 'run_id': 'first-guide-run', 'verdict': 'fail'},
        {'owner_id': 'label-owner', 'run_id': 'last-guide-run', 'verdict': 'pass'},
    ]
