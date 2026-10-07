"""JSON-lines retrieval protocol; local model failures are never empty hits."""
import json
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path


def serve(index: Path, fixtures: Path):
    from app.knowledge.hybrid import search, StaleIndexError
    output = sys.stdout
    for line in sys.stdin:
        try:
            request = json.loads(line)
            with redirect_stdout(sys.stderr):
                if request['action'] != 'hybrid':
                    raise ValueError('Unsupported retrieval action')
                result = search(index, request['query'], request['namespace'], request['limit'],
                                allowed_ids=request['allowed_ids'], category=request['category'],
                                expected_index_revision=request['expected_index_revision'], fixtures=fixtures)
        except StaleIndexError:
            traceback.print_exc(file=sys.stderr)
            result = {'error': 'KNOWLEDGE_STALE'}
        except Exception:
            traceback.print_exc(file=sys.stderr)
            result = {'error': 'KNOWLEDGE_UNAVAILABLE'}
        output.write(json.dumps(result, ensure_ascii=False) + '\n')
        output.flush()
