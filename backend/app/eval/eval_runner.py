"""Evaluation harness runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import yaml

from app.config import ROOT_DIR
from app.llm.service import LLMService
from app.llm.schema_guard import validate_json_payload
from app.llm.tool_registry import load_tool_registry, validate_tool_call
from app.llm.normalizers.tool_calls import normalize_inbound_tool_calls
from app.llm.schemas import Plan, ToolCallList, Finding, RuleSpecProposal, LLMFailure
from app.models import Decision, ExplanationBundle
from app.eval.eval_report import build_eval_report_json, build_eval_report_md

SCHEMA_MAP = {
    "Plan": Plan,
    "ToolCallList": ToolCallList,
    "Finding": Finding,
    "Decision": Decision,
    "ExplanationBundle": ExplanationBundle,
    "RuleSpecProposal": RuleSpecProposal,
    "LLMFailure": LLMFailure,
}


@dataclass
class EvalTest:
    test_id: str
    description: str
    expected_schema: Optional[str] = None
    prompt: Optional[str] = None
    team_id: Optional[str] = None
    agent_id: Optional[str] = None
    model_id: Optional[str] = None


def _default_eval_path() -> Path:
    return ROOT_DIR / "llm" / "configs" / "eval_suite.yaml"


def _load_tests(path: Optional[Path] = None) -> tuple[List[EvalTest], Dict[str, float]]:
    suite_path = path or _default_eval_path()
    if not suite_path.exists():
        return [], {}
    with suite_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    tests = []
    for entry in payload.get("tests", []) or []:
        tests.append(
            EvalTest(
                test_id=entry.get("id", "unknown"),
                description=entry.get("description", ""),
                expected_schema=entry.get("expected_schema"),
                prompt=entry.get("prompt"),
                team_id=entry.get("team_id"),
                agent_id=entry.get("agent_id"),
                model_id=entry.get("model"),
            )
        )
    return tests, payload.get("thresholds", {}) or {}


def _resolve_schema(name: Optional[str]) -> Any:
    if not name:
        return None
    return SCHEMA_MAP.get(name)


def _default_prompt(schema_name: Optional[str]) -> str:
    if schema_name == "ToolCallList":
        return "Return a JSON object with a calls array that includes one tool call for retrieve_context with query 'fraud check'."
    if schema_name == "Plan":
        return "Return a JSON plan with title and three steps for investigating a fraud alert."
    if schema_name == "Finding":
        return "Return a JSON finding with category 'velocity' and summary for a fraud check."
    if schema_name == "Decision":
        return "Return a JSON decision with decision_type 'block' and outcome 'approved'."
    if schema_name == "ExplanationBundle":
        return "Return a JSON explanation bundle with summary and details for a fraud alert."
    if schema_name == "RuleSpecProposal":
        return "Return a JSON rule spec proposal with title and one rule entry." 
    return "Return a short JSON object." 


async def run_eval_suite(path: Optional[Path] = None, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    tests, thresholds = _load_tests(path)
    service = LLMService()
    tool_registry = load_tool_registry()
    results: List[Dict[str, Any]] = []
    for test in tests:
        schema = _resolve_schema(test.expected_schema)
        prompt = test.prompt or _default_prompt(test.expected_schema)
        messages = [
            {"role": "system", "content": "Return only JSON. Do not include markdown."},
            {"role": "user", "content": prompt},
        ]
        response = await service.generate(
            messages=messages,
            max_tokens=600,
            response_schema=schema,
            requested_model=test.model_id,
            team_id=test.team_id,
            agent_id=test.agent_id,
            actor_id=test.agent_id or "eval",
        )
        schema_ok, payload, schema_error = validate_json_payload(response, schema)
        tool_ok = True
        if test.expected_schema == "ToolCallList" and payload:
            calls = payload.get("calls") or []
            normalized = normalize_inbound_tool_calls("openai", calls, requested_by=test.agent_id or "eval")
            for call in normalized:
                name = call.get("tool_name")
                args = call.get("arguments") or {}
                if not name or validate_tool_call(name, args, tool_registry):
                    tool_ok = False
                    break
        results.append(
            {
                "id": test.test_id,
                "description": test.description,
                "schema": test.expected_schema,
                "schema_valid": schema_ok,
                "schema_error": schema_error,
                "tool_valid": tool_ok,
                "pass": schema_ok and tool_ok,
            }
        )

    summary = build_eval_report_json(results, thresholds)
    out_dir = output_dir or (ROOT_DIR / "run_artifacts" / "eval")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "eval_report.json"
    md_path = out_dir / "eval_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(build_eval_report_md(summary), encoding="utf-8")
    return summary
