"""Fetch only the handoff-pinned public BGE files into this worktree cache."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODEL = 'BAAI/bge-small-zh-v1.5'
REVISION = '7999e1d3359715c523056ef9478215996d62a620'
ALLOW = ['config.json', 'model.safetensors', 'tokenizer.json',
         'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']
CACHE = ROOT / '.cache/huggingface'
RECORD = ROOT / 'work/local-cloud-integration/local-acceptance-20261008/bge-download-record.json'


def main():
    # The measured HF CDN requires the configured local proxy on this host.
    # This invocation makes no system or product network configuration changes.
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(
        repo_id=MODEL,
        revision=REVISION,
        cache_dir=CACHE,
        local_files_only=False,
        token=False,
        allow_patterns=ALLOW,
    )).resolve()
    cache = CACHE.resolve()
    if not snapshot.is_relative_to(cache):
        raise RuntimeError('resolved snapshot escaped the worktree-owned cache')
    files = []
    for name in ALLOW:
        path = snapshot / name
        if path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as source:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(block)
            files.append({'name': name, 'bytes': path.stat().st_size,
                          'sha256': digest.hexdigest(),
                          'symlink': path.is_symlink()})
    if not any(row['name'] == 'model.safetensors' for row in files):
        raise RuntimeError('pinned snapshot is missing model.safetensors')
    record = {'model': MODEL, 'revision': REVISION, 'token': False,
              'allow_patterns': ALLOW, 'cache': str(cache),
              'snapshot': str(snapshot), 'files': files}
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'model': MODEL, 'revision': REVISION, 'token': False,
                      'file_count': len(files), 'total_bytes': sum(row['bytes'] for row in files),
                      'files': files, 'record': str(RECORD)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
