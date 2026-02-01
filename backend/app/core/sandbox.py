"""
Rule code sandbox execution helpers.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Dict

SAFE_BUILTINS = MappingProxyType({
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "abs": abs,
    "sorted": sorted,
    "round": round,
})


def execute_rule(code: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute rule code in a constrained sandbox.

    Args:
        code: Python code defining a `run_rule(inputs)` function.
        inputs: Input payload for the rule.

    Returns:
        Rule execution output dictionary.

    Raises:
        ValueError: When the code does not define a runnable rule.
        RuntimeError: When execution fails.
    """
    globals_dict = {"__builtins__": SAFE_BUILTINS}
    locals_dict: Dict[str, Any] = {}
    try:
        exec(code, globals_dict, locals_dict)
    except Exception as exc:
        raise RuntimeError("Rule compilation failed") from exc

    rule_func = locals_dict.get("run_rule")
    if not callable(rule_func):
        raise ValueError("Rule code must define run_rule(inputs)")

    try:
        result = rule_func(inputs)
    except Exception as exc:
        raise RuntimeError("Rule execution failed") from exc

    if not isinstance(result, dict):
        raise ValueError("Rule output must be a dict")
    return result
