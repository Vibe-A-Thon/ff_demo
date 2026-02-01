"""Schema validation and repair helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import json
from jsonschema import validate, ValidationError
from pydantic import BaseModel


def _schema_from_response_schema(response_schema: Any) -> Optional[Dict[str, Any]]:
    if response_schema is None:
        return None
    if isinstance(response_schema, dict):
        return response_schema
    if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
        return response_schema.model_json_schema()
    if isinstance(response_schema, BaseModel):
        return response_schema.model_json_schema()
    return None


def validate_json_payload(content: str, response_schema: Any) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    schema = _schema_from_response_schema(response_schema)
    if not schema:
        return True, None, None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return False, None, f"Invalid JSON: {exc.msg}"
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        return False, payload, f"Schema validation failed: {exc.message}"
    return True, payload, None
