from typing import TypedDict, Annotated, Sequence, Dict, Any, Union
import operator
from langgraph.graph import StateGraph, END
from agents.base import BaseAgent, AgentDecision
from core.memory.manager import MemoryManager
from core.messaging import MessageBroker


class BattleState(TypedDict):
    battle_id: str
    turn: int
    history: Annotated[Sequence[Dict[str, Any]], operator.add]
    current_attack: Dict[str, Any]
    current_defense: Dict[str, Any]
    outcome: str
    is_finished: bool


class WarLoopStateMachine:
    def __init__(
        self,
        red_agent: BaseAgent,
        blue_agent: BaseAgent,
        memory: MemoryManager = None,
        broker: MessageBroker = None,
    ):
        self.red_agent = red_agent
        self.blue_agent = blue_agent
        self.memory = memory
        self.broker = broker
        self.workflow = StateGraph(BattleState)
        self._build_graph()

    def _build_graph(self):
        # Define nodes
        self.workflow.add_node("red_attack", self.red_attack_node)
        self.workflow.add_node("blue_detect", self.blue_detect_node)
        self.workflow.add_node("outcome_determination", self.outcome_determination_node)

        # Define edges
        self.workflow.set_entry_point("red_attack")
        self.workflow.add_edge("red_attack", "blue_detect")
        self.workflow.add_edge("blue_detect", "outcome_determination")
        self.workflow.add_conditional_edges(
            "outcome_determination",
            self.should_continue,
            {"continue": "red_attack", "end": END},
        )

        self.app = self.workflow.compile()

    async def red_attack_node(self, state: BattleState) -> Dict[str, Any]:
        """
        Red Agent generates an attack.
        """
        context = {"history": state.get("history", []), "turn": state.get("turn", 0)}

        decision = await self.red_agent.think(context)
        attack = await self.red_agent.act(decision)

        # Log to messaging
        if self.broker:
            await self.broker.publish(
                "battle_events",
                {"type": "attack", "battle_id": state.get("battle_id"), "data": attack},
            )

        return {
            "current_attack": attack,
            "turn": state.get("turn", 0) + 1,
            "history": [{"role": "red", "action": attack}],
        }

    async def blue_detect_node(self, state: BattleState) -> Dict[str, Any]:
        """
        Blue Agent attempts detection.
        """
        context = {
            "attack": state.get("current_attack"),
            "history": state.get("history", []),
        }

        decision = await self.blue_agent.think(context)
        defense = await self.blue_agent.act(decision)

        # Log to messaging
        if self.broker:
            await self.broker.publish(
                "battle_events",
                {
                    "type": "defense",
                    "battle_id": state.get("battle_id"),
                    "data": defense,
                },
            )

        return {
            "current_defense": defense,
            "history": [{"role": "blue", "action": defense}],
        }

    async def outcome_determination_node(self, state: BattleState) -> Dict[str, Any]:
        """
        Determine the winner of the round.
        """
        attack = state.get("current_attack")
        defense = state.get("current_defense")

        # Simple logic for now: if blue defends, blue wins.
        # In reality, this would be complex logic comparing attack parameters vs defense rules.
        outcome = "blue_win" if defense.get("action") == "block" else "red_win"

        if self.memory:
            self.memory.remember_battle(
                state.get("battle_id"),
                {"attack": attack, "defense": defense, "outcome": outcome},
            )

        return {"outcome": outcome, "history": [{"role": "system", "outcome": outcome}]}

    def should_continue(self, state: BattleState) -> str:
        """
        Decide whether to continue the battle or end.
        """
        if state.get("turn", 0) >= 5:  # Limit to 5 turns for now
            return "end"
        return "continue"
