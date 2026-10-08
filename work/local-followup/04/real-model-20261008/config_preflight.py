"""Presence-only inspection of the explicitly authorized original dotenv file.

This program never prints values from the file and never mutates process env.
"""
from __future__ import annotations

import hashlib
import json
from urllib.parse import urlsplit

from harness_config import FIELDS, SOURCE_ENV as SOURCE, is_nonempty, read_source_values


def _safe_origin(value: object) -> str | None:
    if not value:
        return None
    try:
        parsed = urlsplit(str(value))
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
            return 'configured-invalid-or-non-http-origin'
        host = parsed.hostname
        port = f':{parsed.port}' if parsed.port else ''
        return f'{parsed.scheme}://{host}{port}'
    except (TypeError, ValueError):
        return 'configured-invalid-or-non-http-origin'


def main() -> None:
    values = read_source_values(SOURCE)
    nonempty = {
        key: is_nonempty(values, key)
        for fields in FIELDS.values()
        for key in fields
    }
    for scope, fields in FIELDS.items():
        print(f'{scope}.ready={str(all(nonempty[field] for field in fields)).lower()}')
        for field in fields:
            print(f'{scope}.{field}.nonempty={str(nonempty[field]).lower()}')

    model = str(values.get('LLM_MODEL') or '').strip()
    print(f'main_model_id={model if model else "<missing>"}')
    print(f'main_api_origin={_safe_origin(values.get("OPENAI_BASE_URL")) or "<missing>"}')
    print(f'kev_origin={_safe_origin(values.get("KEV_BASE_URL")) or "<missing>"}')

    # Hash only non-secret IDs and sanitized origins, never the API key or raw URL.
    nonsecret = {
        'OPENAI_ORIGIN': _safe_origin(values.get('OPENAI_BASE_URL')),
        'LLM_MODEL': model or None,
        'LLM_MODE': str(values.get('LLM_MODE') or '').strip() or None,
        'MEMORY_EXTRACTION_MODEL': str(values.get('MEMORY_EXTRACTION_MODEL') or '').strip() or None,
        'MEMORY_DREAM_MODEL': str(values.get('MEMORY_DREAM_MODEL') or '').strip() or None,
        'KEV_ORIGIN': _safe_origin(values.get('KEV_BASE_URL')),
    }
    canonical = json.dumps(nonsecret, sort_keys=True, separators=(',', ':')).encode()
    print(f'nonsecret_config_sha256={hashlib.sha256(canonical).hexdigest()}')


if __name__ == '__main__':
    main()
