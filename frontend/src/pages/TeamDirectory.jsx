import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ScrollArea } from "../components/ui/scroll-area";
import { Skeleton } from "../components/ui/skeleton";
import { Users, Shield, Swords, Brain, Zap } from "lucide-react";
import { agentAPI, teamAPI } from "../lib/api";
import { toast } from "sonner";

const teamIcons = {
  red: Swords,
  blue: Shield,
  purple: Brain,
  green: Zap,
  black: Shield,
  orange: Shield,
  gold: Brain,
  white: Shield,
};

const TeamDirectory = () => {
  const [teams, setTeams] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTeams = async () => {
      setLoading(true);
      try {
        const [teamRes, agentRes] = await Promise.all([teamAPI.getAll(), agentAPI.getAll()]);
        setTeams(teamRes?.data || []);
        setAgents(agentRes?.data || []);
      } catch (error) {
        toast.error("Failed to load team directory.");
        setTeams([]);
        setAgents([]);
      } finally {
        setLoading(false);
      }
    };
    loadTeams();
  }, []);

  const teamStats = useMemo(() => {
    return teams.map((team) => {
      const teamAgents = agents.filter((agent) => agent.team_id === team.team_id);
      const activeCount = teamAgents.filter((agent) => agent.status === "active" || agent.status === "running").length;
      return {
        ...team,
        totalAgents: teamAgents.length,
        activeAgents: activeCount,
        sampleAgents: teamAgents.slice(0, 4),
      };
    });
  }, [teams, agents]);

  return (
    <div className="flex h-full flex-col gap-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Organization</p>
            <h1 className="text-2xl font-semibold">Team Directory</h1>
          </div>
          <Badge className="bg-emerald-500/15 text-emerald-300 border border-emerald-500/30" data-testid="teams-count">
            {teams.length} teams online
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Review the eight-team organization, their mission statements, and live agent coverage. Use this view to confirm
          staffing before launching a war loop run.
        </p>
      </header>
      <ScrollArea className="flex-1">
        <div className="grid gap-4 pr-2 md:grid-cols-2 xl:grid-cols-4" data-testid="team-grid">
          {loading && Array.from({ length: 8 }).map((_, idx) => (
            <Card key={`team-skeleton-${idx}`} className="border-border">
              <CardHeader>
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
              </CardContent>
            </Card>
          ))}
          {!loading && teamStats.map((team) => {
            const Icon = teamIcons[team.team_id] || Users;
            return (
              <Card key={team.team_id} className="border-border" data-testid={`team-card-${team.team_id}`}>
                <CardHeader className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="border-border text-xs">
                      {team.internal_name}
                    </Badge>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <CardTitle className="text-lg">{team.bank_facing_name}</CardTitle>
                  <p className="text-xs text-muted-foreground">{team.mission_statement}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{team.totalAgents} agents</span>
                    <span>{team.activeAgents} active</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {team.capability_tags?.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="border-border text-[11px]">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <ScrollArea className="h-20">
                    <div className="space-y-1 text-xs text-muted-foreground">
                      {team.sampleAgents.length === 0 && <span>No agents registered.</span>}
                      {team.sampleAgents.map((agent) => (
                        <div key={agent.agent_id} className="flex items-center justify-between">
                          <span>{agent.agent_name}</span>
                          <Badge variant="outline" className="border-border text-[10px]">
                            {agent.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                  <Button variant="outline" size="sm" className="w-full" data-testid={`team-view-${team.team_id}`}>
                    View Team Detail
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
};

export default TeamDirectory;
