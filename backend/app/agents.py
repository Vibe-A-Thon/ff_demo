from typing import Any, Dict, List
from app.models import AgentTrace
from app.agent_registry import AgentRegistry
from app.tooling import TOOL_IMPLEMENTATIONS, derive_seed, rng

DEFAULT_REGISTRY = AgentRegistry.from_defaults()

class BaseAgent:
    agent_id: str
    team_id: str

    def __init__(self, agent_id: str, team_id: str):
        self.agent_id = agent_id
        self.team_id = team_id

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        outputs: Dict[str, Any] = {}
        for step in plan_steps:
            tool_name = step.get("tool")
            params = step.get("params", {})
            impl = TOOL_IMPLEMENTATIONS.get(tool_name)
            if not impl:
                continue
            step_seed = derive_seed(seed, tool_name)
            outputs[tool_name] = impl(params, step_seed)
        return outputs

    async def reflect(self, outputs: Dict[str, Any]) -> List[str]:
        return []

    async def emit(self, context: Dict[str, Any], seed: int) -> AgentTrace:
        plan_steps = await self.plan(context)
        outputs = await self.act(plan_steps, seed)
        notes = await self.reflect(outputs)
        return AgentTrace(agent_id=self.agent_id, team_id=self.team_id, plan=plan_steps, outputs=outputs, notes=notes)


class BaseOrchestrator(BaseAgent):
    def __init__(self, agent_id: str, team_id: str, registry: AgentRegistry | None = None):
        super().__init__(agent_id, team_id)
        self.registry = registry or DEFAULT_REGISTRY

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        objective = context.get("objective", "Generate synthetic outputs")
        delegation = self.registry.build_delegation_plan(self.team_id, objective, max_agents=3)
        return [
            {"tool": "synthetic", "params": {"context": context, "objective": objective}},
            {"tool": "delegate", "params": {"team": self.team_id, "delegation": delegation}},
        ]

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        randomizer = rng(seed)
        delegation = []
        for step in plan_steps:
            if step.get("tool") == "delegate":
                delegation = step.get("params", {}).get("delegation", [])
                break
        artifacts = []
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
            "summary": "Synthetic orchestrator output",
            "score": round(randomizer.uniform(0.7, 0.95), 2),
            "delegation": delegation,
            "artifacts": artifacts,
            "safety": {"synthetic_only": True, "watermark": "Simulation/Training Only"},
        }


class RedOrchestrator(BaseOrchestrator):
    def __init__(self):
        super().__init__("red.orchestrator", "red")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("blue.orchestrator", "blue")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("purple.orchestrator", "purple")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("green.orchestrator", "green")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("black.orchestrator", "black")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("orange.orchestrator", "orange")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("gold.orchestrator", "gold")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("white.orchestrator", "white")

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
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
    def __init__(self):
        super().__init__("red.orchestrator.v1", "red")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        scenario = context.get("scenario_id", "demo")
        return [
            {"tool": "simulate_transactions", "params": {"scenario": scenario, "count": 25, "rails": ["cards", "upi", "ach"]}},
            {"tool": "apply_attack", "params": {"attack_type": "velocity_anomaly", "events": context.get("events", [])}},
        ]


class BlueAgent(BaseAgent):
    def __init__(self):
        super().__init__("blue.orchestrator.v1", "blue")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        events = context.get("events", [])
        return [
            {"tool": "score_risk", "params": {"events": events}},
            {"tool": "respond_actions", "params": {"scores": context.get("scores", [])}},
        ]


class GoldAgent(BaseAgent):
    def __init__(self):
        super().__init__("gold.orchestrator.v1", "gold")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        decision = (context or {}).get("decision", "monitor")
        summary = f"Gold team summary: decision={decision} based on synthetic signals."
        details = "Signals indicate elevated velocity and risk scoring."
        return {"summary": summary, "details": details}

    async def emit(self, context: Dict[str, Any], seed: int) -> AgentTrace:
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
    return ORCHESTRATORS.get(team_id)
