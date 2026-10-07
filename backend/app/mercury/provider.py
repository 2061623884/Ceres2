"""Cancellable provider port; configuration is shared with the application."""
from openai import OpenAI
from app.core.config import get_settings
from app.core.deepseek_request import official_deepseek_thinking_body


class QueryChatClient:
    def __init__(self):
        self.client = None
        self.cancelled = False

    def chat(self, messages, tools=None):
        if self.cancelled:
            raise TimeoutError('Query cancelled')
        settings = get_settings()
        with OpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key,
                    timeout=15, max_retries=0) as client:
            self.client = client
            try:
                if self.cancelled:
                    raise TimeoutError('Query cancelled')
                request = dict(model=settings.llm_model, messages=messages,
                    tools=tools, tool_choice='auto', temperature=0.2)
                thinking = official_deepseek_thinking_body(settings.openai_base_url)
                if thinking is not None:
                    request['extra_body'] = thinking
                return client.chat.completions.create(**request).choices[0].message
            finally:
                self.client = None

    def cancel(self):
        self.cancelled = True
        if self.client is not None:
            self.client.close()
