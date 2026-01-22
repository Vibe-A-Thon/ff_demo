import pytest
from core.orchestration import WarLoopStateMachine, BattleState
from agents.base import BaseAgent, AgentDecision
from unittest.mock import AsyncMock, MagicMock


class MockAgent(BaseAgent):
    async def think(self, context):
        return AgentDecision(action="test_action", params={}, reasoning="test")

    async def act(self, decision):
        return {"action": "test_action", "details": "test"}


@pytest.mark.asyncio
async def test_war_loop_initialization():
    red = MockAgent("red")
    blue = MockAgent("blue")
    machine = WarLoopStateMachine(red, blue)
    assert machine.app is not None


@pytest.mark.asyncio
async def test_red_attack_node():
    red = MockAgent("red")
    blue = MockAgent("blue")
    broker = AsyncMock()
    machine = WarLoopStateMachine(red, blue, broker=broker)

    state = {"battle_id": "1", "turn": 0, "history": []}
    result = await machine.red_attack_node(state)

    assert result["current_attack"]["action"] == "test_action"
    assert result["turn"] == 1
    assert len(result["history"]) == 1
    broker.publish.assert_called_once()


@pytest.mark.asyncio
async def test_blue_detect_node():
    red = MockAgent("red")
    blue = MockAgent("blue")
    broker = AsyncMock()
    machine = WarLoopStateMachine(red, blue, broker=broker)

    state = {"battle_id": "1", "current_attack": {"action": "attack"}, "history": []}
    result = await machine.blue_detect_node(state)

    assert result["current_defense"]["action"] == "test_action"
    broker.publish.assert_called_once()


@pytest.mark.asyncio
async def test_outcome_determination_node():
    red = MockAgent("red")
    blue = MockAgent("blue")
    memory = MagicMock()
    machine = WarLoopStateMachine(red, blue, memory=memory)

    state = {
        "battle_id": "1",
        "current_attack": {"action": "attack"},
        "current_defense": {"action": "block"},  # trigger blue win
    }
    result = await machine.outcome_determination_node(state)

    assert result["outcome"] == "blue_win"
    memory.remember_battle.assert_called_once()


@pytest.mark.asyncio
async def test_should_continue():
    red = MockAgent("red")
    blue = MockAgent("blue")
    machine = WarLoopStateMachine(red, blue)

    assert machine.should_continue({"turn": 1}) == "continue"
    assert machine.should_continue({"turn": 5}) == "end"
