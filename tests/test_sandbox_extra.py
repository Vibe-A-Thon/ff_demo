import pytest

from app.core.sandbox import execute_rule


def test_execute_rule_blocks_imports():
    code = """

def run_rule(inputs):
    import os
    return {"cwd": os.getcwd()}
"""
    with pytest.raises(RuntimeError):
        execute_rule(code, {})


def test_execute_rule_blocks_open_builtin():
    code = """

def run_rule(inputs):
    handle = open('file.txt', 'w')
    return {"ok": True}
"""
    with pytest.raises(RuntimeError):
        execute_rule(code, {})


def test_execute_rule_safe_builtins_work():
    code = """

def run_rule(inputs):
    return {"total": sum(inputs["values"]), "top": max(inputs["values"])}
"""
    result = execute_rule(code, {"values": [1, 2, 3]})
    assert result["total"] == 6
    assert result["top"] == 3
