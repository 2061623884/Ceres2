"""Verify that the pinned public BGE model can be downloaded and run on CPU."""

from __future__ import annotations

import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODEL_ID = "BAAI/bge-small-zh-v1.5"
HF_CACHE = ROOT / ".cache" / "huggingface"

# Keep this smoke independent from any user-level Hugging Face cache or token.
os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

from huggingface_hub import HfApi, snapshot_download
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    repo = HfApi().model_info(MODEL_ID, revision="main", token=False)
    revision = repo.sha
    model_dir = Path(
        snapshot_download(
            repo_id=MODEL_ID,
            revision=revision,
            cache_dir=HF_CACHE,
            token=False,
        )
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_dir,
        local_files_only=True,
        trust_remote_code=False,
    )
    model = AutoModel.from_pretrained(
        model_dir,
        local_files_only=True,
        trust_remote_code=False,
        use_safetensors=True,
    ).to("cpu")
    model.eval()

    instruction = "为这个句子生成表示以用于检索相关文章："
    rows = [instruction + "鸡蛋", "番茄炒蛋需要鸡蛋和番茄"]
    inputs = tokenizer(rows, padding=True, truncation=True, return_tensors="pt")
    with torch.inference_mode():
        outputs = model(**inputs)
        embeddings = F.normalize(outputs.last_hidden_state[:, 0], p=2, dim=1)

    weight_path = model_dir / "model.safetensors"
    result = {
        "model_id": MODEL_ID,
        "revision": revision,
        "model_path": str(model_dir),
        "weight_bytes": weight_path.stat().st_size,
        "weight_sha256": sha256(weight_path),
        "device": str(embeddings.device),
        "embedding_shape": list(embeddings.shape),
        "embedding_dimension": int(embeddings.shape[-1]),
        "finite": bool(torch.isfinite(embeddings).all()),
        "l2_norms": [float(value) for value in embeddings.norm(dim=1)],
        "torch": version("torch"),
        "transformers": version("transformers"),
        "huggingface_hub": version("huggingface-hub"),
        "implicit_hub_token_disabled": os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] == "1",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
