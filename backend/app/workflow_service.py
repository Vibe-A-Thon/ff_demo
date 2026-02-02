from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.db import db
from app.models import ApprovalRequest, AgentArtifact
from app.tooling import derive_seed, rng
from app.agents import RED_AGENT, BLUE_AGENT, GOLD_AGENT, get_orchestrator, execute_team_stage

WAR_LOOP_STAGES: List[str] = [
    "red_simulate_attack",
    "blue_detect_respond",
    "purple_rulespec_update",
    "green_build_patch",
    "black_stress_test",
    "orange_review_approve",
    "gold_generate_explanation",
    "white_compliance_audit",
    "done",
]

WORKFLOW_STATES: List[str] = [
    "incident_created",
    "triaged",
    "rulespec_drafted",
    "rulespec_pending_approval",
    "rulespec_approved",
    "patch_in_progress",
    "patch_ready",
    "testing_in_progress",
    "evidence_ready",
    "patch_pending_approval",
    "patch_approved",
    "release_planned",
    "release_pending_approval",
    "release_approved",
    "deploying",
    "deployed",
    "monitoring",
    "closed_success",
    "rolled_back",
    "frozen",
]

APPROVAL_STATES = {
    "rulespec_pending_approval": {
        "approval_action": "rulespec_review",
        "approved_state": "rulespec_approved",
        "rejected_state": "rulespec_drafted",
        "roles": ["Bank Fraud Architect/Manager", "Bank Admin", "Super Admin"],
    },
    "patch_pending_approval": {
        "approval_action": "patch_review",
        "approved_state": "patch_approved",
        "rejected_state": "patch_in_progress",
        "roles": ["Bank Fraud TechLead", "Bank Admin", "Super Admin"],
    },
    "release_pending_approval": {
        "approval_action": "release_review",
        "approved_state": "release_approved",
        "rejected_state": "release_planned",
        "roles": ["Bank Fraud TechManager", "Bank Admin", "Super Admin"],
    },
}

WORKFLOW_TRANSITIONS = {
    "incident_created": "triaged",
    "triaged": "rulespec_drafted",
    "rulespec_drafted": "rulespec_pending_approval",
    "rulespec_approved": "patch_in_progress",
    "patch_in_progress": "patch_ready",
    "patch_ready": "testing_in_progress",
    "testing_in_progress": "evidence_ready",
    "evidence_ready": "patch_pending_approval",
    "patch_approved": "release_planned",
    "release_planned": "release_pending_approval",
    "release_approved": "deploying",
    "deploying": "deployed",
    "deployed": "monitoring",
}

TERMINAL_WORKFLOW_STATES = {"closed_success", "rolled_back", "frozen"}


def next_war_loop_stage(current_stage: str) -> str:
    if current_stage not in WAR_LOOP_STAGES:
        return WAR_LOOP_STAGES[0]
    index = WAR_LOOP_STAGES.index(current_stage)
    if index + 1 >= len(WAR_LOOP_STAGES):
        return "done"
    return WAR_LOOP_STAGES[index + 1]


def _synthetic_rulespec(seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    return {
        "rule_id": f"R-FF-{seed % 9999:04d}",
        "title": "Velocity Spike Defense",
        "confidence": round(randomizer.uniform(0.78, 0.93), 2),
        "conditions": [
            {"field": "velocity_bucket", "op": "eq", "value": "spike"},
            {"field": "amount", "op": "gte", "value": 1500},
        ],
        "actions": ["review", "step_up_auth"],
        "notes": "Synthetic rulespec draft from Purple team.",
    }


def _synthetic_patch(seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    return {
        "patch_id": f"PATCH-{seed % 10000:04d}",
        "language": "python",
        "summary": "Add velocity spike threshold with step-up auth enforcement.",
        "risk_level": randomizer.choice(["low", "medium"]),
        "files": ["rules/velocity_spike.py"],
    }


def _synthetic_test_report(seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    failed = 0 if randomizer.random() > 0.25 else 1
    return {
        "tests_run": 12,
        "failed": failed,
        "coverage": round(randomizer.uniform(82, 96), 1),
        "notes": "Synthetic stress test results for Black team.",
    }


def _synthetic_compliance(seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    return {
        "policy_checks": [
            {"check": "PII_redaction", "status": "pass"},
            {"check": "fairness_bias_scan", "status": randomizer.choice(["pass", "pass", "warn"])},
            {"check": "audit_trace", "status": "pass"},
        ],
        "summary": "White team compliance audit complete.",
    }


def _stage_payload(stage: str, seed: int, context: Dict[str, Any]) -> Dict[str, Any]:
    if stage == "purple_rulespec_update":
        return {"rulespec": _synthetic_rulespec(seed)}
    if stage == "green_build_patch":
        return {"patch": _synthetic_patch(seed)}
    if stage == "black_stress_test":
        return {"test_report": _synthetic_test_report(seed)}
    if stage == "orange_review_approve":
        return {"review": {"status": "pending", "summary": "Awaiting Orange approval."}}
    if stage == "white_compliance_audit":
        return {"compliance": _synthetic_compliance(seed)}
    if stage == "done":
        return {"summary": "War loop completed."}
    return {"summary": "Stage executed."}


async def stage_is_approved(run_id: str, stage: str) -> bool:
    approval = await db.approvals.find_one(
        {"resource_type": "run", "resource_id": run_id, "action": stage, "status": "approved"},
        {"_id": 0},
    )
    return approval is not None


async def ensure_stage_approval(run_id: str, stage: str, requestor_id: str = "system") -> Optional[Dict[str, Any]]:
    existing = await db.approvals.find_one(
        {"resource_type": "run", "resource_id": run_id, "action": stage, "status": {"$in": ["pending", "approved"]}},
        {"_id": 0},
    )
    if existing:
        return existing

    approval = ApprovalRequest(
        resource_type="run",
        resource_id=run_id,
        action=stage,
        requestor_id=requestor_id,
        metadata={"stage": stage},
    )
    await db.approvals.insert_one(approval.model_dump())
    return approval.model_dump()


async def execute_war_loop_stage(run: Dict[str, Any], stage: str, seed: int) -> Tuple[Dict[str, Any], Optional[str]]:
    context: Dict[str, Any] = {"scenario_id": run.get("scenario_id")}
    stage_to_team = {
        "red_simulate_attack": "red",
        "blue_detect_respond": "blue",
        "purple_rulespec_update": "purple",
        "green_build_patch": "green",
        "black_stress_test": "black",
        "orange_review_approve": "orange",
        "gold_generate_explanation": "gold",
        "white_compliance_audit": "white",
    }

    team_id = stage_to_team.get(stage)
    if team_id:
        orchestrator = get_orchestrator(team_id)
        bundle = await execute_team_stage(
            run_id=run.get("id", ""),
            team_id=team_id,
            objective=f"{stage} objective",
            inputs=run.get("stage_inputs", []) or [],
            params={"scenario_id": run.get("scenario_id")},
            seed=seed,
            max_agents=3,
            auto_execute=True,
        )

        for task in bundle.get("tasks", []):
            await db.agent_tasks.update_one(
                {"task_id": task.task_id},
                {"$set": task.model_dump()},
                upsert=True,
            )

        for artifact in bundle.get("artifacts", []):
            await db.agent_artifacts.update_one(
                {"artifact_id": artifact.get("artifact_id")},
                {"$set": AgentArtifact(**artifact).model_dump()},
                upsert=True,
            )

        for execution in bundle.get("executions", []):
            task = execution.get("task")
            result = execution.get("result")
            if task and result:
                await db.agent_tasks.update_one(
                    {"task_id": task.task_id},
                    {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
                )

        bundle_payload = {
            "team_id": team_id,
            "tasks": [task.model_dump() for task in bundle["tasks"]],
            "artifacts": bundle["artifacts"],
            "lineage": bundle["lineage"],
            "executions": [
                {
                    "task_id": execution["task"].task_id,
                    "status": execution["result"].status,
                    "metrics": execution["result"].metrics,
                }
                for execution in bundle.get("executions", [])
            ],
        }

        if orchestrator:
            if stage == "red_simulate_attack":
                red_trace = await RED_AGENT.emit(context, seed)
                return {
                    "agent": red_trace.model_dump(),
                    "outputs": red_trace.outputs,
                    "orchestrator": (await orchestrator.emit(context, seed)).model_dump(),
                    "bundle": bundle_payload,
                }, None
            if stage == "blue_detect_respond":
                last_events = run.get("last_events") or []
                blue_trace = await BLUE_AGENT.emit({"events": last_events}, seed)
                return {
                    "agent": blue_trace.model_dump(),
                    "outputs": blue_trace.outputs,
                    "orchestrator": (await orchestrator.emit({"events": last_events}, seed)).model_dump(),
                    "bundle": bundle_payload,
                }, None
            if stage == "gold_generate_explanation":
                decision = run.get("last_decision", "monitor")
                gold_trace = await GOLD_AGENT.emit({"decision": decision}, seed)
                return {
                    "agent": gold_trace.model_dump(),
                    "outputs": gold_trace.outputs,
                    "orchestrator": (await orchestrator.emit({"decision": decision}, seed)).model_dump(),
                    "bundle": bundle_payload,
                }, None
            orchestrator_trace = await orchestrator.emit(context, seed)
            payload = {"agent": orchestrator_trace.model_dump(), "outputs": orchestrator_trace.outputs, "bundle": bundle_payload}
            if stage == "black_stress_test":
                report = orchestrator_trace.outputs.get("stress_test", {})
                if report.get("failed", 0) > 0:
                    return {"outputs": payload, "status": "failed"}, "purple_rulespec_update"
            return payload, None

    payload = _stage_payload(stage, seed, context)
    if stage == "black_stress_test":
        report = payload.get("test_report", {})
        if report.get("failed", 0) > 0:
            return {"outputs": payload, "status": "failed"}, "purple_rulespec_update"
    return {"outputs": payload, "status": "ok"}, None


def can_transition_from(state: str) -> bool:
    if state in TERMINAL_WORKFLOW_STATES:
        return False
    return True


def next_workflow_state(state: str, outcome: Optional[str] = None) -> str:
    if state == "monitoring":
        return "rolled_back" if outcome == "rolled_back" else "closed_success"
    if state in WORKFLOW_TRANSITIONS:
        return WORKFLOW_TRANSITIONS[state]
    if state in APPROVAL_STATES:
        return state
    return state


def build_workflow_entry(state: str, actor_id: str, notes: Optional[str]) -> Dict[str, Any]:
    return {
        "state": state,
        "actor_id": actor_id,
        "notes": notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def advance_workflow(run: Dict[str, Any], actor_id: str, outcome: Optional[str], notes: Optional[str]) -> Tuple[str, List[Dict[str, Any]]]:
    state = run.get("workflow_state", "incident_created")
    transitions: List[Dict[str, Any]] = []

    if not can_transition_from(state):
        return state, transitions

    next_state = next_workflow_state(state, outcome)
    if next_state in APPROVAL_STATES:
        await ensure_stage_approval(run["id"], next_state, requestor_id=actor_id)

    transitions.append(build_workflow_entry(next_state, actor_id, notes))
    return next_state, transitions


async def decide_workflow(run: Dict[str, Any], actor_id: str, actor_role: Optional[str], decision: str, notes: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    state = run.get("workflow_state", "incident_created")
    approval_rule = APPROVAL_STATES.get(state)
    if not approval_rule:
        return state, {"message": "No approval required"}

    if actor_role and actor_role not in approval_rule.get("roles", []):
        return state, {"message": "Role not permitted", "allowed_roles": approval_rule.get("roles")}

    approval_action = approval_rule["approval_action"]
    await ensure_stage_approval(run["id"], state, requestor_id=actor_id)

    approval = await db.approvals.find_one(
        {"resource_type": "run", "resource_id": run["id"], "action": state},
        {"_id": 0},
    )
    if approval and approval.get("requestor_id") == actor_id:
        return state, {"message": "SoD violation: requester cannot approve own request"}

    await db.approvals.update_one(
        {"resource_type": "run", "resource_id": run["id"], "action": state},
        {
            "$set": {"status": "approved" if decision == "approved" else "rejected"},
            "$push": {
                "approvers": {
                    "approver_id": actor_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": decision,
                    "notes": notes,
                    "approval_action": approval_action,
                }
            },
        },
    )

    next_state = approval_rule["approved_state"] if decision == "approved" else approval_rule["rejected_state"]
    entry = build_workflow_entry(next_state, actor_id, notes)
    return next_state, entry


async def get_workflow_approvals(run_id: str) -> List[Dict[str, Any]]:
    return await db.approvals.find(
        {"resource_type": "run", "resource_id": run_id},
        {"_id": 0},
    ).to_list(200)


async def compute_governance_status(run_id: str) -> Dict[str, Any]:
    approvals = await get_workflow_approvals(run_id)
    decision_by_action = {a.get("action"): a.get("status") for a in approvals}
    required = [
        "rulespec_pending_approval",
        "patch_pending_approval",
        "release_pending_approval",
    ]

    rejected = [action for action, status in decision_by_action.items() if status == "rejected"]
    pending = [action for action in required if decision_by_action.get(action) != "approved"]

    if rejected:
        status = "FREEZE_RELEASES"
    elif pending:
        status = "PROCEED_WITH_REVIEW"
    else:
        status = "SAFE_TO_PROCEED"

    return {
        "run_id": run_id,
        "status": status,
        "pending": pending,
        "rejected": rejected,
        "required": required,
    }
