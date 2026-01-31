import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { agentAPI, teamAPI } from "../lib/api";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import { ClipboardList, CheckCircle2, XCircle } from "lucide-react";

const statusStyles = {
  pending: "bg-zinc-800 text-zinc-300 border-zinc-700",
  running: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  active: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  success: "bg-green-500/15 text-green-400 border-green-500/20",
  failed: "bg-red-500/15 text-red-400 border-red-500/20",
  blocked: "bg-red-500/15 text-red-400 border-red-500/20",
  paused: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  fulfilled: "bg-green-500/15 text-green-400 border-green-500/20",
  open: "bg-zinc-800 text-zinc-300 border-zinc-700",
};

const AgentTaskQueue = () => {
  const { user } = useAuth();
  const [teams, setTeams] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [teamFilter, setTeamFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    const loadQueue = async () => {
      setLoading(true);
      try {
        const [teamRes, taskRes, requestRes] = await Promise.all([
          teamAPI.getAll(),
          agentAPI.listTasks(),
          agentAPI.listRequests(),
        ]);
        setTeams(teamRes?.data || []);
        setTasks(taskRes?.data || []);
        setRequests(requestRes?.data || []);
      } catch (error) {
        toast.error("Failed to load agent queue.");
        setTeams([]);
        setTasks([]);
        setRequests([]);
      } finally {
        setLoading(false);
      }
    };
    loadQueue();
  }, []);

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesSearch =
        task.task_type?.toLowerCase().includes(search.toLowerCase()) ||
        task.run_id?.toLowerCase().includes(search.toLowerCase());
      const matchesTeam = teamFilter === "all" || task.team_id === teamFilter;
      const matchesStatus = statusFilter === "all" || task.status === statusFilter;
      return matchesSearch && matchesTeam && matchesStatus;
    });
  }, [tasks, search, teamFilter, statusFilter]);

  const filteredRequests = useMemo(() => {
    return requests.filter((request) => {
      const matchesSearch = request.artifact_type?.toLowerCase().includes(search.toLowerCase());
      const matchesTeam =
        teamFilter === "all" || request.from_team === teamFilter || request.to_team === teamFilter;
      const matchesStatus = statusFilter === "all" || request.status === statusFilter;
      return matchesSearch && matchesTeam && matchesStatus;
    });
  }, [requests, search, teamFilter, statusFilter]);

  const markTask = async (taskId, status) => {
    try {
      await agentAPI.completeTask(taskId, {
        status,
        outputs: [],
        metrics: {},
        decision_trace: ["Updated via queue"],
      });
      setTasks((prev) => prev.map((task) => (task.task_id === taskId ? { ...task, status } : task)));
      toast.success("Task status updated.");
    } catch (error) {
      toast.error("Failed to update task.");
    }
  };

  const respondRequest = async (requestId, status) => {
    try {
      await agentAPI.respondRequest(requestId, {
        status,
        response: { actor: user?.email || user?.id || "operator" },
      });
      setRequests((prev) => prev.map((req) => (req.request_id === requestId ? { ...req, status } : req)));
      toast.success("Request response saved.");
    } catch (error) {
      toast.error("Failed to respond to request.");
    }
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Operations</p>
            <h1 className="text-2xl font-semibold">Agent Task Queue</h1>
          </div>
          <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30" data-testid="agent-queue-count">
            {tasks.length} tasks • {requests.length} requests
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Track cross-team tasks, coordination requests, and governance responses in one place.
        </p>
      </header>

      <Card className="border-border" data-testid="agent-queue-filters">
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
          <Input
            placeholder="Search run id, task type, or artifact"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            data-testid="agent-queue-search"
          />
          <Select value={teamFilter} onValueChange={setTeamFilter}>
            <SelectTrigger className="w-full md:w-[200px]" data-testid="agent-queue-team">
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
            <SelectTrigger className="w-full md:w-[200px]" data-testid="agent-queue-status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="blocked">Blocked</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="fulfilled">Fulfilled</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Tabs defaultValue="tasks" className="space-y-4" data-testid="agent-queue-tabs">
        <TabsList>
          <TabsTrigger value="tasks" data-testid="agent-queue-tab-tasks">Tasks</TabsTrigger>
          <TabsTrigger value="requests" data-testid="agent-queue-tab-requests">Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ClipboardList className="h-4 w-4 text-blue-400" />
                Active Tasks
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[420px]">
                <div className="divide-y divide-border">
                  {loading && (
                    <div className="p-4 text-sm text-muted-foreground">Loading tasks...</div>
                  )}
                  {!loading && filteredTasks.length === 0 && (
                    <div className="p-4 text-sm text-muted-foreground">No tasks in queue.</div>
                  )}
                  {filteredTasks.map((task) => (
                    <div key={task.task_id} className="px-5 py-4 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium">{task.task_type}</p>
                          <p className="text-xs text-muted-foreground">
                            Run {task.run_id} • {task.team_id}
                          </p>
                        </div>
                        <Badge className={`border ${statusStyles[task.status] || statusStyles.pending}`}>
                          {task.status}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span>Priority: {task.priority ?? 0}</span>
                        <span>Created: {task.created_at ? new Date(task.created_at).toLocaleString() : "-"}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => markTask(task.task_id, "success")}
                          data-testid={`agent-task-success-${task.task_id}`}
                        >
                          <CheckCircle2 className="mr-1 h-4 w-4" />
                          Mark Success
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => markTask(task.task_id, "failed")}
                          data-testid={`agent-task-failed-${task.task_id}`}
                        >
                          <XCircle className="mr-1 h-4 w-4" />
                          Mark Failed
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="requests">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ClipboardList className="h-4 w-4 text-purple-400" />
                Collaboration Requests
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[420px]">
                <div className="divide-y divide-border">
                  {loading && (
                    <div className="p-4 text-sm text-muted-foreground">Loading requests...</div>
                  )}
                  {!loading && filteredRequests.length === 0 && (
                    <div className="p-4 text-sm text-muted-foreground">No requests in queue.</div>
                  )}
                  {filteredRequests.map((req) => (
                    <div key={req.request_id} className="px-5 py-4 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium">{req.artifact_type}</p>
                          <p className="text-xs text-muted-foreground">
                            {req.from_team} → {req.to_team}
                          </p>
                        </div>
                        <Badge className={`border ${statusStyles[req.status] || statusStyles.open}`}>{req.status}</Badge>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span>Priority: {req.priority}</span>
                        <span>Due: {req.due_by || "n/a"}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => respondRequest(req.request_id, "fulfilled")}
                          data-testid={`agent-request-fulfill-${req.request_id}`}
                        >
                          Fulfill
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => respondRequest(req.request_id, "blocked")}
                          data-testid={`agent-request-block-${req.request_id}`}
                        >
                          Block
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentTaskQueue;
