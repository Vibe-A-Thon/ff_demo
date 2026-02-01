"""Multimodal ingestion helpers for RAG (PDF/Image OCR)."""

from __future__ import annotations

import io
from typing import Any, Dict, Tuple

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OCRUnavailableError(RuntimeError):
    """Raised when OCR dependencies are missing."""


def _extract_text_from_pdf(raw: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
    except Exception as exc:  # pragma: no cover - import failure
        raise OCRUnavailableError("PyPDF2 is not installed") from exc

    reader = PdfReader(io.BytesIO(raw))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_text_from_image(raw: bytes) -> str:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise OCRUnavailableError("Pillow is not installed") from exc
    try:
        import pytesseract
    except Exception as exc:  # pragma: no cover
        raise OCRUnavailableError("pytesseract is not installed") from exc

    image = Image.open(io.BytesIO(raw))
    return pytesseract.image_to_string(image).strip()


def extract_text_from_upload(filename: str, content_type: str, raw: bytes) -> Tuple[str, Dict[str, Any]]:
    """Extract text from a PDF or image upload.

    Args:
        filename: Original filename.
        content_type: MIME type.
        raw: File bytes.

    Returns:
        Tuple[str, Dict[str, Any]]: Extracted text and metadata.

    Raises:
        OCRUnavailableError: If required OCR libs are missing.
        ValueError: If file type is unsupported.
    """
    meta = {"filename": filename, "content_type": content_type}
    if content_type in {"application/pdf"} or filename.lower().endswith(".pdf"):
        text = _extract_text_from_pdf(raw)
        meta["source"] = "pdf"
        return text, meta
    if content_type.startswith("image/") or filename.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        text = _extract_text_from_image(raw)
        meta["source"] = "image"
        return text, meta
    raise ValueError("Unsupported file type")
