import React, { useMemo, useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Bot, PauseCircle, PlayCircle, Plus, Shield, Users } from "lucide-react";
import { agentAPI, teamAPI } from "../lib/api";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";

const statusStyles = {
  active: "bg-green-500/15 text-green-400 border-green-500/20",
  paused: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  idle: "bg-zinc-800 text-zinc-400 border-zinc-700",
  running: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  blocked: "bg-red-500/15 text-red-400 border-red-500/20",
};

const modeStyles = {
  HITL: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  HOTL: "bg-purple-500/15 text-purple-400 border-purple-500/20",
};

const AgentManagement = () => {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [teamFilter, setTeamFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [teams, setTeams] = useState([]);
  const [agents, setAgents] = useState([]);
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [assignOpen, setAssignOpen] = useState(false);
  const [assignAgent, setAssignAgent] = useState(null);
  const [taskType, setTaskType] = useState("status_check");
  const [taskPriority, setTaskPriority] = useState("2");
  const [taskRunId, setTaskRunId] = useState("ops");
  const [taskNotes, setTaskNotes] = useState("");

  useEffect(() => {
    const loadRoster = async () => {
      setLoading(true);
      try {
        const [teamRes, agentRes, registryRes] = await Promise.all([
          teamAPI.getAll(),
          agentAPI.getAll(),
          agentAPI.getRegistry(),
        ]);
        setTeams(teamRes?.data || []);
        setAgents(agentRes?.data || []);
        setRegistrySnapshot(registryRes?.data || null);
      } catch (error) {
        toast.error("Failed to load agent roster.");
        setTeams([]);
        setAgents([]);
        setRegistrySnapshot(null);
      } finally {
        setLoading(false);
      }
    };
    loadRoster();
  }, []);

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const name = agent.agent_name || "";
      const matchesSearch = name.toLowerCase().includes(search.toLowerCase());
      const matchesTeam = teamFilter === "all" || agent.team_id === teamFilter;
      const matchesStatus = statusFilter === "all" || agent.status === statusFilter;
      return matchesSearch && matchesTeam && matchesStatus;
    });
  }, [agents, search, teamFilter, statusFilter]);

  const handleAssign = (agent) => {
    setAssignAgent(agent);
    setTaskRunId("ops");
    setTaskType("status_check");
    setTaskPriority("2");
    setTaskNotes("");
    setAssignOpen(true);
  };

  const submitAssignment = async () => {
    if (!assignAgent) return;
    try {
      await agentAPI.createTask({
        run_id: taskRunId || "ops",
        team_id: assignAgent.team_id,
        target_agent_id: assignAgent.agent_id,
        task_type: taskType,
        inputs: taskNotes ? [{ note: taskNotes }] : [],
        priority: Number(taskPriority || 2),
        created_by: user?.email || user?.id || "operator",
      });
      toast.success("Task assigned to agent.");
      setAssignOpen(false);
    } catch (error) {
      toast.error("Failed to assign task.");
    }
  };

  const toggleStatus = (agent) => {
    const nextStatus = agent.status === "active" ? "paused" : "active";
    setAgents((prev) => prev.map((item) => (item.agent_id === agent.agent_id ? { ...item, status: nextStatus } : item)));
    toast("Status update queued for governance review.");
  };

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
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="border-border">
            {teams.length} teams
          </Badge>
          <Badge variant="outline" className="border-border">
            {agents.length} agents
          </Badge>
          <Badge variant="outline" className="border-border">
            {agents.filter((agent) => agent.status === "active").length} active
          </Badge>
        </div>
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
              {teams.map((team) => (
                <SelectItem key={team.team_id} value={team.team_id}>
                  {team.internal_name}
                </SelectItem>
              ))}
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
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="blocked">Blocked</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card className="border-border" data-testid="agent-registry-preview">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Registry Delegation Preview</CardTitle>
          <Badge variant="outline" className="border-border">
            {registrySnapshot?.agents?.length || 0} registry agents
          </Badge>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {registrySnapshot?.delegation_preview?.length ? (
            <div className="grid gap-2 md:grid-cols-3">
              {registrySnapshot.delegation_preview.map((item) => (
                <div key={item.agent_id} className="rounded-md border border-border bg-zinc-900/40 p-3">
                  <div className="font-medium text-white">{item.agent_name}</div>
                  <div className="text-xs text-muted-foreground">{item.role}</div>
                  <div className="mt-2 text-xs text-muted-foreground">{item.objective}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">Registry preview not available.</div>
          )}
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
              {loading && (
                <TableRow>
                  <TableCell colSpan={6} className="text-muted-foreground">
                    Loading agents...
                  </TableCell>
                </TableRow>
              )}
              {!loading && filteredAgents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-muted-foreground">
                    No agents match the current filters.
                  </TableCell>
                </TableRow>
              )}
              {!loading && filteredAgents.map((agent) => (
                <TableRow key={agent.agent_id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-muted-foreground" />
                      {agent.agent_name}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-border" data-testid={`agent-team-${agent.agent_id}`}>
                      {agent.team_id}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={`border ${statusStyles[agent.status] || statusStyles.idle}`} data-testid={`agent-status-${agent.agent_id}`}>
                      {agent.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={`border ${modeStyles[agent.operating_mode] || modeStyles.HITL}`} data-testid={`agent-mode-${agent.agent_id}`}>
                      {agent.operating_mode?.toUpperCase() || "HITL"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{agent.updated_at ? new Date(agent.updated_at).toLocaleString() : "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="outline" size="sm" data-testid={`agent-toggle-${agent.agent_id}`} onClick={() => toggleStatus(agent)}>
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
                      <Button
                        variant="outline"
                        size="sm"
                        data-testid={`agent-assign-${agent.agent_id}`}
                        onClick={() => handleAssign(agent)}
                      >
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

      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent className="bg-card border-border max-w-lg" data-testid="agent-assign-dialog">
          <DialogHeader>
            <DialogTitle>Assign Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Agent</Label>
              <div className="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
                {assignAgent?.agent_name || "Select an agent"}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-run-id">Run ID</Label>
              <Input
                id="task-run-id"
                value={taskRunId}
                onChange={(event) => setTaskRunId(event.target.value)}
                data-testid="agent-task-run-id"
              />
            </div>
            <div className="space-y-2">
              <Label>Task Type</Label>
              <Select value={taskType} onValueChange={setTaskType}>
                <SelectTrigger data-testid="agent-task-type">
                  <SelectValue placeholder="Select task type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="status_check">Status Check</SelectItem>
                  <SelectItem value="scenario_review">Scenario Review</SelectItem>
                  <SelectItem value="evidence_pack">Evidence Pack</SelectItem>
                  <SelectItem value="compliance_review">Compliance Review</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select value={taskPriority} onValueChange={setTaskPriority}>
                <SelectTrigger data-testid="agent-task-priority">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">High</SelectItem>
                  <SelectItem value="2">Medium</SelectItem>
                  <SelectItem value="3">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-notes">Notes</Label>
              <Input
                id="task-notes"
                value={taskNotes}
                onChange={(event) => setTaskNotes(event.target.value)}
                placeholder="Add any context or constraints"
                data-testid="agent-task-notes"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setAssignOpen(false)} data-testid="agent-task-cancel">
                Cancel
              </Button>
              <Button onClick={submitAssignment} data-testid="agent-task-submit">
                Assign Task
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AgentManagement;
