from __future__ import annotations

from typing import Dict, List, Optional
from app.models import AgentProfile, TeamProfile
from app.teams_data import default_agent_payloads, default_team_payloads


class AgentRegistry:
    def __init__(self) -> None:
        self._teams: Dict[str, TeamProfile] = {}
        self._agents: Dict[str, AgentProfile] = {}

    @classmethod
    def from_defaults(cls) -> "AgentRegistry":
        registry = cls()
        for team_payload in default_team_payloads():
            team = TeamProfile(**team_payload)
            registry._teams[team.team_id] = team
        for agent_payload in default_agent_payloads():
            agent = AgentProfile(**agent_payload)
            registry._agents[agent.agent_id] = agent
        return registry

    def list_teams(self) -> List[TeamProfile]:
        return list(self._teams.values())

    def list_agents(self, team_id: Optional[str] = None) -> List[AgentProfile]:
        if not team_id:
            return list(self._agents.values())
        return [agent for agent in self._agents.values() if agent.team_id == team_id]

    def get_team(self, team_id: str) -> Optional[TeamProfile]:
        return self._teams.get(team_id)

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self._agents.get(agent_id)

    def get_team_agents(self, team_id: str) -> List[AgentProfile]:
        return self.list_agents(team_id)

    def register_agent(self, agent: AgentProfile) -> None:
        self._agents[agent.agent_id] = agent

    def update_agent_status(self, agent_id: str, status: str) -> Optional[AgentProfile]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        agent.status = status
        return agent

    def build_delegation_plan(self, team_id: str, objective: str, max_agents: int = 3) -> List[Dict[str, str]]:
        agents = sorted(self.get_team_agents(team_id), key=lambda item: item.agent_id)
        selected = agents[:max_agents]
        return [
            {
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "role": agent.role,
                "objective": objective,
            }
            for agent in selected
        ]
