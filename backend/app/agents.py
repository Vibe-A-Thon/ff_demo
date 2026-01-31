from typing import Any, Dict, List
from app.models import AgentTrace
from app.tooling import TOOL_IMPLEMENTATIONS, derive_seed

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
