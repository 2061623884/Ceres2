"""Reproducible hybrid build/query and the isolated local retrieval worker."""
import argparse
import json
from pathlib import Path
from app.knowledge.bge import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build-hybrid', 'hybrid', 'serve'])
    parser.add_argument('--fixtures', type=Path, default=ROOT / 'data/fixtures')
    parser.add_argument('--index', type=Path, default=ROOT / 'data/indexes/hybrid.sqlite3')
    parser.add_argument('--namespace', choices=['product', 'recipe', 'policy'], default='product')
    parser.add_argument('--query')
    args = parser.parse_args()
    if args.action == 'serve':
        from app.knowledge.worker import serve
        serve(args.index, args.fixtures)
        return
    if args.action == 'build-hybrid':
        from app.knowledge.hybrid import build
        result = build(args.fixtures, args.index)
    else:
        from app.knowledge.hybrid import search
        result = search(args.index, args.query, args.namespace, fixtures=args.fixtures)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
