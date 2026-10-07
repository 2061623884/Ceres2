"""JSON-lines worker; model/index dependencies stay outside the business env."""
import asyncio
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path


def serve(index: Path, graph_root: Path):
    output = sys.stdout
    for line in sys.stdin:
        request = json.loads(line)
        with redirect_stdout(sys.stderr):
            if request['action'] == 'hybrid':
                from app.knowledge.hybrid import search
                result = search(index, request['query'], request['namespace'], request['limit'],
                    allowed_ids=request.get('allowed_ids'), category=request.get('category'))
            else:
                from app.knowledge.graph import search
                result = asyncio.run(search(graph_root, request['query'], request['method']))
        output.write(json.dumps(result, ensure_ascii=False)+'\n')
        output.flush()
