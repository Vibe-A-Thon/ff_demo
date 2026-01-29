import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Bot, PauseCircle, PlayCircle, Plus, Shield, Users } from "lucide-react";

const agentRoster = [
  { id: "agent-red-01", name: "Red Orchestrator", team: "Red", status: "active", mode: "HOTL", lastRun: "6m ago" },
  { id: "agent-blue-02", name: "Blue Sentinel", team: "Blue", status: "active", mode: "HITL", lastRun: "12m ago" },
  { id: "agent-purple-04", name: "Root Cause Analyst", team: "Purple", status: "paused", mode: "HITL", lastRun: "1h ago" },
  { id: "agent-green-03", name: "Rule-to-Code Translator", team: "Green", status: "active", mode: "HOTL", lastRun: "18m ago" },
  { id: "agent-black-01", name: "Chaos Injection", team: "Black", status: "idle", mode: "HOTL", lastRun: "3h ago" },
  { id: "agent-gold-02", name: "Decision Explainer", team: "Gold", status: "active", mode: "HITL", lastRun: "9m ago" },
  { id: "agent-white-01", name: "Compliance Validator", team: "White", status: "active", mode: "HITL", lastRun: "28m ago" },
];

const statusStyles = {
  active: "bg-green-500/15 text-green-400 border-green-500/20",
  paused: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  idle: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

const modeStyles = {
  HITL: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  HOTL: "bg-purple-500/15 text-purple-400 border-purple-500/20",
};

const AgentManagement = () => {
  const [search, setSearch] = useState("");
  const [teamFilter, setTeamFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredAgents = useMemo(() => {
    return agentRoster.filter((agent) => {
      const matchesSearch = agent.name.toLowerCase().includes(search.toLowerCase());
      const matchesTeam = teamFilter === "all" || agent.team.toLowerCase() === teamFilter;
      const matchesStatus = statusFilter === "all" || agent.status === statusFilter;
      return matchesSearch && matchesTeam && matchesStatus;
    });
  }, [search, teamFilter, statusFilter]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Operations</p>
            <h1 className="text-2xl font-semibold">Agent Management</h1>
          </div>
          <Button className="gap-2" data-testid="agent-add">
            <Plus className="h-4 w-4" />
            Add Agent
          </Button>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Control agent availability, modes, and ownership for each team. Changes are logged to the audit trail.
        </p>
      </header>

      <Card className="border-border" data-testid="agent-filters">
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
          <div className="flex-1">
            <Input
              placeholder="Search agents, teams, or capabilities"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              data-testid="agent-search"
            />
          </div>
          <Select value={teamFilter} onValueChange={setTeamFilter}>
            <SelectTrigger className="w-full md:w-[180px]" data-testid="agent-filter-team">
              <SelectValue placeholder="Team" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teams</SelectItem>
              <SelectItem value="red">Red</SelectItem>
              <SelectItem value="blue">Blue</SelectItem>
              <SelectItem value="purple">Purple</SelectItem>
              <SelectItem value="green">Green</SelectItem>
              <SelectItem value="black">Black</SelectItem>
              <SelectItem value="gold">Gold</SelectItem>
              <SelectItem value="white">White</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full md:w-[180px]" data-testid="agent-filter-status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="idle">Idle</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card className="border-border" data-testid="agent-table">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Active Agent Roster</CardTitle>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-4 w-4" />
            Governance enforced
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Team</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAgents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-muted-foreground" />
                      {agent.name}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-border" data-testid={`agent-team-${agent.id}`}>
                      {agent.team}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={`border ${statusStyles[agent.status]}`} data-testid={`agent-status-${agent.id}`}>
                      {agent.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={`border ${modeStyles[agent.mode]}`} data-testid={`agent-mode-${agent.id}`}>
                      {agent.mode}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{agent.lastRun}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="outline" size="sm" data-testid={`agent-toggle-${agent.id}`}>
                        {agent.status === "active" ? (
                          <>
                            <PauseCircle className="mr-1 h-3.5 w-3.5" />
                            Pause
                          </>
                        ) : (
                          <>
                            <PlayCircle className="mr-1 h-3.5 w-3.5" />
                            Activate
                          </>
                        )}
                      </Button>
                      <Button variant="outline" size="sm" data-testid={`agent-assign-${agent.id}`}>
                        <Users className="mr-1 h-3.5 w-3.5" />
                        Assign
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default AgentManagement;
