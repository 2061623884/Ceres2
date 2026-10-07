"""One structured and one streamed request through the registered GraphRAG provider."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dotenv import dotenv_values
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

ENV_PATH = Path("/home/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
OUTPUT = Path(__file__).with_name("provider-smoke-2026-10-07.json")


class SmokeReply(BaseModel):
    status: Literal["ok"]
    label: Literal["provider-smoke"]


def usage_summary(value) -> dict | None:
    if value is None:
        return None
    data = value.model_dump() if hasattr(value, "model_dump") else value
    return {
        key: data.get(key)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        if key in data
    }


def safe_failure(exc: Exception) -> dict:
    response = getattr(exc, "response", None)
    return {
        "type": type(exc).__name__,
        "status_code": getattr(response, "status_code", None) or getattr(exc, "status_code", None),
        "code": getattr(exc, "code", None),
        "error_type": getattr(exc, "type", None),
    }


def main() -> None:
    values = dotenv_values(ENV_PATH, encoding="utf-8")
    selected = {
        "OPENAI_BASE_URL": values.get("OPENAI_BASE_URL"),
        "OPENAI_API_KEY": values.get("OPENAI_API_KEY"),
        "LLM_MODEL": values.get("LLM_MODEL"),
    }
    if not all(isinstance(value, str) and value.strip() for value in selected.values()):
        raise RuntimeError("approved provider config is incomplete")
    # The user's current Ceres2 config enters only this dedicated test process.
    for name, value in selected.items():
        os.environ[name] = value

    from app.core.config import get_settings  # noqa: E402
    from app.knowledge.graph import config  # noqa: E402
    from app.knowledge.providers import CALLS  # noqa: E402
    from graphrag_llm.completion import create_completion  # noqa: E402

    get_settings.cache_clear()
    graph_config = config(OUTPUT.parent / "provider-smoke-root")
    completion = create_completion(
        model_config=graph_config.completion_models["chat"],
        tokenizer=object(),
    )
    host = urlparse(selected["OPENAI_BASE_URL"]).hostname
    result = {
        "model_id": selected["LLM_MODEL"],
        "base_hostname": host,
        "structured": {"attempted": True, "passed": False, "usage": None},
        "streaming": {"attempted": True, "passed": False, "usage": None},
        "calls": [],
        "failure": None,
    }
    try:
        response = completion.completion(
            messages="返回 status 为 ok、label 为 provider-smoke 的 JSON 对象。",
            response_format=SmokeReply,
            temperature=0,
            max_completion_tokens=96,
        )
        formatted = response.formatted_response
        result["structured"].update({
            "passed": isinstance(formatted, SmokeReply)
            and formatted.status == "ok"
            and formatted.label == "provider-smoke",
            "validated_fields": list(formatted.model_fields_set) if isinstance(formatted, SmokeReply) else [],
            "usage": usage_summary(response.usage),
        })
        CALLS.clear()
        stream = completion.completion(
            messages="只回复短语 smoke-ok。",
            stream=True,
            temperature=0,
            max_completion_tokens=32,
        )
        chunks = 0
        characters = 0
        for chunk in stream:
            chunks += 1
            if chunk.choices and chunk.choices[0].delta.content:
                characters += len(chunk.choices[0].delta.content)
        stream_call = next((row for row in reversed(CALLS) if row.get("streaming")), None)
        result["streaming"].update({
            "passed": chunks > 0 and characters > 0,
            "chunk_count": chunks,
            "content_characters": characters,
            "usage": usage_summary(stream_call.get("usage")) if stream_call else None,
        })
        result["calls"] = [
            {
                "kind": row.get("kind"),
                "model": row.get("model"),
                "duration_ms": row.get("duration_ms"),
                "usage": usage_summary(row.get("usage")),
                "streaming": row.get("streaming"),
                "structured": row.get("structured"),
            }
            for row in CALLS
        ]
    except Exception as exc:
        result["failure"] = safe_failure(exc)

    result["config_complete"] = True
    result["api_key_written"] = False
    result["provider_called"] = bool(result["calls"]) or result["structured"]["passed"] or result["streaming"]["passed"]
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["structured"]["passed"] or not result["streaming"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
