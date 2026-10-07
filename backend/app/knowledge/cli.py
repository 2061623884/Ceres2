"""Reproducible demo build/query entry point, using the isolated knowledge env."""
import argparse
import asyncio
import json
from pathlib import Path
from app.knowledge.bge import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build-hybrid', 'hybrid', 'build-graph', 'graph', 'serve'])
    parser.add_argument('--fixtures', type=Path, default=ROOT / 'data/fixtures')
    parser.add_argument('--index', type=Path, default=ROOT / 'data/indexes/hybrid.sqlite3')
    parser.add_argument('--graph-root', type=Path, default=ROOT / 'data/indexes/graphrag')
    parser.add_argument('--namespace', choices=['product', 'recipe', 'policy'], default='product')
    parser.add_argument('--method', choices=['local', 'global'], default='local')
    parser.add_argument('--query')
    args = parser.parse_args()
    if args.action == 'build-hybrid':
        from app.knowledge.hybrid import build
        result = build(args.fixtures, args.index)
    elif args.action == 'hybrid':
        from app.knowledge.hybrid import search
        result = search(args.index, args.query, args.namespace)
    elif args.action == 'build-graph':
        from app.knowledge.graph import build
        result = asyncio.run(build(args.fixtures, args.graph_root))
    elif args.action == 'graph':
        from app.knowledge.graph import search
        result = asyncio.run(search(args.graph_root, args.query, args.method))
    else:
        from app.knowledge.worker import serve
        serve(args.index, args.graph_root)
        return
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
