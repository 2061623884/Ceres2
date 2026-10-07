"""Official api.deepseek.com enables thinking unless the request disables it."""
from urllib.parse import urlparse


def official_deepseek_thinking_body(base_url: str):
    if urlparse(base_url).hostname == 'api.deepseek.com':
        return {'thinking': {'type': 'disabled'}}
    return None
