"""Graph CLI jobs have killable process boundaries; Guide owns its own deadline."""
import argparse
import asyncio
from contextlib import redirect_stdout
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
from uuid import uuid4
from app.knowledge.bge import ROOT


def graph_job():
    """Single supervised child job; stdout is reserved for its JSON result."""
    request = json.loads(sys.stdin.readline())
    with redirect_stdout(sys.stderr):
        try:
            from app.knowledge.graph import build, search
            root, fixtures = Path(request['graph_root']), Path(request['fixtures'])
            if request['action'] == 'build-graph':
                result = asyncio.run(build(fixtures, root, deadline=request['deadline']))
            else:
                result = asyncio.run(search(root, request['query'], request['method'],
                    fixtures=fixtures, deadline=request['deadline'], graph_query_id=request['graph_query_id']))
        except Exception:
            traceback.print_exc()
            result = {'error': 'GRAPH_BUILD_FAILED' if request['action'] == 'build-graph' else 'GRAPH_UNAVAILABLE'}
    print(json.dumps(result, ensure_ascii=False))


def supervise_graph_job(request):
    """Timeout/interrupt kills even a model thread stuck during asyncio shutdown."""
    building = request['action'] == 'build-graph'
    manifest = Path(request['graph_root']) / 'manifest.json'
    if building:
        # A rebuild is invalid until a fully completed child publishes its manifest.
        manifest.unlink(missing_ok=True)
    failure = {'graph_query_id': request['graph_query_id'], 'method': request.get('method'),
               'graph_status': 'unobserved', 'official_graph_calls': None,
               'calls': None, 'call_counts': None}
    remaining = request['deadline'] - time.monotonic()
    if remaining <= 0:
        return {**failure, 'error': 'KNOWLEDGE_TIMEOUT', 'graph_status': 'not_executed'}
    child = subprocess.Popen([sys.executable, '-c', 'from app.knowledge.cli import graph_job; graph_job()'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        remaining = request['deadline'] - time.monotonic()
        stdout, _ = child.communicate(json.dumps(request) + '\n', timeout=max(0, remaining))
        if time.monotonic() >= request['deadline']:
            result = {**failure, 'error': 'KNOWLEDGE_TIMEOUT'}
        elif child.returncode:
            result = {**failure, 'error': 'GRAPH_BUILD_FAILED' if building else 'GRAPH_UNAVAILABLE'}
        else:
            result = json.loads(stdout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        # Bounded private cause; never print the request, command arguments or query.
        print('Graph CLI child interrupted: ' + type(error).__name__, file=sys.stderr)
        child.kill()
        # Reaping cannot add a fresh wait budget after the job deadline.
        threading.Thread(target=child.wait, daemon=True).start()
        child.stdin.close()
        child.stdout.close()
        result = {**failure, 'error': 'KNOWLEDGE_CANCELLED' if isinstance(error, KeyboardInterrupt) else 'KNOWLEDGE_TIMEOUT'}
    if building and result.get('error'):
        manifest.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        'Examples: graph --query 鸡蛋 --method local; '
        'build-graph --timeout-seconds 120. Offline build budget is explicit and independent of the 15-second Guide budget.'))
    parser.add_argument('action', choices=['build-hybrid', 'hybrid', 'build-graph', 'graph', 'serve'])
    parser.add_argument('--fixtures', type=Path, default=ROOT / 'data/fixtures')
    parser.add_argument('--index', type=Path, default=ROOT / 'data/indexes/hybrid.sqlite3')
    parser.add_argument('--graph-root', type=Path, default=ROOT / 'data/indexes/graphrag')
    parser.add_argument('--namespace', choices=['product', 'recipe', 'policy'], default='product')
    parser.add_argument('--method', choices=['local', 'global'], default='local')
    parser.add_argument('--query')
    parser.add_argument('--deadline', type=float, help='Graph query caller absolute monotonic deadline; default is 15 seconds from this CLI invocation')
    parser.add_argument('--timeout-seconds', type=float, help='Required finite positive budget for an independent offline build-graph job')
    started = time.monotonic()
    args = parser.parse_args()
    if args.action == 'build-graph':
        if args.deadline is not None or args.timeout_seconds is None or not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
            parser.error('build-graph requires a finite positive --timeout-seconds, not a Guide --deadline')
        deadline = started + args.timeout_seconds
    else:
        if args.timeout_seconds is not None:
            parser.error('--timeout-seconds is only for offline build-graph')
        if args.deadline is not None and (args.action != 'graph' or not math.isfinite(args.deadline)):
            parser.error('--deadline is only a finite absolute graph query deadline')
        deadline = args.deadline if args.deadline is not None else started + 15
    if args.action == 'serve':
        from app.knowledge.worker import serve
        serve(args.index, args.fixtures, args.graph_root)
        return
    if args.action in ('graph', 'build-graph'):
        result = supervise_graph_job({'action': args.action, 'fixtures': str(args.fixtures),
            'graph_root': str(args.graph_root), 'query': args.query, 'method': args.method,
            'deadline': deadline, 'graph_query_id': uuid4().hex})
    elif args.action == 'build-hybrid':
        from app.knowledge.hybrid import build
        result = build(args.fixtures, args.index)
    else:
        from app.knowledge.hybrid import search
        result = search(args.index, args.query, args.namespace, fixtures=args.fixtures)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
