
import os
import shutil
import subprocess
import tempfile
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class SandboxRunner:
    def __init__(self, timeout_sec: int = 30):
        self.timeout = timeout_sec

    def _setup_workspace(self, rsb_content: bytes) -> str:
        tmp_dir = Path(tempfile.gettempdir()) / f"rsb_sandbox_{uuid.uuid4()}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # Write zip
        zip_path = tmp_dir / "package.rsb"
        zip_path.write_bytes(rsb_content)
        
        # Extract
        shutil.unpack_archive(str(zip_path), str(tmp_dir), "zip")
        return str(tmp_dir)

    def run_tests(self, rsb_content: bytes) -> Dict[str, Any]:
        """Run tests found in the RSB package within a subprocess."""
        workspace = self._setup_workspace(rsb_content)
        workspace_path = Path(workspace)
        
        results = {
            "passed": False,
            "unit_tests": {"passed": 0, "failed": 0, "total": 0, "output": ""},
            "integration_tests": {"passed": 0, "failed": 0, "total": 0},
            "error": None
        }

        try:
            # Install requirements if any? (Skip for now, assume stdlib + app env)
            
            # Locate tests
            tests_dir = workspace_path / "tests"
            if not tests_dir.exists():
                results["error"] = "No tests directory found"
                return results

            # Run Pytest
            # We assume pytest is installed in the current environment
            cmd = ["pytest", str(tests_dir), "--json-report", "--json-report-file=report.json"]
            
            # Run
            # Note: Running in same env is risky in prod, but OK for hackathon demo if we trust content or rely on OS limits
            # Ideally this runs in `docker run ...`
            
            process = subprocess.run(
                cmd, 
                cwd=workspace, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            
            report_path = workspace_path / "report.json"
            if report_path.exists():
                report = json.loads(report_path.read_text())
                summary = report.get("summary", {})
                results["unit_tests"]["passed"] = summary.get("passed", 0)
                results["unit_tests"]["failed"] = summary.get("failed", 0)
                results["unit_tests"]["total"] = summary.get("total", 0)
                results["unit_tests"]["output"] = process.stdout
                results["passed"] = (results["unit_tests"]["failed"] == 0 and results["unit_tests"]["total"] > 0)
            else:
                results["unit_tests"]["output"] = process.stdout + "\n" + process.stderr
                results["error"] = "Pytest did not generate a report (possibly syntax error or missing deps)"

        except subprocess.TimeoutExpired:
            results["error"] = "Test execution timed out"
        except Exception as e:
            logger.exception("Sandbox execution failed")
            results["error"] = str(e)
        finally:
            # Cleanup
            try:
                shutil.rmtree(workspace)
            except Exception:
                pass

        return results
