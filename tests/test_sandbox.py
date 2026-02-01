import pytest
from app.core.sandbox import execute_rule


def test_execute_rule_success():
    code = """

def run_rule(inputs):
    return {"score": inputs["value"] * 2}
"""
    result = execute_rule(code, {"value": 4})
    assert result == {"score": 8}


def test_execute_rule_missing_function():
    code = """

def noop():
    return {}
"""
    with pytest.raises(ValueError):
        execute_rule(code, {})


def test_execute_rule_invalid_output():
    code = """

def run_rule(inputs):
    return [1, 2]
"""
    with pytest.raises(ValueError):
        execute_rule(code, {})
