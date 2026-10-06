"""Controlled pytest defaults, installed before collection imports the app.

Applies to direct pytest and capture.py -> pytest, not arbitrary captured scripts.
Individual fixtures can still select their own loopback model server and database.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_runtime = TemporaryDirectory(prefix='ceres-controlled-tests-')
_controlled_environment = {
    'OPENAI_API_KEY': 'offline-fixture-key',
    'OPENAI_BASE_URL': 'http://127.0.0.1:9/v1',
    'LLM_MODEL': 'controlled-test',
    'LLM_MODE': 'live',
    'MEMORY_EXTRACTION_MODEL': 'qwen3.8-27b',
    'MEMORY_DREAM_MODEL': 'qwen3.8-27b',
    'DATABASE_URL': 'sqlite:///:memory:',
    'MERCURY_CHECKPOINT_PATH': str(Path(_runtime.name) / 'checkpoints.sqlite3'),
    'HUMAN_OPERATOR_TOKEN': '',
    'SHOPPING_WRITES_PAUSED': 'false',
    'BUSINESS_DATA_MODE': 'demo',
    'NO_PROXY': '127.0.0.1,localhost,::1',
    'no_proxy': '127.0.0.1,localhost,::1',
}
# Settings accepts case-insensitive aliases. Remove inherited spellings first
# so a lowercase parent credential cannot shadow the uppercase override.
for name in tuple(os.environ):
    if name.upper() in _controlled_environment or name.lower() in ('http_proxy', 'https_proxy', 'all_proxy'):
        del os.environ[name]
os.environ.update(_controlled_environment)

# Importing config defines Settings but does not instantiate it. Disable dotenv
# before database/main/test modules can create and cache the first Settings.
from app.core.config import Settings, get_settings

Settings.model_config['env_file'] = None
get_settings.cache_clear()
