"""JSON-lines retrieval protocol; model failures are never empty evidence."""
import asyncio
import json
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path


def serve(index: Path, fixtures: Path, graph_root: Path):
    from app.knowledge.hybrid import StaleIndexError
    output = sys.stdout
    for line in sys.stdin:
        try:
            request = json.loads(line)
            with redirect_stdout(sys.stderr):
                if request['action'] == 'hybrid':
                    from app.knowledge.hybrid import search
                    result = search(index, request['query'], request['namespace'], request['limit'],
                                    allowed_ids=request['allowed_ids'], category=request['category'],
                                    expected_index_revision=request['expected_index_revision'], fixtures=fixtures)
                elif request['action'] == 'graph':
                    from app.knowledge.graph import search
                    result = asyncio.run(search(graph_root, request['query'], request['method'],
                        fixtures=fixtures, deadline=request['deadline'], graph_query_id=request['graph_query_id']))
                else:
                    raise ValueError('Unsupported retrieval action')
        except StaleIndexError:
            traceback.print_exc(file=sys.stderr)
            result = {'error': 'KNOWLEDGE_STALE'}
        except Exception:
            traceback.print_exc(file=sys.stderr)
            result = {'error': 'KNOWLEDGE_UNAVAILABLE'}
        output.write(json.dumps(result, ensure_ascii=False) + '\n')
        output.flush()
