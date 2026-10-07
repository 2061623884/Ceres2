"""Read approved completion config from the user's current Ceres2 .env safely."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

SOURCE = Path("/home/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
OUTPUT = Path(__file__).with_name("provider-config-probe-2026-10-07.json")


def main() -> None:
    if not SOURCE.is_file():
        result = {"source_exists": False, "config_complete": False, "network_checked": False}
    else:
        values = dotenv_values(SOURCE, encoding="utf-8")
        model = (values.get("LLM_MODEL") or "").strip()
        base_url = (values.get("OPENAI_BASE_URL") or "").strip()
        key_present = bool((values.get("OPENAI_API_KEY") or "").strip())
        parsed = urlparse(base_url)
        hostname = parsed.hostname
        result = {
            "source_exists": True,
            "model_id": model or None,
            "base_hostname": hostname,
            "api_key_present": key_present,
            "base_url_valid": parsed.scheme in {"http", "https"} and bool(hostname),
            "config_complete": bool(model and key_present and parsed.scheme in {"http", "https"} and hostname),
            "network_checked": False,
        }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
