"""Agent orchestration utilities.

Defines agent behaviors and orchestrators for the war loop.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from app.models import AgentTrace, AgentTask, AgentResult, AgentProfile
from app.agent_registry import AgentRegistry
from app.tooling import TOOL_IMPLEMENTATIONS, derive_seed, rng
from app.config import get_integration_setting
from app.deps import get_llm_service
from app.rag_utils import contains_sensitive_identifiers

DEFAULT_REGISTRY = AgentRegistry.from_defaults()


def _get_llm_model() -> str:
    return get_integration_setting("llm", "model", "gpt-4o") or "gpt-4o"


def _seed_from_string(value: str) -> int:
    """Derive a deterministic seed from a string."""
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _seeded_timestamp(seed: int) -> str:
    """Generate a deterministic timestamp from a seed."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return (base + timedelta(seconds=seed % 100000)).isoformat()


def _stable_hash(payload: Dict[str, Any]) -> str:
    """Hash a payload deterministically."""
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _derive_task_seed(task: AgentTask, agent_id: str) -> int:
    """Derive a deterministic seed for a task/agent pair."""
    base = task.seed if task.seed is not None else _seed_from_string(f"{task.run_id}:{task.task_id}")
    return derive_seed(base, agent_id)


def _deterministic_task_id(
    run_id: str,
    team_id: str,
    agent_id: str,
    task_type: str,
    objective: str,
    seed: int | None,
    index: int,
) -> str:
    payload = f"{run_id}:{team_id}:{agent_id}:{task_type}:{objective}:{seed}:{index}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _build_trace_ids(task: AgentTask, agent_id: str) -> Dict[str, str]:
    trace_seed = _stable_hash({"run_id": task.run_id, "task_id": task.task_id, "agent_id": agent_id})
    trace_id = task.trace_id or trace_seed[:16]
    span_id = task.span_id or _stable_hash({"trace_id": trace_id, "agent_id": agent_id})[:16]
    parent_span_id = task.parent_span_id or _stable_hash({"trace_id": trace_id, "run_id": task.run_id})[:16]
    return {"trace_id": trace_id, "span_id": span_id, "parent_span_id": parent_span_id}


def _artifact_payload(artifact_type: str, seed: int, task: AgentTask, agent_id: str, team_id: str, llm_summary: str | None) -> Dict[str, Any]:
    randomizer = rng(seed)
    base = {
        "artifact_type": artifact_type,
        "summary": llm_summary or f"Synthetic {artifact_type} produced by {agent_id}.",
        "confidence": round(randomizer.uniform(0.72, 0.97), 2),
        "run_id": task.run_id,
        "task_id": task.task_id,
        "team_id": team_id,
        "agent_id": agent_id,
    }
    if artifact_type == "AttackCampaign":
        base.update({"campaign_id": f"CMP-{seed % 9999:04d}", "variants": ["velocity_spike", "identity_mismatch"]})
    elif artifact_type == "AttackPlaybook":
        base.update({"playbook_id": f"PB-{seed % 9999:04d}", "steps": ["recon", "execute", "exfiltrate"]})
    elif artifact_type == "SyntheticIdentityBundle":
        base.update({"bundle_id": f"ID-{seed % 9999:04d}", "identities": randomizer.randint(3, 9)})
    elif artifact_type == "SyntheticTransactionStream":
        base.update({"stream_id": f"TXS-{seed % 9999:04d}", "events": randomizer.randint(18, 42)})
    elif artifact_type == "ReconFindings":
        base.update({"signals": ["velocity_gap", "device_anomaly"], "severity": randomizer.choice(["low", "medium", "high"])})
    elif artifact_type == "AttackVariantReport":
        base.update({"variants_tested": randomizer.randint(2, 6), "success_rate": round(randomizer.uniform(0.4, 0.8), 2)})
    elif artifact_type == "AttackPlan":
        base.update({"plan_id": f"AP-{seed % 9999:04d}", "objective": task.params.get("objective", "simulate attack")})
    elif artifact_type == "RuleHits":
        base.update({"rules_triggered": randomizer.randint(2, 8), "top_rule": f"R-FF-{seed % 9999:04d}"})
    elif artifact_type == "BaselineDeviations":
        base.update({"deviations": randomizer.randint(1, 5), "baseline": "customer_velocity"})
    elif artifact_type == "GraphFindings":
        base.update({"clusters": randomizer.randint(1, 3), "ring_score": round(randomizer.uniform(0.3, 0.8), 2)})
    elif artifact_type == "DeviceSessionRisk":
        base.update({"risk_score": round(randomizer.uniform(0.4, 0.9), 2), "signals": ["proxy", "impossible_travel"]})
    elif artifact_type == "ModelScores":
        base.update({"avg_score": round(randomizer.uniform(0.35, 0.85), 2), "drift": round(randomizer.uniform(0.01, 0.12), 3)})
    elif artifact_type == "DecisionPackage":
        base.update({"decision": randomizer.choice(["allow", "review", "block"]), "confidence": round(randomizer.uniform(0.72, 0.96), 2)})
    elif artifact_type == "EscalationPack":
        base.update({"escalation_id": f"ESC-{seed % 9999:04d}", "priority": randomizer.choice(["P1", "P2", "P3"])})
    elif artifact_type == "OutcomeLabels":
        base.update({"labels": ["chargeback_pending", "under_review"], "lag_days": randomizer.randint(1, 7)})
    elif artifact_type == "FailureDiagnosis":
        base.update({"root_cause": "rule_gap", "confidence": round(randomizer.uniform(0.6, 0.9), 2)})
    elif artifact_type == "RuleSpec":
        base.update({"rule_id": f"R-FF-{seed % 9999:04d}", "action": "step_up_auth"})
    elif artifact_type == "ThreatForecast":
        base.update({"forecast_window_days": 30, "emerging_patterns": ["mule_network", "account_takeover"]})
    elif artifact_type == "PolicyConstraints":
        base.update({"constraints": ["fairness", "data_minimization"], "status": "reviewed"})
    elif artifact_type == "OntologyUpdate":
        base.update({"nodes_added": randomizer.randint(2, 6), "edges_added": randomizer.randint(3, 8)})
    elif artifact_type == "RequirementsPack":
        base.update({"requirements": ["add_velocity_rule", "extend_device_risk"], "priority": "high"})
    elif artifact_type == "CodePatch":
        base.update({"patch_id": f"PATCH-{seed % 9999:04d}", "files": ["rules/velocity_spike.py"]})
    elif artifact_type == "PipelineChange":
        base.update({"pipeline": "streaming_ingest", "change": "add_feature_enrichment"})
    elif artifact_type == "FeatureSignalSpec":
        base.update({"features": ["velocity_bucket", "device_risk"], "version": "v1"})
    elif artifact_type == "ObservabilityHooks":
        base.update({"metrics": ["latency", "false_positive_rate"], "logs": "enabled"})
    elif artifact_type == "PerformanceReport":
        base.update({"p95_latency_ms": randomizer.randint(120, 280), "throughput_rps": randomizer.randint(300, 900)})
    elif artifact_type == "ConfigBundle":
        base.update({"configs": ["risk_thresholds", "channel_weights"], "version": "2026.02"})
    elif artifact_type == "TestPlan":
        base.update({"tests": randomizer.randint(8, 16), "coverage_target": 0.9})
    elif artifact_type == "ReplayReport":
        base.update({"replays": randomizer.randint(2, 6), "regression_found": randomizer.choice([True, False])})
    elif artifact_type == "EdgeCaseSet":
        base.update({"cases": randomizer.randint(5, 12), "focus": "velocity_bursts"})
    elif artifact_type == "ChaosReport":
        base.update({"faults": randomizer.randint(2, 5), "resilience": round(randomizer.uniform(0.7, 0.95), 2)})
    elif artifact_type == "LoadTestReport":
        base.update({"max_rps": randomizer.randint(800, 2000), "error_rate": round(randomizer.uniform(0.01, 0.05), 3)})
    elif artifact_type == "CoverageReport":
        base.update({"coverage": round(randomizer.uniform(0.82, 0.97), 2), "gaps": randomizer.randint(0, 3)})
    elif artifact_type == "DefectReport":
        base.update({"defects": randomizer.randint(0, 4), "severity": randomizer.choice(["low", "medium"])})
    elif artifact_type == "CodeReviewReport":
        base.update({"review_status": "pending", "comments": randomizer.randint(1, 4)})
    elif artifact_type == "SecurityScanReport":
        base.update({"issues_found": randomizer.randint(0, 2), "status": "pending"})
    elif artifact_type == "EvidenceVerification":
        base.update({"evidence_complete": True, "notes": "Synthetic evidence verified."})
    elif artifact_type == "ReleaseRiskReport":
        base.update({"risk_level": randomizer.choice(["low", "medium", "high"]), "mitigations": 2})
    elif artifact_type == "RollbackVerification":
        base.update({"rollback_ready": True, "kill_switch": "verified"})
    elif artifact_type == "ReleaseDecision":
        base.update({"decision": randomizer.choice(["approve", "hold"]), "notes": "Pending governance."})
    elif artifact_type == "ExplanationPack":
        base.update({"summary": base["summary"], "details": "Synthetic explanation with evidence references."})
    elif artifact_type == "EvidenceTrace":
        base.update({"evidence_links": randomizer.randint(3, 7), "provenance": "run_trace"})
    elif artifact_type == "AudienceVariantSet":
        base.update({"audiences": ["ops", "customer", "regulator"], "variants": 3})
    elif artifact_type == "ExplanationQAReport":
        base.update({"coverage": round(randomizer.uniform(0.85, 0.98), 2), "flags": []})
    elif artifact_type == "CaseNarrative":
        base.update({"timeline_steps": randomizer.randint(4, 8), "tone": "executive"})
    elif artifact_type == "CompliancePack":
        base.update({"checks": ["pii_redaction", "audit_trace"], "status": "pending"})
    elif artifact_type == "RegulatoryMapping":
        base.update({"frameworks": ["PCI", "SOC2"], "status": "draft"})
    elif artifact_type == "ComplianceValidationReport":
        base.update({"validation": "pending", "issues": 0})
    elif artifact_type == "FairnessReport":
        base.update({"bias_score": round(randomizer.uniform(0.01, 0.08), 3), "status": "review"})
    elif artifact_type == "AuditIntegrityReport":
        base.update({"hash_chain": "ok", "gaps": 0})
    elif artifact_type == "GovernanceApproval":
        base.update({"approval": "pending", "approver_role": "council"})
    return base

class BaseAgent:
    """Base agent contract for planning and execution."""

    agent_id: str
    team_id: str
    role: str
    capabilities: List[str]
    inputs: List[str]
    outputs: List[str]
    operating_mode: str
    guardrails: List[str]
    allowed_tools: List[str]

    def __init__(self, agent_id: str, team_id: str, profile: AgentProfile | None = None):
        """Initialize a base agent.

        Args:
            agent_id: Agent identifier.
            team_id: Team identifier.
            profile: Optional agent profile.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        self.agent_id = agent_id
        self.team_id = team_id
        self.profile = profile
        self.role = profile.role if profile else "Agent"
        self.capabilities = profile.capabilities if profile else []
        self.inputs = profile.inputs if profile else []
        self.outputs = profile.outputs if profile else []
        self.operating_mode = profile.operating_mode if profile else "manual"
        self.guardrails = profile.guardrails if profile else ["synthetic_only"]
        self.allowed_tools = profile.allowed_tools if profile else []

    def get_contract(self) -> Dict[str, Any]:
        """Return agent contract metadata."""
        return {
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "operating_mode": self.operating_mode,
            "guardrails": self.guardrails,
            "allowed_tools": self.allowed_tools,
        }

    async def pre_execute(self, task: AgentTask, seed: int) -> None:
        """Hook executed before a task run."""
        return None

    async def post_execute(self, task: AgentTask, result: AgentResult) -> None:
        """Hook executed after a task run."""
        return None

    async def on_error(self, task: AgentTask, error: Exception) -> None:
        """Hook executed when a task run fails."""
        return None

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a plan for the agent.

        Args:
            context: Input context.

        Returns:
            List[Dict[str, Any]]: Planned steps.

        Raises:
            None: No explicit exceptions are raised.
        """
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute plan steps and return outputs.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Outputs by tool.

        Raises:
            None: No explicit exceptions are raised.
        """
        outputs: Dict[str, Any] = {}
        blocked_tools: List[str] = []
        for step in plan_steps:
            tool_name = step.get("tool")
            params = step.get("params", {})
            if self.allowed_tools and tool_name not in self.allowed_tools:
                blocked_tools.append(tool_name)
                continue
            impl = TOOL_IMPLEMENTATIONS.get(tool_name)
            if not impl:
                continue
            step_seed = derive_seed(seed, tool_name)
            outputs[tool_name] = impl(params, step_seed)
        if blocked_tools:
            outputs["blocked_tools"] = blocked_tools
        return outputs

    async def reflect(self, outputs: Dict[str, Any]) -> List[str]:
        """Reflect on outputs and produce notes.

        Args:
            outputs: Tool outputs.

        Returns:
            List[str]: Reflection notes.

        Raises:
            None: No explicit exceptions are raised.
        """
        return []

    async def validate_task(self, task: AgentTask) -> List[str]:
        """Validate a task before execution.

        Args:
            task: Task payload.

        Returns:
            List[str]: Validation issues.

        Raises:
            None: No explicit exceptions are raised.
        """
        issues: List[str] = []
        if task.team_id != self.team_id:
            issues.append("team_id mismatch")
        if not task.run_id:
            issues.append("missing run_id")
        if not task.task_type:
            issues.append("missing task_type")
        if task.target_agent_id and task.target_agent_id != self.agent_id:
            issues.append("target_agent_id mismatch")
        if self.inputs and not any(item.get("artifact_type") in self.inputs for item in task.inputs):
            issues.append("missing required inputs")
        if "synthetic_only" in self.guardrails and task.inputs:
            joined = json.dumps(task.inputs, default=str)
            if contains_sensitive_identifiers(joined):
                issues.append("synthetic-only guardrail violation")
        return issues

    async def explain_result(self, result: AgentResult) -> List[str]:
        """Provide a short explanation for a result.

        Args:
            result: Agent result.

        Returns:
            List[str]: Explanation notes.

        Raises:
            None: No explicit exceptions are raised.
        """
        if result.status != "success":
            return ["Task failed validation."]
        return ["Synthetic task executed with deterministic replay."]

    async def emit(self, context: Dict[str, Any], seed: int) -> AgentTrace:
        """Run plan, act, and reflect to produce a trace.

        Args:
            context: Input context.
            seed: Random seed.

        Returns:
            AgentTrace: Agent trace payload.

        Raises:
            None: No explicit exceptions are raised.
        """
        plan_steps = await self.plan(context)
        outputs = await self.act(plan_steps, seed)
        notes = await self.reflect(outputs)
        return AgentTrace(agent_id=self.agent_id, team_id=self.team_id, plan=plan_steps, outputs=outputs, notes=notes)

    async def run_task(self, task: AgentTask) -> AgentResult:
        """Run an agent task with deterministic outputs.

        Args:
            task: Agent task payload.

        Returns:
            AgentResult: Deterministic task result.

        Raises:
            None: No explicit exceptions are raised.
        """
        trace_info = _build_trace_ids(task, self.agent_id)
        validation_issues = await self.validate_task(task)
        if validation_issues:
            return AgentResult(
                status="failed",
                outputs=[],
                metrics={"validation_errors": validation_issues, **trace_info},
                decision_trace=["validation_failed"] + validation_issues,
                logs_ref=f"run_artifacts/{task.run_id}/agents/{self.agent_id}.jsonl",
                trace_id=trace_info["trace_id"],
            )

        seed = _derive_task_seed(task, self.agent_id)
        await self.pre_execute(task, seed)
            llm_service = get_llm_service()
            llm_summary: str | None = None
            try:
                prompt = (
                    "You are an AI agent in Fraud Forge. Summarize the task output in 1-2 sentences. "
                    "Keep it synthetic and defensive.\n"
                    f"Team: {task.team_id}. Task: {task.task_type}. Objective: {task.params.get('objective', 'N/A')}."
                )
                llm_summary = await llm_service.generate(
                    messages=[
                        {"role": "system", "content": "You are a defensive fraud simulation assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=120,
                    requested_model=_get_llm_model(),
                    team_id=task.team_id,
                    agent_id=self.agent_id,
                    actor_id=self.agent_id,
                    run_id=task.run_id,
                    trace_id=trace_info["trace_id"],
                )
                llm_summary = llm_summary.strip()
            except Exception:
                llm_summary = None
        try:
            plan_steps = await self.plan({"task": task.model_dump()})
            outputs = await self.act(plan_steps, seed)
            notes = await self.reflect(outputs)
        except Exception as exc:
            await self.on_error(task, exc)
            return AgentResult(
                status="failed",
                outputs=[],
                metrics={"error": str(exc), **trace_info},
                decision_trace=["execution_failed", str(exc)],
                logs_ref=f"run_artifacts/{task.run_id}/agents/{self.agent_id}.jsonl",
                trace_id=trace_info["trace_id"],
            )

        artifacts: List[Dict[str, Any]] = []
        decision_trace: List[str] = []
        artifact_types = outputs.get("artifact_types") if isinstance(outputs, dict) else None
        if not artifact_types:
            artifact_types = self.outputs or ["Artifact"]
        for index, artifact_type in enumerate(artifact_types, start=1):
            artifact_seed = derive_seed(seed, f"{artifact_type}:{index}")
            payload = _artifact_payload(artifact_type, artifact_seed, task, self.agent_id, self.team_id, llm_summary)
            artifact = {
                "artifact_id": f"{self.agent_id}:{artifact_type}:{artifact_seed % 100000}",
                "artifact_type": artifact_type,
                "schema_version": "1.0",
                "agent_id": self.agent_id,
                "team_id": self.team_id,
                "task_id": task.task_id,
                "run_id": task.run_id,
                "payload": payload,
                "lineage": {
                    "inputs": task.inputs,
                    "seed": artifact_seed,
                    "task_type": task.task_type,
                    "trace_id": trace_info["trace_id"],
                    "span_id": trace_info["span_id"],
                },
                "safety_flags": {"synthetic_only": True, "watermark": "Simulation/Training Only"},
                "hash": _stable_hash(payload),
                "created_at": _seeded_timestamp(artifact_seed),
                "trace_id": trace_info["trace_id"],
                "span_id": trace_info["span_id"],
            }
            artifacts.append(artifact)
            decision_trace.append(f"generated {artifact_type}")

        result = AgentResult(
            status="success",
            outputs=artifacts,
            metrics={
                "quality": round(rng(seed).uniform(0.72, 0.95), 2),
                "latency_ms": int(rng(seed).uniform(120, 680)),
                "seed": seed,
                "llm": bool(llm_summary),
                **trace_info,
            },
            decision_trace=decision_trace + notes,
            logs_ref=f"run_artifacts/{task.run_id}/agents/{self.agent_id}.jsonl",
            trace_id=trace_info["trace_id"],
        )
        result.decision_trace += await self.explain_result(result)
        await self.post_execute(task, result)
        return result


class SyntheticAgentRuntime(BaseAgent):
    """Runtime for synthetic sub-agents based on registry profiles."""

    def __init__(self, profile: AgentProfile):
        super().__init__(profile.agent_id, profile.team_id, profile)
        self.profile = profile

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        outputs = self.profile.outputs or ["Artifact"]
        return [{"tool": "synthetic", "params": {"artifact_type": artifact}} for artifact in outputs]

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        artifact_types = [step.get("params", {}).get("artifact_type") for step in plan_steps if step.get("params")]
        return {"artifact_types": [item for item in artifact_types if item]}


def build_agent_runtime_registry(registry: AgentRegistry | None = None) -> Dict[str, SyntheticAgentRuntime]:
    """Build runtime agents for every registered agent profile."""
    runtime_registry: Dict[str, SyntheticAgentRuntime] = {}
    registry = registry or DEFAULT_REGISTRY
    for profile in registry.list_agents():
        runtime_registry[profile.agent_id] = SyntheticAgentRuntime(profile)
    return runtime_registry


AGENT_RUNTIME_REGISTRY = build_agent_runtime_registry()


def get_agent_runtime(agent_id: str) -> SyntheticAgentRuntime | None:
    """Get runtime agent by id."""
    return AGENT_RUNTIME_REGISTRY.get(agent_id)


WAR_LOOP_TEAM_ORDER = ["red", "blue", "purple", "green", "black", "orange", "gold", "white"]


def _build_lineage_edges(inputs: List[Dict[str, Any]], outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    for output in outputs:
        for parent in inputs:
            edges.append(
                {
                    "source": parent.get("artifact_id"),
                    "target": output.get("artifact_id"),
                    "relation": "DERIVED_FROM",
                    "artifact_type": output.get("artifact_type"),
                }
            )
    return edges


class OrchestrationEngine:
    """Robust multi-team orchestration engine with lineage and approvals."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or DEFAULT_REGISTRY

    async def execute_team(
        self,
        run_id: str,
        team_id: str,
        objective: str,
        task_type: str,
        inputs: List[Dict[str, Any]],
        params: Dict[str, Any],
        max_agents: int,
        auto_execute: bool,
        seed: int | None,
    ) -> Dict[str, Any]:
        delegation = self.registry.build_delegation_plan(team_id, objective, max_agents=max_agents)
        tasks: List[AgentTask] = []
        executions: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        lineage: List[Dict[str, Any]] = []
        for index, delegate in enumerate(delegation, start=1):
            task_id = _deterministic_task_id(
                run_id,
                team_id,
                delegate["agent_id"],
                task_type,
                objective,
                seed,
                index,
            )
            created_at = _seeded_timestamp(derive_seed(seed or _seed_from_string(run_id), f"task:{task_id}"))
            task = AgentTask(
                task_id=task_id,
                run_id=run_id,
                team_id=team_id,
                target_agent_id=delegate["agent_id"],
                task_type=task_type,
                inputs=inputs,
                params={**params, "objective": objective},
                seed=seed,
                status="pending",
                created_by="system",
                created_at=created_at,
                updated_at=created_at,
            )
            tasks.append(task)
            runtime = get_agent_runtime(task.target_agent_id or "")
            if not auto_execute or not runtime:
                continue
            if runtime.operating_mode in {"manual", "hitl"}:
                task.status = "waiting_approval"
                task.updated_at = _seeded_timestamp(derive_seed(seed or _seed_from_string(run_id), f"task:update:{task_id}"))
                continue
            result = await runtime.run_task(task)
            task.status = result.status
            task.updated_at = datetime.now(timezone.utc).isoformat()
            executions.append({"task": task, "result": result})
            artifacts.extend(result.outputs)
            lineage.extend(_build_lineage_edges(inputs, result.outputs))

        return {
            "team_id": team_id,
            "objective": objective,
            "tasks": tasks,
            "executions": executions,
            "artifacts": artifacts,
            "lineage": lineage,
        }

    async def orchestrate(
        self,
        run_id: str,
        objective: str,
        teams: List[str],
        task_type: str,
        inputs: List[Dict[str, Any]],
        params: Dict[str, Any],
        max_agents_per_team: int,
        auto_execute: bool,
        seed: int | None,
    ) -> Dict[str, Any]:
        ordered = [team for team in WAR_LOOP_TEAM_ORDER if team in teams]
        ordered += [team for team in teams if team not in ordered]
        team_bundles: List[Dict[str, Any]] = []
        inherited_inputs = inputs
        all_tasks: List[AgentTask] = []
        all_results: List[AgentResult] = []
        all_artifacts: List[Dict[str, Any]] = []
        lineage: List[Dict[str, Any]] = []
        for team_id in ordered:
            bundle = await self.execute_team(
                run_id,
                team_id,
                objective,
                task_type,
                inherited_inputs,
                params,
                max_agents_per_team,
                auto_execute,
                seed,
            )
            team_bundles.append(bundle)
            all_tasks.extend(bundle["tasks"])
            all_artifacts.extend(bundle["artifacts"])
            lineage.extend(bundle["lineage"])
            for execution in bundle["executions"]:
                all_results.append(execution["result"])
            if auto_execute and bundle["artifacts"]:
                inherited_inputs = [
                    {"artifact_id": art.get("artifact_id"), "artifact_type": art.get("artifact_type")}
                    for art in bundle["artifacts"]
                ]

        return {
            "teams": team_bundles,
            "tasks": all_tasks,
            "results": all_results,
            "artifacts": all_artifacts,
            "lineage": lineage,
        }


ORCHESTRATION_ENGINE = OrchestrationEngine()


async def orchestrate_multi_team_tasks(
    run_id: str,
    objective: str,
    teams: List[str],
    task_type: str,
    inputs: List[Dict[str, Any]],
    params: Dict[str, Any],
    max_agents_per_team: int,
    auto_execute: bool,
    seed: int | None,
) -> Dict[str, Any]:
    return await ORCHESTRATION_ENGINE.orchestrate(
        run_id,
        objective,
        teams,
        task_type,
        inputs,
        params,
        max_agents_per_team,
        auto_execute,
        seed,
    )


async def execute_team_stage(
    run_id: str,
    team_id: str,
    objective: str,
    inputs: List[Dict[str, Any]],
    params: Dict[str, Any],
    seed: int | None,
    max_agents: int = 3,
    auto_execute: bool = True,
) -> Dict[str, Any]:
    bundle = await ORCHESTRATION_ENGINE.execute_team(
        run_id,
        team_id,
        objective,
        f"{team_id}_stage_task",
        inputs,
        params,
        max_agents,
        auto_execute,
        seed,
    )
    return bundle


class BaseOrchestrator(BaseAgent):
    """Base orchestrator for delegating agent work."""

    def __init__(self, agent_id: str, team_id: str, registry: AgentRegistry | None = None):
        """Initialize an orchestrator.

        Args:
            agent_id: Orchestrator identifier.
            team_id: Team identifier.
            registry: Optional registry override.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__(agent_id, team_id)
        self.registry = registry or DEFAULT_REGISTRY

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a delegation plan for an objective.

        Args:
            context: Input context.

        Returns:
            List[Dict[str, Any]]: Planned steps.

        Raises:
            None: No explicit exceptions are raised.
        """
        objective = context.get("objective", "Generate synthetic outputs")
        delegation = self.registry.build_delegation_plan(self.team_id, objective, max_agents=3)
        return [
            {"tool": "synthetic", "params": {"context": context, "objective": objective}},
            {"tool": "delegate", "params": {"team": self.team_id, "delegation": delegation}},
        ]

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute orchestration and generate artifacts.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        delegation = []
        for step in plan_steps:
            if step.get("tool") == "delegate":
                delegation = step.get("params", {}).get("delegation", [])
                break
        artifacts = []
        llm_service = get_llm_service()
        llm_summary: str | None = None
        try:
            objective = ""
            for step in plan_steps:
                if step.get("tool") == "synthetic":
                    objective = step.get("params", {}).get("objective", "")
                    break
            prompt = (
                "You are an orchestrator for Fraud Forge. Provide a concise summary for the orchestration output. "
                "Keep it synthetic and defensive.\n"
                f"Team: {self.team_id}. Objective: {objective or 'N/A'}."
            )
            llm_summary = await llm_service.generate(
                messages=[
                    {"role": "system", "content": "You are a defensive fraud simulation assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
                requested_model=_get_llm_model(),
                team_id=self.team_id,
                agent_id=self.team_id,
                actor_id=self.team_id,
            )
            llm_summary = llm_summary.strip()
        except Exception:
            llm_summary = None
        for index, item in enumerate(delegation, start=1):
            artifacts.append(
                {
                    "artifact_id": f"{self.team_id}-artifact-{seed % 10000}-{index}",
                    "agent_id": item.get("agent_id"),
                    "role": item.get("role"),
                    "summary": f"Synthetic output for {item.get('role', 'agent')}.",
                    "quality": round(randomizer.uniform(0.7, 0.96), 2),
                }
            )
        return {
            "summary": llm_summary or "Synthetic orchestrator output",
            "score": round(randomizer.uniform(0.7, 0.95), 2),
            "delegation": delegation,
            "artifacts": artifacts,
            "safety": {"synthetic_only": True, "watermark": "Simulation/Training Only"},
            "llm": bool(llm_summary),
        }


class RedOrchestrator(BaseOrchestrator):
    """Red team orchestrator."""

    def __init__(self):
        """Initialize the red orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("red.orchestrator", "red")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute red orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "attack_plan": {
                    "campaign": "Velocity Spike",
                    "variants": ["velocity_anomaly", "identity_mismatch"],
                    "confidence": round(randomizer.uniform(0.7, 0.9), 2),
                },
                "artifact_type": "AttackPlan",
            }
        )
        return payload


class BlueOrchestrator(BaseOrchestrator):
    """Blue team orchestrator."""

    def __init__(self):
        """Initialize the blue orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("blue.orchestrator", "blue")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute blue orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "decision": {
                    "outcome": randomizer.choice(["allow", "review", "block"]),
                    "confidence": round(randomizer.uniform(0.75, 0.95), 2),
                },
                "artifact_type": "Decision",
            }
        )
        return payload


class PurpleOrchestrator(BaseOrchestrator):
    """Purple team orchestrator."""

    def __init__(self):
        """Initialize the purple orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("purple.orchestrator", "purple")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute purple orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "rulespec": {
                    "rule_id": f"R-FF-{seed % 9999:04d}",
                    "title": "Velocity Spike Defense",
                    "confidence": round(randomizer.uniform(0.78, 0.93), 2),
                },
                "artifact_type": "RuleSpec",
            }
        )
        return payload


class GreenOrchestrator(BaseOrchestrator):
    """Green team orchestrator."""

    def __init__(self):
        """Initialize the green orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("green.orchestrator", "green")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute green orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "patch": {
                    "patch_id": f"PATCH-{seed % 10000:04d}",
                    "risk_level": randomizer.choice(["low", "medium"]),
                },
                "artifact_type": "Patch",
            }
        )
        return payload


class BlackOrchestrator(BaseOrchestrator):
    """Black team orchestrator."""

    def __init__(self):
        """Initialize the black orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("black.orchestrator", "black")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute black orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        randomizer = rng(seed)
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "stress_test": {
                    "tests_run": 12,
                    "failed": 0 if randomizer.random() > 0.2 else 1,
                    "coverage": round(randomizer.uniform(82, 96), 1),
                },
                "artifact_type": "StressTestReport",
            }
        )
        return payload


class OrangeOrchestrator(BaseOrchestrator):
    """Orange team orchestrator."""

    def __init__(self):
        """Initialize the orange orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("orange.orchestrator", "orange")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute orange orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "approval": {
                    "decision": "pending",
                    "notes": "Awaiting release review.",
                },
                "artifact_type": "ApprovalDecision",
            }
        )
        return payload


class GoldOrchestrator(BaseOrchestrator):
    """Gold team orchestrator."""

    def __init__(self):
        """Initialize the gold orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("gold.orchestrator", "gold")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute gold orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "explanation": {
                    "summary": "Synthetic explanation generated for demo.",
                    "details": "Evidence indicates elevated velocity and device risk signals.",
                },
                "artifact_type": "ExplanationPack",
            }
        )
        return payload


class WhiteOrchestrator(BaseOrchestrator):
    """White team orchestrator."""

    def __init__(self):
        """Initialize the white orchestrator.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("white.orchestrator", "white")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        """Execute white orchestrator plan.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.

        Returns:
            Dict[str, Any]: Orchestrator outputs.

        Raises:
            None: No explicit exceptions are raised.
        """
        payload = await super().act(plan_steps, seed)
        payload.update(
            {
                "compliance": {
                    "checks": ["PII_redaction", "audit_trace", "fairness"],
                    "status": "pending",
                },
                "artifact_type": "CompliancePack",
            }
        )
        return payload


class RedAgent(BaseAgent):
    """Red team agent."""

    def __init__(self):
        """Initialize the red agent.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("red.orchestrator.v1", "red")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan red agent steps.

        Args:
            context: Input context.

        Returns:
            List[Dict[str, Any]]: Planned steps.

        Raises:
            None: No explicit exceptions are raised.
        """
        scenario = context.get("scenario_id", "demo")
        return [
            {"tool": "simulate_transactions", "params": {"scenario": scenario, "count": 25, "rails": ["cards", "upi", "ach"]}},
            {"tool": "apply_attack", "params": {"attack_type": "velocity_anomaly", "events": context.get("events", [])}},
        ]


class BlueAgent(BaseAgent):
    """Blue team agent."""

    def __init__(self):
        """Initialize the blue agent.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("blue.orchestrator.v1", "blue")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan blue agent steps.

        Args:
            context: Input context.

        Returns:
            List[Dict[str, Any]]: Planned steps.

        Raises:
            None: No explicit exceptions are raised.
        """
        events = context.get("events", [])
        return [
            {"tool": "score_risk", "params": {"events": events}},
            {"tool": "respond_actions", "params": {"scores": context.get("scores", [])}},
        ]


class GoldAgent(BaseAgent):
    """Gold team agent."""

    def __init__(self):
        """Initialize the gold agent.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        super().__init__("gold.orchestrator.v1", "gold")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan gold agent steps.

        Args:
            context: Input context.

        Returns:
            List[Dict[str, Any]]: Planned steps.

        Raises:
            None: No explicit exceptions are raised.
        """
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate gold agent outputs.

        Args:
            plan_steps: Planned steps.
            seed: Random seed.
            context: Optional context override.

        Returns:
            Dict[str, Any]: Output payload.

        Raises:
            None: No explicit exceptions are raised.
        """
        decision = (context or {}).get("decision", "monitor")
        summary = f"Gold team summary: decision={decision} based on synthetic signals."
        details = "Signals indicate elevated velocity and risk scoring."
        return {"summary": summary, "details": details}

    async def emit(self, context: Dict[str, Any], seed: int) -> AgentTrace:
        """Emit an agent trace using custom act.

        Args:
            context: Input context.
            seed: Random seed.

        Returns:
            AgentTrace: Agent trace.

        Raises:
            None: No explicit exceptions are raised.
        """
        plan_steps = await self.plan(context)
        outputs = await self.act(plan_steps, seed, context)
        notes = await self.reflect(outputs)
        return AgentTrace(agent_id=self.agent_id, team_id=self.team_id, plan=plan_steps, outputs=outputs, notes=notes)


RED_AGENT = RedAgent()
BLUE_AGENT = BlueAgent()
GOLD_AGENT = GoldAgent()

ORCHESTRATORS = {
    "red": RedOrchestrator(),
    "blue": BlueOrchestrator(),
    "purple": PurpleOrchestrator(),
    "green": GreenOrchestrator(),
    "black": BlackOrchestrator(),
    "orange": OrangeOrchestrator(),
    "gold": GoldOrchestrator(),
    "white": WhiteOrchestrator(),
}


def get_orchestrator(team_id: str) -> BaseOrchestrator | None:
    """Return orchestrator for a team.

    Args:
        team_id: Team identifier.

    Returns:
        BaseOrchestrator | None: Orchestrator instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    return ORCHESTRATORS.get(team_id)
