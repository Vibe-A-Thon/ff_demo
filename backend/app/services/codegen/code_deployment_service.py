"""Code deployment service.

Manages deployment of generated rule code to the runtime environment.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import os
import hashlib
from pathlib import Path


class CodeDeploymentService:
    """Handles deployment of generated code to production environment."""

    def __init__(self, deployment_dir: str = "./backend/data/deployed_rules"):
        """Initialize deployment service.

        Args:
            deployment_dir: Directory where deployed rules are stored.
        """
        self.deployment_dir = Path(deployment_dir)
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
        
        # Registry of deployed rules
        self.deployed_rules: Dict[str, Dict[str, Any]] = {}

    def deploy_code(
        self,
        rule_id: str,
        code: str,
        metadata: Dict[str, Any],
        mode: str = "sandbox"
    ) -> Dict[str, Any]:
        """Deploy generated code to the environment.

        Args:
            rule_id: Unique rule identifier.
            code: Generated Python code.
            metadata: Rule metadata.
            mode: Deployment mode ('sandbox', 'staging', 'production').

        Returns:
            Deployment result with status and location.
        """
        # Sanitize rule ID for filename
        safe_rule_id = rule_id.replace("/", "_").replace("\\", "_")
        
        # Determine deployment path
        mode_dir = self.deployment_dir / mode
        mode_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = mode_dir / f"{safe_rule_id}.py"
        
        # Write code to file
        file_path.write_text(code, encoding="utf-8")
        
        # Compute file hash
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Register deployment
        deployment_record = {
            "rule_id": rule_id,
            "file_path": str(file_path),
            "mode": mode,
            "hash": code_hash,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
            "status": "deployed",
        }
        
        self.deployed_rules[rule_id] = deployment_record
        
        return deployment_record

    def validate_deployment(self, rule_id: str) -> Dict[str, Any]:
        """Validate a deployed rule.

        Args:
            rule_id: Rule identifier.

        Returns:
            Validation result.
        """
        if rule_id not in self.deployed_rules:
            return {
                "valid": False,
                "error": "Rule not found in deployment registry",
            }
        
        record = self.deployed_rules[rule_id]
        file_path = Path(record["file_path"])
        
        # Check file exists
        if not file_path.exists():
            return {
                "valid": False,
                "error": f"Deployed file not found: {file_path}",
            }
        
        # Verify hash
        current_content = file_path.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        
        if current_hash != record["hash"]:
            return {
                "valid": False,
                "error": "File hash mismatch - file may have been tampered with",
            }
        
        return {
            "valid": True,
            "file_path": str(file_path),
            "hash": current_hash,
        }

    def rollback_deployment(self, rule_id: str) -> Dict[str, Any]:
        """Rollback a deployed rule.

        Args:
            rule_id: Rule identifier.

        Returns:
            Rollback result.
        """
        if rule_id not in self.deployed_rules:
            return {
                "success": False,
                "error": "Rule not found in deployment registry",
            }
        
        record = self.deployed_rules[rule_id]
        file_path = Path(record["file_path"])
        
        # Remove deployed file
        if file_path.exists():
            file_path.unlink()
        
        # Update registry
        record["status"] = "rolled_back"
        record["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Rule deployment rolled back successfully",
        }

    def list_deployed_rules(self, mode: str = None) -> List[Dict[str, Any]]:
        """List deployed rules.

        Args:
            mode: Optional mode filter ('sandbox', 'staging', 'production').

        Returns:
            List of deployed rule records.
        """
        rules = list(self.deployed_rules.values())
        
        if mode:
            rules = [r for r in rules if r.get("mode") == mode]
        
        return rules

    def promote_deployment(self, rule_id: str, from_mode: str, to_mode: str) -> Dict[str, Any]:
        """Promote a rule from one deployment mode to another.

        Args:
            rule_id: Rule identifier.
            from_mode: Source deployment mode.
            to_mode: Target deployment mode.

        Returns:
            Promotion result.
        """
        if rule_id not in self.deployed_rules:
            return {
                "success": False,
                "error": "Rule not found in deployment registry",
            }
        
        record = self.deployed_rules[rule_id]
        
        if record["mode"] != from_mode:
            return {
                "success": False,
                "error": f"Rule is not in {from_mode} mode",
            }
        
        # Read current code
        current_path = Path(record["file_path"])
        if not current_path.exists():
            return {
                "success": False,
                "error": "Source file not found",
            }
        
        code = current_path.read_text(encoding="utf-8")
        
        # Deploy to new mode
        new_deployment = self.deploy_code(
            rule_id=rule_id,
            code=code,
            metadata=record["metadata"],
            mode=to_mode,
        )
        
        return {
            "success": True,
            "rule_id": rule_id,
            "promoted_from": from_mode,
            "promoted_to": to_mode,
            "new_path": new_deployment["file_path"],
        }


# Singleton instance
code_deployment_service = CodeDeploymentService()
