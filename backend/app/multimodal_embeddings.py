"""Multimodal embedding helpers (image)."""

from __future__ import annotations

import asyncio
import os
from typing import List

from app.core.logging_config import get_logger
from app.config import get_integration_setting
from app.model_cache import configure_model_cache_env, get_model_cache_dir

logger = get_logger(__name__)

_model = None
_preprocess = None
_tokenizer = None
_device = "cpu"


def _load_model():
    global _model, _preprocess, _tokenizer
    if _model is not None:
        return
    try:
        import open_clip
        import torch
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("open_clip_torch/torch/Pillow are required for image embeddings") from exc

    cache_dir = get_model_cache_dir()
    configure_model_cache_env(cache_dir)

    cpu_threads_raw = get_integration_setting("multimodal", "cpu_threads", "0")
    cpu_threads = int(cpu_threads_raw or 0)
    if cpu_threads > 0:
        torch.set_num_threads(cpu_threads)
        torch.set_num_interop_threads(max(1, cpu_threads // 2))

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32",
        pretrained="openai",
        cache_dir=cache_dir,
    )
    model.eval()
    model.to(_device)
    _model = model
    _preprocess = preprocess
    _tokenizer = open_clip.get_tokenizer("ViT-B-32")


def _embed_image_bytes_sync(raw: bytes) -> List[float]:
    _load_model()
    import torch
    from PIL import Image
    import io

    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image_tensor = _preprocess(image).unsqueeze(0)
    with torch.no_grad():
        image_features = _model.encode_image(image_tensor)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features[0].cpu().tolist()


async def embed_image_bytes(raw: bytes) -> List[float]:
    """Embed image bytes using CLIP (open_clip).

    Args:
        raw: Image bytes.

    Returns:
        List[float]: Embedding vector.
    """
    return await asyncio.to_thread(_embed_image_bytes_sync, raw)
