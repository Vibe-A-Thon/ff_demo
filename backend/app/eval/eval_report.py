"""Evaluation report helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def build_eval_report_json(results: List[Dict[str, Any]], thresholds: Dict[str, float]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item.get("pass"))
    schema_valid = sum(1 for item in results if item.get("schema_valid"))
    tool_valid = sum(1 for item in results if item.get("tool_valid"))

    schema_rate = schema_valid / total if total else 0.0
    tool_rate = tool_valid / total if total else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "schema_valid_rate": schema_rate,
        "tool_call_accuracy": tool_rate,
        "thresholds": thresholds,
        "results": results,
    }


def build_eval_report_md(summary: Dict[str, Any]) -> str:
    lines = [
        "# Fraud Forge Eval Report",
        "",
        f"Generated: {summary.get('generated_at')}",
        "",
        f"Total tests: {summary.get('total')}",
        f"Passed: {summary.get('passed')}",
        f"Failed: {summary.get('failed')}",
        "",
        f"Schema validity rate: {summary.get('schema_valid_rate'):.2%}",
        f"Tool call accuracy: {summary.get('tool_call_accuracy'):.2%}",
        "",
        "## Results",
    ]
    for item in summary.get("results", []):
        status = "PASS" if item.get("pass") else "FAIL"
        lines.append(f"- {item.get('id')} — {status} — schema={item.get('schema_valid')} tool={item.get('tool_valid')}")
    return "\n".join(lines)
