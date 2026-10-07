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
    'KEV_BASE_URL': '',
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

# New role ingress always executes the production Kev parser/transport contract.
# Inherited business tests use a controlled current-role response, not live routing
# acceptance. Dedicated routing tests explicitly replace this transport's chooser.
# Both decisions execute the same production parser/transport. calls contains ALL
# actual requests; entry_calls/policy_calls are purpose-aware views for exact counts.
# No test-name switches, external network fallbacks, or business-service bypasses.
import json
from types import SimpleNamespace
import httpx
import pytest


@pytest.fixture(autouse=True)
def controlled_kev_transport(monkeypatch):
    from app.services import kev_provider
    control = {'calls': [], 'entry_calls': [], 'policy_calls': [],
               'choose': lambda state: 'no', 'choose_policy': lambda state: 'no'}
    def handle(request):
        assert request.url == httpx.URL('http://kev-controlled.invalid/v1/systemone')
        payload = json.loads(request.content)
        control['calls'].append(payload)
        purpose = next(iter(payload['questions']))
        control['policy_calls' if purpose == 'policy' else 'entry_calls'].append(payload)
        choice = control['choose_policy' if purpose == 'policy' else 'choose'](payload['state'])
        if isinstance(choice, httpx.HTTPError):
            raise choice
        if isinstance(choice, Exception):
            raise httpx.ConnectError(str(choice), request=request)
        return httpx.Response(200, json={'model':'kev-latest', 'answers':{purpose:{
            'type':'choice', 'choice':choice,
            'probabilities':{key:float(key == choice) for key in kev_provider.CRITERIA}}}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as fixture_client:
        monkeypatch.setattr(kev_provider, 'client', lambda:fixture_client)
        monkeypatch.setattr(kev_provider, 'get_settings', lambda:SimpleNamespace(kev_base_url='http://kev-controlled.invalid'))
        yield control
