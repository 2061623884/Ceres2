"""Run the demo GraphRAG build with only the approved current Ceres2 provider config."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

ENV_PATH = Path("/home/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
FIXTURES = ROOT / "data/fixtures"
GRAPH_ROOT = ROOT / "data/indexes/graphrag"
OUTPUT = Path(__file__).with_name("graph-build-smoke-v3-2026-10-07.json")


def main() -> None:
    values = dotenv_values(ENV_PATH, encoding="utf-8")
    selected = {
        "OPENAI_BASE_URL": values.get("OPENAI_BASE_URL"),
        "OPENAI_API_KEY": values.get("OPENAI_API_KEY"),
        "LLM_MODEL": values.get("LLM_MODEL"),
    }
    if not all(isinstance(value, str) and value.strip() for value in selected.values()):
        raise RuntimeError("approved provider config is incomplete")
    if GRAPH_ROOT.exists() and any(GRAPH_ROOT.iterdir()):
        raise RuntimeError("isolated graph output path is not empty")
    for name, value in selected.items():
        os.environ[name] = value

    from app.core.config import get_settings  # noqa: E402
    from app.knowledge.graph import build  # noqa: E402

    get_settings.cache_clear()
    manifest = asyncio.run(build(FIXTURES, GRAPH_ROOT))
    calls = manifest["calls"]
    completion_calls = [call for call in calls if call.get("kind") == "completion"]
    embedding_calls = [call for call in calls if call.get("kind") == "embedding"]
    report = {
        "exit_result": "success",
        "provider_model": selected["LLM_MODEL"],
        "provider_host": urlparse(selected["OPENAI_BASE_URL"]).hostname,
        "graph_root": str(GRAPH_ROOT),
        "source_counts": manifest["counts"],
        "graph_counts": manifest["graph_counts"],
        "output_counts": manifest["output_counts"],
        "provider_revision": manifest["provider_revision"],
        "call_count": len(calls),
        "completion_call_count": len(completion_calls),
        "embedding_call_count": len(embedding_calls),
        "completion_usage": [call.get("usage") for call in completion_calls],
        "embedding_usage": [
            {"prompt_tokens": call.get("prompt_tokens"), "texts": call.get("texts")}
            for call in embedding_calls
        ],
        "api_key_written": False,
        "manifest_path": str(GRAPH_ROOT / "manifest.json"),
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
