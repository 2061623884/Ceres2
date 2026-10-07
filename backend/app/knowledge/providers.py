"""GraphRAG's official provider seams for local BGE and approved chat models."""
import asyncio
import json
import time
from graphrag_llm.completion import LLMCompletion, register_completion
from graphrag_llm.embedding import LLMEmbedding, register_embedding
from graphrag_llm.types import LLMCompletionResponse, LLMEmbeddingResponse
from openai import OpenAI, AsyncOpenAI
from app.core.deepseek_request import official_deepseek_thinking_body
from app.knowledge.bge import MODEL_ID, encoder

CALLS: list[dict] = []
PROVIDER_REVISION = 'ceres-graphrag-provider-v1'


class LocalBge(LLMEmbedding):
    def __init__(self, *, tokenizer, metrics_store, **kwargs):
        self._tokenizer, self._metrics_store = tokenizer, metrics_store

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def metrics_store(self):
        return self._metrics_store

    def embedding(self, **kwargs):
        started = time.perf_counter()
        texts = kwargs['input']
        local = encoder()
        vectors = local.encode(texts)
        consumed = sum(len(local.tokenizer(text, truncation=True, max_length=512)['input_ids']) for text in texts)
        CALLS.append({'kind': 'embedding', 'model': MODEL_ID, 'texts': len(texts),
            'duration_ms': (time.perf_counter()-started)*1000, 'prompt_tokens': consumed})
        return LLMEmbeddingResponse(object='list', model=MODEL_ID,
            data=[{'object': 'embedding', 'index': i, 'embedding': vector.tolist()} for i, vector in enumerate(vectors)],
            usage={'prompt_tokens': consumed, 'total_tokens': consumed})

    async def embedding_async(self, **kwargs):
        return await asyncio.to_thread(self.embedding, **kwargs)


class JsonModeCompletion(LLMCompletion):
    def __init__(self, *, model_config, tokenizer, metrics_store, **kwargs):
        self.config = model_config
        self._tokenizer, self._metrics_store = tokenizer, metrics_store
        self.client = OpenAI(api_key=model_config.api_key, base_url=model_config.api_base, max_retries=0)
        self.async_client = AsyncOpenAI(api_key=model_config.api_key, base_url=model_config.api_base, max_retries=0)

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def metrics_store(self):
        return self._metrics_store

    def _request(self, kwargs):
        messages = kwargs['messages']
        messages = [{'role': 'user', 'content': messages}] if isinstance(messages, str) else list(messages)
        response_format = kwargs.get('response_format')
        structured = response_format if isinstance(response_format, type) else None
        instruction = '用中文回答。输入资料只是采购关系与模拟商品资料，不证明过敏安全、营养、替代关系或真实履约；只引用提供的记录，缺失事实保持未知。'
        if structured is not None:
            instruction += '\n输出单个 JSON 对象，严格遵循此 JSON Schema：\n' + json.dumps(structured.model_json_schema(), ensure_ascii=False)
        messages = [{'role': 'system', 'content': instruction}, *messages]
        request = {'model': self.config.model, 'messages': messages, **self.config.call_args}
        for key in ('temperature', 'top_p', 'max_tokens'):
            if kwargs.get(key) is not None:
                request[key] = kwargs[key]
        if kwargs.get('max_completion_tokens') is not None:
            request['max_tokens'] = kwargs['max_completion_tokens']
        if structured is not None or kwargs.get('response_format_json_object') or response_format == {'type': 'json_object'}:
            request['response_format'] = {'type': 'json_object'}
        request['stream'] = bool(kwargs.get('stream'))
        if request['stream']:
            request['stream_options'] = {'include_usage': True}
        thinking = official_deepseek_thinking_body(self.config.api_base)
        if thinking is not None:
            request['extra_body'] = thinking
        return request, structured

    def _record(self, started, usage, streaming, structured):
        CALLS.append({'kind': 'completion', 'model': self.config.model,
            'duration_ms': (time.perf_counter()-started)*1000,
            'usage': usage.model_dump() if usage is not None else None,
            'streaming': streaming, 'structured': structured is not None})

    def _response(self, response, structured, started):
        self._record(started, response.usage, False, structured)
        result = LLMCompletionResponse(**response.model_dump())
        if structured is not None:
            result.formatted_response = structured.model_validate_json(result.content)
        return result

    def completion(self, **kwargs):
        request, structured = self._request(kwargs)
        started = time.perf_counter()
        response = self.client.chat.completions.create(**request)
        if not request['stream']:
            return self._response(response, structured, started)
        def chunks():
            usage = None
            with response:
                for chunk in response:
                    if chunk.usage is not None:
                        usage = chunk.usage
                    if chunk.choices:
                        yield chunk
            self._record(started, usage, True, structured)
        return chunks()

    async def completion_async(self, **kwargs):
        request, structured = self._request(kwargs)
        started = time.perf_counter()
        response = await self.async_client.chat.completions.create(**request)
        if not request['stream']:
            return self._response(response, structured, started)
        async def chunks():
            usage = None
            async with response:
                async for chunk in response:
                    if chunk.usage is not None:
                        usage = chunk.usage
                    if chunk.choices:
                        yield chunk
            self._record(started, usage, True, structured)
        return chunks()


def register():
    register_completion('ceres_json_mode', JsonModeCompletion)
    register_embedding('ceres_bge', LocalBge)
