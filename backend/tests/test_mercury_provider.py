"""Provider wire contract is separate from actual-model quality evidence."""
from types import SimpleNamespace
import pytest


@pytest.mark.parametrize('fails', [False, True])
def test_query_provider_closes_client_and_uses_shared_configuration(monkeypatch, fails):
    from app.mercury import provider
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, 'openai_base_url', 'http://provider-fixture.invalid/v1')
    monkeypatch.setattr(settings, 'openai_api_key', 'synthetic-not-a-real-key')
    monkeypatch.setattr(settings, 'llm_model', 'qwen3.8-27b')
    captured = {}
    class Client:
        def __init__(self, **kwargs):
            captured['client'] = kwargs
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            captured['closed'] = True
        def create(self, **kwargs):
            captured['request'] = kwargs
            if fails:
                raise RuntimeError('synthetic transport error')
            return SimpleNamespace(choices=[SimpleNamespace(message='response')])
    monkeypatch.setattr(provider, 'OpenAI', Client)
    port = provider.QueryChatClient()
    if fails:
        with pytest.raises(RuntimeError):
            port.chat([{'role': 'user', 'content': '查询'}], tools=[])
    else:
        assert port.chat([{'role': 'user', 'content': '查询'}], tools=[]) == 'response'
    assert captured['closed'] and port.client is None
    assert captured['client']['max_retries'] == 0
    assert captured['client']['timeout'] == 15
    assert captured['request']['model'] == 'qwen3.8-27b'
    assert captured['request']['tool_choice'] == 'auto'
