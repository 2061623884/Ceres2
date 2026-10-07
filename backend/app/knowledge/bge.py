"""Pinned, local CPU BGE encoding shared by hybrid retrieval and GraphRAG."""
from pathlib import Path
import threading

MODEL_ID = 'BAAI/bge-small-zh-v1.5'
MODEL_REVISION = '7999e1d3359715c523056ef9478215996d62a620'
DIMENSIONS = 512
ROOT = Path(__file__).resolve().parents[3]


class BgeEncoder:
    def __init__(self):
        from huggingface_hub import snapshot_download
        from transformers import AutoModel, AutoTokenizer
        snapshot = snapshot_download(MODEL_ID, revision=MODEL_REVISION,
            cache_dir=ROOT / '.cache/huggingface', local_files_only=True, token=False)
        self.tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
        self.model = AutoModel.from_pretrained(snapshot, local_files_only=True,
            trust_remote_code=False, use_safetensors=True).to('cpu').eval()

    def encode(self, texts: list[str]):
        import numpy as np
        import torch
        import torch.nn.functional as F
        batches = []
        for start in range(0, len(texts), 16):
            inputs = self.tokenizer(texts[start:start+16], padding=True, truncation=True,
                max_length=512, return_tensors='pt')
            with torch.inference_mode():
                output = self.model(**inputs)
                batches.append(F.normalize(output.last_hidden_state[:, 0], p=2, dim=1).numpy())
        return np.concatenate(batches).astype('<f4')


_INITIALIZE = threading.Lock()
_ENCODER: BgeEncoder | None = None


def encoder() -> BgeEncoder:
    global _ENCODER
    # GraphRAG starts multiple embedding tasks. Transformers' lazy imports
    # must complete once before another task can access the same local model.
    with _INITIALIZE:
        if _ENCODER is None:
            _ENCODER = BgeEncoder()
        return _ENCODER
