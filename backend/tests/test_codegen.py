"""Tests for RuleSpec to Code Pipeline.

Tests code generation, validation, and deployment functionality.
"""

import pytest
from app.services.codegen.rule_code_generator import RuleCodeGenerator
from app.services.codegen.code_deployment_service import CodeDeploymentService


@pytest.fixture
def code_generator():
    """Fixture for code generator."""
    return RuleCodeGenerator()


@pytest.fixture
def deployment_service():
    """Fixture for deployment service."""
    return CodeDeploymentService(deployment_dir="./tests/data/deployed_rules")


class TestRuleCodeGenerator:
    """Test rule code generation."""

    def test_generate_velocity_rule(self, code_generator):
        """Test velocity rule generation."""
        rulespec = {
            "rule_id": "velocity_test_001",
            "type": "velocity",
            "title": "High Velocity Transaction Rule",
            "threshold": 10,
            "window_minutes": 5,
            "confidence": 0.92,
        }
        
        result = code_generator.generate_code(rulespec)
        
        assert result["rule_id"] == "velocity_test_001"
        assert "def evaluate_velocity_test_001" in result["code"]
        assert result["language"] == "python"
        assert "hash" in result
        assert len(result["hash"]) == 64  # SHA-256

    def test_generate_threshold_rule(self, code_generator):
        """Test threshold rule generation."""
        rulespec = {
            "rule_id": "threshold_test_001",
            "type": "threshold",
            "title": "High Amount Threshold Rule",
            "field": "amount",
            "threshold": 10000,
            "operator": "greater_than",
            "confidence": 0.88,
        }
        
        result = code_generator.generate_code(rulespec)
        
        assert result["rule_id"] == "threshold_test_001"
        assert "def evaluate_threshold_test_001" in result["code"]
        assert "amount" in result["code"]
        assert "10000" in result["code"]

    def test_generate_pattern_rule(self, code_generator):
        """Test pattern matching rule generation."""
        rulespec = {
            "rule_id": "pattern_test_001",
            "type": "pattern",
            "title": "Suspicious Pattern Rule",
            "patterns": [
                {"field": "description", "pattern": "test.*fraud"},
                {"field": "merchant", "pattern": "suspicious.*"},
            ],
            "confidence": 0.85,
        }
        
        result = code_generator.generate_code(rulespec)
        
        assert result["rule_id"] == "pattern_test_001"
        assert "def evaluate_pattern_test_001" in result["code"]
        assert "re.search" in result["code"]

    def test_generate_composite_rule(self, code_generator):
        """Test composite rule generation."""
        rulespec = {
            "rule_id": "composite_test_001",
            "type": "composite",
            "title": "Composite Fraud Rule",
            "conditions": [
                {"field": "amount", "operator": "greater_than", "value": 5000},
                {"field": "risk_score", "operator": "greater_than", "value": 0.7},
            ],
            "logic": "AND",
            "confidence": 0.90,
        }
        
        result = code_generator.generate_code(rulespec)
        
        assert result["rule_id"] == "composite_test_001"
        assert "def evaluate_composite_test_001" in result["code"]
        assert "all(results)" in result["code"]

    def test_validate_generated_code_valid(self, code_generator):
        """Test code validation for valid code."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {
        "triggered": False,
        "risk_score": 0.1,
    }
'''
        
        validation = code_generator.validate_generated_code(code)
        
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_generated_code_syntax_error(self, code_generator):
        """Test code validation detects syntax errors."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {
        "triggered": False
        "risk_score": 0.1,  # Missing comma
    }
'''
        
        validation = code_generator.validate_generated_code(code)
        
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0

    def test_validate_generated_code_security_eval(self, code_generator):
        """Test code validation detects eval() usage."""
        code = '''
def evaluate_test_rule(transaction, context):
    result = eval("1 + 1")  # Dangerous!
    return {"triggered": False}
'''
        
        validation = code_generator.validate_generated_code(code)
        
        assert validation["valid"] is False
        assert any("eval()" in err for err in validation["errors"])

    def test_sanitize_name(self, code_generator):
        """Test name sanitization."""
        assert code_generator._sanitize_name("test-rule-001") == "test_rule_001"
        assert code_generator._sanitize_name("123rule") == "rule_123rule"
        assert code_generator._sanitize_name("RuleWith@Special#Chars") == "rulewith_special_chars"


class TestCodeDeploymentService:
    """Test code deployment service."""

    def test_deploy_code_sandbox(self, deployment_service):
        """Test deploying code to sandbox."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {"triggered": False, "risk_score": 0.1}
'''
        
        result = deployment_service.deploy_code(
            rule_id="test_rule_001",
            code=code,
            metadata={"title": "Test Rule"},
            mode="sandbox",
        )
        
        assert result["rule_id"] == "test_rule_001"
        assert result["mode"] == "sandbox"
        assert result["status"] == "deployed"
        assert "file_path" in result
        assert "hash" in result

    def test_validate_deployment(self, deployment_service):
        """Test deployment validation."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {"triggered": False}
'''
        
        # Deploy first
        deployment_service.deploy_code(
            rule_id="test_rule_002",
            code=code,
            metadata={},
            mode="sandbox",
        )
        
        # Validate
        validation = deployment_service.validate_deployment("test_rule_002")
        
        assert validation["valid"] is True

    def test_list_deployed_rules(self, deployment_service):
        """Test listing deployed rules."""
        # Deploy multiple rules
        for i in range(3):
            deployment_service.deploy_code(
                rule_id=f"test_rule_list_{i}",
                code=f"def evaluate_rule_{i}(): pass",
                metadata={},
                mode="sandbox",
            )
        
        deployments = deployment_service.list_deployed_rules()
        
        assert len(deployments) >= 3

    def test_promote_deployment(self, deployment_service):
        """Test promoting deployment from sandbox to staging."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {"triggered": False}
'''
        
        # Deploy to sandbox
        deployment_service.deploy_code(
            rule_id="test_rule_promote",
            code=code,
            metadata={},
            mode="sandbox",
        )
        
        # Promote to staging
        result = deployment_service.promote_deployment(
            rule_id="test_rule_promote",
            from_mode="sandbox",
            to_mode="staging",
        )
        
        assert result["success"] is True
        assert result["promoted_from"] == "sandbox"
        assert result["promoted_to"] == "staging"

    def test_rollback_deployment(self, deployment_service):
        """Test rolling back deployment."""
        code = '''
def evaluate_test_rule(transaction, context):
    return {"triggered": False}
'''
        
        # Deploy first
        deployment_service.deploy_code(
            rule_id="test_rule_rollback",
            code=code,
            metadata={},
            mode="sandbox",
        )
        
        # Rollback
        result = deployment_service.rollback_deployment("test_rule_rollback")
        
        assert result["success"] is True
        assert result["rule_id"] == "test_rule_rollback"


class TestEndToEndPipeline:
    """Test end-to-end RuleSpec to Code pipeline."""

    def test_full_pipeline_flow(self, code_generator, deployment_service):
        """Test complete flow from RuleSpec to deployment."""
        # Step 1: Define RuleSpec
        rulespec = {
            "rule_id": "e2e_test_rule",
            "type": "threshold",
            "title": "End-to-End Test Rule",
            "field": "amount",
            "threshold": 1000,
            "operator": "greater_than",
            "confidence": 0.95,
        }
        
        # Step 2: Generate code
        generated = code_generator.generate_code(rulespec)
        assert generated["rule_id"] == "e2e_test_rule"
        
        # Step 3: Validate code
        validation = code_generator.validate_generated_code(generated["code"])
        assert validation["valid"] is True
        
        # Step 4: Deploy to sandbox
        deployment = deployment_service.deploy_code(
            rule_id=generated["rule_id"],
            code=generated["code"],
            metadata=generated["metadata"],
            mode="sandbox",
        )
        assert deployment["status"] == "deployed"
        
        # Step 5: Validate deployment
        deployment_validation = deployment_service.validate_deployment(generated["rule_id"])
        assert deployment_validation["valid"] is True
        
        # Step 6: Promote to staging
        promotion = deployment_service.promote_deployment(
            rule_id=generated["rule_id"],
            from_mode="sandbox",
            to_mode="staging",
        )
        assert promotion["success"] is True
