"""Same-provider semantic smoke for approved lookup plans and guarded claims.

This is a small prompt-path check, not a blind quality score. It deliberately
stores only case IDs, verdicts, lengths, hashes, and provider usage metadata.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
TESTING = Path(__file__).resolve().parent
OUTPUT = TESTING / "interim-claim-semantic-audit-v2-2026-10-07.json"
POLICY_PLAN = (
    TESTING / "tmp/pi-real-smoke/product-policy-rejected-audit-capture-v2/"
    "rejected-audit-candidates.jsonl"
)
RECIPE_SSE = (
    TESTING / "tmp/pi-real-smoke/recipe-relations-current-v4/guide-sse.jsonl"
)
GENERAL_CLAIM_JS = ROOT / "runtime/pi/dist/general-claim.js"
GENERAL_CLAIM_TS = ROOT / "runtime/pi/src/general-claim.ts"
WORKER_DIST = ROOT / "runtime/pi/dist/worker.js"
CASES = [
    ("captured_product_policy_lookup_plan", True, False, False, "captured"),
    ("captured_live_recipe_lookup_plan", True, False, False, "captured"),
    ("chinese_egg_lookup_plan", True, False, False, "authored"),
    ("factual_price_claim", False, True, False, "authored"),
    ("factual_stock_claim", False, True, False, "authored"),
    ("claimed_ingredient_result", False, True, False, "authored"),
    ("policy_eligibility_claim", False, True, False, "authored"),
    ("positive_purchase_promise", False, False, True, "authored"),
    ("already_added_claim", False, False, True, "authored"),
    ("held_unfamiliar_recipe_quantity", False, True, False, "held_variant"),
    ("held_ingredient_only_recipe_result", False, True, False, "held_variant"),
    ("held_shared_ingredient_recipe_result", False, True, False, "held_variant"),
    ("held_same_targets_lookup_plan", True, False, False, "held_variant"),
]
AUTHORED_TEXT = {
    "chinese_egg_lookup_plan": "我先查鸡蛋有哪些商品规格和当前模拟价格，再对照菜谱用量；这一步只查信息，不加购。",
    "factual_price_claim": "鲜鸡蛋10枚装当前模拟价格是12.80元。",
    "factual_stock_claim": "鲜鸡蛋10枚装目前有货，库存25件。",
    "claimed_ingredient_result": "番茄炒蛋需要鸡蛋3枚，蛋炒饭需要鸡蛋2枚。",
    "policy_eligibility_claim": "这盒未开封买错的酸奶符合七天无理由退货条件。",
    "positive_purchase_promise": "我会把这盒鸡蛋加购到你的购物车。",
    "already_added_claim": "我已经替你加购了一盒鸡蛋。",
    "held_unfamiliar_recipe_quantity": "红烧冬瓜两人份需要冬瓜500克。",
    "held_ingredient_only_recipe_result": "番茄炒蛋和蛋炒饭都需要鸡蛋。",
    "held_shared_ingredient_recipe_result": "这两道菜的共有必需食材是鸡蛋。",
    "held_same_targets_lookup_plan": "我先查番茄炒蛋的鸡蛋用量是否为3枚、蛋炒饭是否为2枚，再核对鸡蛋商品规格；现在还不下结论。",
}


def provider_config() -> dict[str, str]:
    path = Path("/data/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    selected = {key: values.get(key, "") for key in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "LLM_MODEL")}
    if not all(selected.values()):
        raise RuntimeError("Approved provider settings are incomplete")
    return selected


def exact_prompt() -> str:
    command = [
        "node", "--input-type=module", "-e",
        f"import {{ INTERIM_CLAIM_PROMPT }} from {json.dumps(GENERAL_CLAIM_JS.as_uri())}; "
        "process.stdout.write(JSON.stringify(INTERIM_CLAIM_PROMPT));",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True, timeout=10)
    return json.loads(result.stdout)


def read_captured_candidate(path: Path, index: int = 0) -> str:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidate = rows[index]["candidate"]
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("Captured audit candidate is empty")
    return candidate


def read_captured_interim(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        frame = json.loads(line)
        if frame.get("type") == "message.interim":
            content = (frame.get("payload") or {}).get("content")
            if isinstance(content, str) and content.strip():
                return content
    raise ValueError("Current recipe SSE has no published interim to audit")


def audit_candidate(base_url: str, key: str, model: str, prompt: str, candidate: str) -> dict:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps([candidate], ensure_ascii=False)},
        ],
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": 256,
        "thinking": {"type": "disabled"},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "text/event-stream", "Authorization": f"Bearer {key}"},
    )
    started = time.monotonic()
    output = ""
    usage = None
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    continue
                chunk = json.loads(data)
                choices = chunk.get("choices") or []
                if choices:
                    output += ((choices[0].get("delta") or {}).get("content") or "")
                if chunk.get("usage"):
                    usage = chunk["usage"]
        parsed = json.loads(output)
        valid = (
            isinstance(parsed, dict)
            and set(parsed) == {"merchant_claims", "execution_claims"}
            and isinstance(parsed["merchant_claims"], bool)
            and isinstance(parsed["execution_claims"], bool)
        )
        return {
            "provider_result": "completed",
            "schema_valid": valid,
            "verdict": parsed if valid else None,
            "usage": usage,
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as error:
        status = error.code if isinstance(error, urllib.error.HTTPError) else None
        return {
            "provider_result": "error",
            "http_status": status,
            "failure_class": type(error).__name__,
            "failure_fingerprint": hashlib.sha256(str(error).encode()).hexdigest(),
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
            "api_key_recorded": False,
        }


def main() -> int:
    config = provider_config()
    prompt = exact_prompt()
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    captured = {
        "captured_product_policy_lookup_plan": read_captured_candidate(POLICY_PLAN),
        "captured_live_recipe_lookup_plan": read_captured_interim(RECIPE_SSE),
    }
    text_by_id = {**captured, **AUTHORED_TEXT}
    source_paths = (GENERAL_CLAIM_TS, GENERAL_CLAIM_JS, WORKER_DIST)
    results = []
    for case_id, expected_allowed, expected_merchant, expected_execution, origin in CASES:
        candidate = text_by_id[case_id]
        observed = audit_candidate(config["OPENAI_BASE_URL"], config["OPENAI_API_KEY"], config["LLM_MODEL"], prompt, candidate)
        expected = {"merchant_claims": expected_merchant, "execution_claims": expected_execution}
        verdict = observed.get("verdict")
        matches = observed.get("schema_valid") is True and verdict == expected
        results.append({
            "case_id": case_id,
            "origin": origin,
            "expected_allowed": expected_allowed,
            "candidate_characters": len(candidate),
            "candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
            "expected_verdict": expected,
            "observed": observed,
            "match": matches,
        })

    complete = [result for result in results if result["observed"]["provider_result"] == "completed"]
    report = {
        "evaluation_type": "same-model semantic smoke; not blind and not an independent accuracy score",
        "provider": {
            "model_id": config["LLM_MODEL"],
            "base_hostname": urlsplit(config["OPENAI_BASE_URL"]).hostname,
            "api_key_recorded": False,
        },
        "api_shape": "OpenAI-compatible streamed chat completion; exact compiled INTERIM_CLAIM_PROMPT; same model, base URL, disabled thinking, max_tokens 256; no JSON-mode override",
        "prompt_sha256": prompt_hash,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        },
        "denominator": len(CASES),
        "completed": len(complete),
        "schema_valid": sum(result["observed"].get("schema_valid") is True for result in results),
        "expected_verdict_matches": sum(result["match"] for result in results),
        "allow_cases": sum(result["expected_allowed"] for result in results),
        "reject_cases": sum(not result["expected_allowed"] for result in results),
        "results": results,
        "conclusion": "Prompt-path samples only; no blind or human review is claimed.",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, ensure_ascii=False, indent=2))
    print(json.dumps([
        {"case_id": result["case_id"], "match": result["match"], "observed": result["observed"].get("verdict"), "provider_result": result["observed"]["provider_result"]}
        for result in results
    ], ensure_ascii=False, indent=2))
    print(f"report_path={OUTPUT}")
    return 0 if len(complete) == len(CASES) and all(result["match"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
