import pytest
from agents.base import BaseAgent, AgentDecision


class TestAgent(BaseAgent):
    pass


@pytest.mark.asyncio
async def test_agent_initialization():
    agent = TestAgent(role="tester")
    assert agent.role == "tester"
    assert agent.tools == []


@pytest.mark.asyncio
async def test_agent_think():
    agent = TestAgent(role="tester")
    context = {"input": "test"}
    decision = await agent.think(context)

    assert isinstance(decision, AgentDecision)
    assert decision.action == "wait"
    assert "Default reasoning" in decision.reasoning


@pytest.mark.asyncio
async def test_agent_act():
    agent = TestAgent(role="tester")
    decision = AgentDecision(action="test_action", params={}, reasoning="test")
    result = await agent.act(decision)

    assert result["status"] == "executed"
    assert result["action"] == "test_action"
