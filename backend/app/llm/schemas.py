"""Canonical LLM output schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Plan"
    steps: List[Dict[str, Any]] = []


class ToolCallList(BaseModel):
    calls: List[Dict[str, Any]] = []


class Finding(BaseModel):
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    summary: str
    evidence: List[Dict[str, Any]] = []


class RuleSpecProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    rules: List[Dict[str, Any]] = []


class LLMFailure(BaseModel):
    failure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str
    message: str
    provider: Optional[str] = None
    model_id: Optional[str] = None
    raw_output: Optional[str] = None
    trace_id: Optional[str] = None
