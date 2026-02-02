"""Rule Code Generator Service.

Converts RuleSpec artifacts into production-ready Python code.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import re
import hashlib


class RuleCodeGenerator:
    """Generates Python code from RuleSpec artifacts."""

    def __init__(self):
        """Initialize the code generator."""
        self.templates = {
            "velocity": self._generate_velocity_rule,
            "threshold": self._generate_threshold_rule,
            "pattern": self._generate_pattern_rule,
            "composite": self._generate_composite_rule,
        }

    def generate_code(self, rulespec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Python code from a RuleSpec.

        Args:
            rulespec: RuleSpec artifact containing rule definition.

        Returns:
            Dict containing generated code, metadata, and validation info.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        rule_type = rulespec.get("type", "threshold")
        title = rulespec.get("title", "Generated Rule")
        
        # Select appropriate template
        generator_func = self.templates.get(rule_type, self._generate_threshold_rule)
        
        # Generate code
        code = generator_func(rulespec)
        
        # Add metadata and wrapper
        full_code = self._wrap_with_metadata(code, rulespec)
        
        # Compute hash for integrity
        code_hash = hashlib.sha256(full_code.encode()).hexdigest()
        
        return {
            "rule_id": rule_id,
            "code": full_code,
            "hash": code_hash,
            "language": "python",
            "framework": "fastapi",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "title": title,
                "type": rule_type,
                "confidence": rulespec.get("confidence", 0.85),
            },
        }

    def _wrap_with_metadata(self, code: str, rulespec: Dict[str, Any]) -> str:
        """Wrap generated code with metadata and documentation.

        Args:
            code: Generated rule code.
            rulespec: Original RuleSpec.

        Returns:
            Wrapped code with docstrings and metadata.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        title = rulespec.get("title", "Generated Rule")
        generated_at = datetime.now(timezone.utc).isoformat()
        
        wrapper = f'''"""
Auto-generated fraud detection rule.

Rule ID: {rule_id}
Title: {title}
Generated: {generated_at}
Source: Purple Team RuleSpec
Framework: Fraud Forge Green Team Code Generator

⚠️  DO NOT EDIT MANUALLY - This file is auto-generated from RuleSpec artifacts.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


# ============================================================================
# RULE IMPLEMENTATION
# ============================================================================

{code}


# ============================================================================
# RULE METADATA
# ============================================================================

RULE_METADATA = {{
    "rule_id": "{rule_id}",
    "title": "{title}",
    "generated_at": "{generated_at}",
    "source": "rulespec",
    "version": "1.0",
}}
'''
        return wrapper

    def _generate_velocity_rule(self, rulespec: Dict[str, Any]) -> str:
        """Generate velocity-based rule code.

        Args:
            rulespec: RuleSpec with velocity parameters.

        Returns:
            Generated Python code.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        threshold = rulespec.get("threshold", 10)
        window_minutes = rulespec.get("window_minutes", 5)
        
        code = f'''
def evaluate_{self._sanitize_name(rule_id)}(transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate velocity-based fraud rule.
    
    Args:
        transaction: Transaction data.
        context: Historical context including recent transactions.
    
    Returns:
        Rule evaluation result with risk score and triggers.
    """
    user_id = transaction.get("user_id")
    amount = transaction.get("amount", 0)
    timestamp = transaction.get("timestamp")
    
    # Get recent transactions from context
    recent_txns = context.get("recent_transactions", [])
    
    # Calculate velocity within time window
    window_seconds = {window_minutes} * 60
    count_in_window = 0
    total_amount = 0
    
    for txn in recent_txns:
        if txn.get("user_id") == user_id:
            # Check if within time window (simplified)
            count_in_window += 1
            total_amount += txn.get("amount", 0)
    
    # Evaluate threshold
    triggered = count_in_window >= {threshold}
    risk_score = min(1.0, count_in_window / {threshold})
    
    return {{
        "rule_id": "{rule_id}",
        "triggered": triggered,
        "risk_score": risk_score,
        "details": {{
            "transaction_count": count_in_window,
            "total_amount": total_amount,
            "threshold": {threshold},
            "window_minutes": {window_minutes},
        }},
        "recommended_action": "block" if triggered else "allow",
    }}
'''
        return code

    def _generate_threshold_rule(self, rulespec: Dict[str, Any]) -> str:
        """Generate threshold-based rule code.

        Args:
            rulespec: RuleSpec with threshold parameters.

        Returns:
            Generated Python code.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        field = rulespec.get("field", "amount")
        threshold = rulespec.get("threshold", 1000)
        operator = rulespec.get("operator", "greater_than")
        
        # Map operator to Python comparison
        op_map = {
            "greater_than": ">",
            "less_than": "<",
            "equals": "==",
            "not_equals": "!=",
        }
        py_operator = op_map.get(operator, ">")
        
        code = f'''
def evaluate_{self._sanitize_name(rule_id)}(transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate threshold-based fraud rule.
    
    Args:
        transaction: Transaction data.
        context: Additional context.
    
    Returns:
        Rule evaluation result with risk score and triggers.
    """
    value = transaction.get("{field}", 0)
    threshold = {threshold}
    
    # Evaluate condition
    triggered = value {py_operator} threshold
    
    # Calculate risk score based on deviation
    if triggered:
        deviation = abs(value - threshold) / max(threshold, 1)
        risk_score = min(1.0, 0.5 + (deviation * 0.5))
    else:
        risk_score = 0.1
    
    return {{
        "rule_id": "{rule_id}",
        "triggered": triggered,
        "risk_score": risk_score,
        "details": {{
            "field": "{field}",
            "value": value,
            "threshold": threshold,
            "operator": "{operator}",
        }},
        "recommended_action": "review" if triggered else "allow",
    }}
'''
        return code

    def _generate_pattern_rule(self, rulespec: Dict[str, Any]) -> str:
        """Generate pattern-matching rule code.

        Args:
            rulespec: RuleSpec with pattern parameters.

        Returns:
            Generated Python code.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        patterns = rulespec.get("patterns", [])
        
        code = f'''
def evaluate_{self._sanitize_name(rule_id)}(transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate pattern-matching fraud rule.
    
    Args:
        transaction: Transaction data.
        context: Additional context.
    
    Returns:
        Rule evaluation result with risk score and triggers.
    """
    import re
    
    patterns = {patterns}
    matched_patterns = []
    
    # Check each pattern
    for pattern_def in patterns:
        field = pattern_def.get("field", "description")
        pattern = pattern_def.get("pattern", ".*")
        
        value = str(transaction.get(field, ""))
        if re.search(pattern, value, re.IGNORECASE):
            matched_patterns.append(pattern_def)
    
    triggered = len(matched_patterns) > 0
    risk_score = min(1.0, len(matched_patterns) * 0.3)
    
    return {{
        "rule_id": "{rule_id}",
        "triggered": triggered,
        "risk_score": risk_score,
        "details": {{
            "matched_patterns": matched_patterns,
            "total_patterns": len(patterns),
        }},
        "recommended_action": "block" if triggered else "allow",
    }}
'''
        return code

    def _generate_composite_rule(self, rulespec: Dict[str, Any]) -> str:
        """Generate composite rule combining multiple conditions.

        Args:
            rulespec: RuleSpec with composite conditions.

        Returns:
            Generated Python code.
        """
        rule_id = rulespec.get("rule_id", "unknown")
        conditions = rulespec.get("conditions", [])
        logic = rulespec.get("logic", "AND")  # AND or OR
        
        code = f'''
def evaluate_{self._sanitize_name(rule_id)}(transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate composite fraud rule.
    
    Args:
        transaction: Transaction data.
        context: Additional context.
    
    Returns:
        Rule evaluation result with risk score and triggers.
    """
    conditions = {conditions}
    results = []
    
    # Evaluate each condition
    for condition in conditions:
        field = condition.get("field")
        operator = condition.get("operator")
        value_threshold = condition.get("value")
        
        actual_value = transaction.get(field, 0)
        
        # Simple evaluation
        if operator == "greater_than":
            condition_met = actual_value > value_threshold
        elif operator == "less_than":
            condition_met = actual_value < value_threshold
        elif operator == "equals":
            condition_met = actual_value == value_threshold
        else:
            condition_met = False
        
        results.append(condition_met)
    
    # Apply logic
    logic = "{logic}"
    if logic == "AND":
        triggered = all(results)
    else:  # OR
        triggered = any(results)
    
    risk_score = sum(results) / max(len(results), 1)
    
    return {{
        "rule_id": "{rule_id}",
        "triggered": triggered,
        "risk_score": risk_score,
        "details": {{
            "conditions_evaluated": len(conditions),
            "conditions_met": sum(results),
            "logic": logic,
        }},
        "recommended_action": "block" if triggered else "allow",
    }}
'''
        return code

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in Python function names.

        Args:
            name: Original name.

        Returns:
            Sanitized name safe for Python identifiers.
        """
        # Remove non-alphanumeric characters and replace with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Ensure it doesn't start with a digit
        if sanitized and sanitized[0].isdigit():
            sanitized = f"rule_{sanitized}"
        return sanitized.lower()

    def validate_generated_code(self, code: str) -> Dict[str, Any]:
        """Validate generated code for syntax and security.

        Args:
            code: Generated Python code.

        Returns:
            Validation result with errors and warnings.
        """
        errors = []
        warnings = []
        
        # Syntax validation
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        
        # Security checks
        dangerous_patterns = [
            (r'\beval\(', "Use of eval() is prohibited"),
            (r'\bexec\(', "Use of exec() is prohibited"),
            (r'\b__import__\(', "Dynamic imports are restricted"),
            (r'\bopen\(', "File operations should be avoided"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                errors.append(message)
        
        # Best practice warnings
        if "# type: ignore" in code:
            warnings.append("Type ignore comments detected")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Singleton instance
rule_code_generator = RuleCodeGenerator()
