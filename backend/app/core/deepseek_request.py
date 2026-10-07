"""Request fields for the explicitly selected official DeepSeek profile."""
from urllib.parse import urlsplit


def official_deepseek_thinking_body(base_url: str):
    if urlsplit(base_url).hostname == 'api.deepseek.com':
        return {'thinking': {'type': 'disabled'}}
    return None
