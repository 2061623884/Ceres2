"""The pytest entry point must isolate configuration before test collection."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_collection_ignores_parent_credentials_and_dotenv(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    suite = tmp_path / 'tests'
    suite.mkdir()
    guard = backend / 'tests' / 'conftest.py'
    (suite / 'conftest.py').write_text(guard.read_text() if guard.exists() else '')
    synthetic_dotenv = tmp_path / '.env'
    synthetic_dotenv.write_text('OPENAI_API_KEY=synthetic-dotenv-key\nHUMAN_OPERATOR_TOKEN=synthetic-dotenv-operator\n')
    # Redirect the dotenv source without ever constructing settings. The audit
    # sentinel below rejects every dotenv read, including this synthetic file.
    (tmp_path / 'conftest.py').write_text(
        'from app.core.config import Settings\n'
        f'Settings.model_config["env_file"] = {str(synthetic_dotenv)!r}\n'
    )
    (suite / 'test_probe.py').write_text(textwrap.dedent('''
        import os
        from pathlib import Path
        from app.core.database import engine
        from app.core.config import get_settings

        # These run during collection, before any fixture can replace settings.
        settings = get_settings()
        assert settings.openai_api_key == 'offline-fixture-key'
        assert settings.openai_base_url == 'http://127.0.0.1:9/v1'
        assert settings.llm_model == 'controlled-test'
        assert settings.llm_mode == 'live'
        assert settings.memory_extraction_model == 'qwen3.8-27b'
        assert settings.memory_dream_model == 'qwen3.8-27b'
        assert settings.human_operator_token == ''
        assert settings.shopping_writes_paused is False
        assert settings.business_data_mode == 'demo'
        assert settings.mercury_checkpoint_path.is_relative_to(Path(os.environ['TMPDIR']))
        assert settings.mercury_checkpoint_path.name == 'checkpoints.sqlite3'
        assert os.environ['NO_PROXY'] == os.environ['no_proxy'] == '127.0.0.1,localhost,::1'
        assert not any(name.lower() in ('http_proxy', 'https_proxy', 'all_proxy') for name in os.environ)
        assert engine.url.database == ':memory:'

        def test_fixture_can_select_its_controlled_provider(monkeypatch):
            monkeypatch.setenv('OPENAI_BASE_URL', 'http://127.0.0.1:12345/v1')
            monkeypatch.setenv('LLM_MODEL', 'controlled-pi')
            get_settings.cache_clear()
            selected = get_settings()
            assert selected.openai_base_url == 'http://127.0.0.1:12345/v1'
            assert selected.llm_model == 'controlled-pi'
            assert selected.openai_api_key == 'offline-fixture-key'
    '''))
    script = textwrap.dedent('''
        import os
        import sys

        def deny_external_io(event, args):
            if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
                if os.path.basename(os.fsdecode(args[0])) == '.env':
                    raise AssertionError('Test collection must never open dotenv')
            if event in ('socket.connect', 'socket.getaddrinfo', 'socket.bind'):
                raise AssertionError('Isolation regression must never use network')

        sys.addaudithook(deny_external_io)
        import pytest
        raise SystemExit(pytest.main(['-q', 'tests']))
    ''')
    # Do not inherit arbitrary credentials, provider URLs, proxy settings or
    # pytest plugins from the invoking developer's environment.
    environment = {
        'PATH': os.defpath,
        'HOME': str(tmp_path),
        'TMPDIR': str(tmp_path),
        'PYTHONPATH': str(backend),
        'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        'OPENAI_API_KEY': 'synthetic-parent-key',
        'openai_api_key': 'synthetic-lowercase-parent-key',
        'OPENAI_BASE_URL': 'https://synthetic-provider.invalid/v1',
        'LLM_MODEL': 'synthetic-parent-model',
        'LLM_MODE': 'synthetic-parent-mode',
        'MEMORY_EXTRACTION_MODEL': 'synthetic-parent-extraction',
        'MEMORY_DREAM_MODEL': 'synthetic-parent-dream',
        'DATABASE_URL': 'sqlite:///synthetic-parent.sqlite3',
        'MERCURY_CHECKPOINT_PATH': str(tmp_path / 'must-not-use-parent.sqlite3'),
        'HUMAN_OPERATOR_TOKEN': 'synthetic-parent-operator',
        'SHOPPING_WRITES_PAUSED': 'true',
        'BUSINESS_DATA_MODE': 'synthetic-parent-mode',
        'HTTPS_PROXY': 'http://synthetic-proxy.invalid:8080',
    }
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '1 passed' in result.stdout
