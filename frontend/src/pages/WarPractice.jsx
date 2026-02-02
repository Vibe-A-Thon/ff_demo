import React, { useMemo, useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { ScrollArea } from "../components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../components/ui/collapsible";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { battleAPI, runAPI, workflowAPI, agentAPI } from "../lib/api";
import {
  Crosshair,
  Swords,
  Shield,
  AlertTriangle,
  Activity,
  FlaskConical,
  Play,
  Pause,
  RotateCcw,
  FileUp,
  Sliders,
  Snowflake,
  Undo2,
  RefreshCcw,
  ChevronDown,
} from "lucide-react";

const SCENARIO_PRESETS = [
  "ATO Burst",
  "P2P Mule Fan-Out",
  "ACH Payroll Diversion",
  "Card Testing Wave",
  "Wire BEC Urgent",
];

const RAILS = ["Cards", "ACH", "Wire", "Instant Payments", "Checks", "Lending"];

const DECISION_MODES = ["Auto (Blue) Decision", "Manual Review Queue", "Hold / Step-Up", "Simulate Miss"];

const WarPractice = () => {
  const navigate = useNavigate();
  const [scenarioName, setScenarioName] = useState("Manual Simulation");
  const [preset, setPreset] = useState("ATO Burst");
  const [attackComplexity, setAttackComplexity] = useState([6]);
  const [velocity, setVelocity] = useState([42]);
  const [stealth, setStealth] = useState([55]);
  const [lossTarget, setLossTarget] = useState("75000");
  const [turns, setTurns] = useState([12]);
  const [rail, setRail] = useState("ACH");
  const [decisionMode, setDecisionMode] = useState("Auto (Blue) Decision");
  const [geoSpread, setGeoSpread] = useState([3]);
  const [muleDensity, setMuleDensity] = useState([4]);
  const [deviceRisk, setDeviceRisk] = useState(true);
  const [identitySpoof, setIdentitySpoof] = useState(true);
  const [cooldownBypass, setCooldownBypass] = useState(false);
  const [sandboxOnly, setSandboxOnly] = useState(true);
  const [streamThinking, setStreamThinking] = useState(true);
  const [uploadFileName, setUploadFileName] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [workflowRunId, setWorkflowRunId] = useState("");
  const [workflowState, setWorkflowState] = useState("incident_created");
  const [workflowStatus, setWorkflowStatus] = useState("idle");
  const [workflowHistory, setWorkflowHistory] = useState([]);
  const [workflowApprovalRequired, setWorkflowApprovalRequired] = useState(false);
  const [governanceStatus, setGovernanceStatus] = useState(null);
  const [workflowApprovals, setWorkflowApprovals] = useState([]);
  const [workflowBusy, setWorkflowBusy] = useState(false);
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [runEvents, setRunEvents] = useState([]);
  const [selectedStageKey, setSelectedStageKey] = useState("");
  const [stageTeamFilter, setStageTeamFilter] = useState("all");
  const [stageAgentFilter, setStageAgentFilter] = useState("all");

  const estimatedRisk = useMemo(() => {
    const base = attackComplexity[0] * 6 + velocity[0] * 0.6 + muleDensity[0] * 7;
    const stealthFactor = 100 - stealth[0];
    return Math.min(98, Math.round(base / 3 + stealthFactor / 4));
  }, [attackComplexity, velocity, muleDensity, stealth]);

  const approvalSummary = useMemo(() => {
    const approvals = workflowApprovals || [];
    return {
      pending: approvals.filter((item) => item.status === "pending").length,
      approved: approvals.filter((item) => item.status === "approved").length,
      rejected: approvals.filter((item) => item.status === "rejected").length,
      total: approvals.length,
    };
  }, [workflowApprovals]);

  useEffect(() => {
    const loadRegistry = async () => {
      try {
        const response = await agentAPI.getRegistry();
        setRegistrySnapshot(response?.data || null);
      } catch (error) {
        setRegistrySnapshot(null);
      }
    };
    loadRegistry();
  }, []);

  const handleStart = async () => {
    setIsRunning(true);
    try {
      const response = await battleAPI.create({
        scenario_name: scenarioName,
        parameters: {
          preset,
          rail,
          decision_mode: decisionMode,
          attack_complexity: attackComplexity[0],
          velocity: velocity[0],
          stealth: stealth[0],
          turns: turns[0],
          geo_spread: geoSpread[0],
          mule_density: muleDensity[0],
          loss_target: Number(lossTarget || 0),
          device_risk: deviceRisk,
          identity_spoof: identitySpoof,
          cooldown_bypass: cooldownBypass,
          sandbox_only: sandboxOnly,
          stream_thinking: streamThinking,
          playbook_file: uploadFileName,
        },
      });
      const battleId = response?.data?.id;
      if (battleId) {
        await battleAPI.start(battleId);
        toast.success("Manual simulation started. Redirecting to War Room.");
        navigate("/war-room", { state: { battleId } });
      } else {
        toast.success("Manual simulation started. Blue team pipeline engaged.");
      }
    } catch (error) {
      toast.error("Failed to start manual simulation.");
      setIsRunning(false);
    }
  };

  const handlePause = () => {
    setIsRunning(false);
    toast("Simulation paused. Awaiting operator action.");
  };

  const handleReset = () => {
    setIsRunning(false);
    toast("Scenario reset to draft state.");
  };

  const handleQueueBattle = async () => {
    try {
      const response = await battleAPI.create({
        scenario_name: scenarioName,
        parameters: {
          preset,
          rail,
          decision_mode: decisionMode,
          attack_complexity: attackComplexity[0],
          velocity: velocity[0],
          stealth: stealth[0],
          turns: turns[0],
          geo_spread: geoSpread[0],
          mule_density: muleDensity[0],
          loss_target: Number(lossTarget || 0),
          device_risk: deviceRisk,
          identity_spoof: identitySpoof,
          cooldown_bypass: cooldownBypass,
          sandbox_only: sandboxOnly,
          stream_thinking: streamThinking,
          playbook_file: uploadFileName,
        },
      });
      const battleId = response?.data?.id;
      toast.success("Queued in War Room as manual red-team practice.");
      if (battleId) {
        navigate("/war-room", { state: { battleId } });
      }
    } catch (error) {
      toast.error("Failed to queue practice battle.");
    }
  };

  const refreshRunEvents = useCallback(async (runId) => {
    if (!runId) return;
    try {
      const response = await runAPI.get(runId);
      setRunEvents(response?.data?.events || []);
    } catch (error) {
      console.error("Failed to load run events:", error);
    }
  }, []);

  const syncWorkflow = useCallback(async (runId) => {
    if (!runId) return;
    try {
      const [workflowResponse, statusResponse, approvalsResponse] = await Promise.all([
        workflowAPI.get(runId),
        workflowAPI.getStatus(runId),
        workflowAPI.getApprovals(runId),
      ]);
      const data = workflowResponse?.data;
      if (data) {
        setWorkflowState(data.workflow_state || "incident_created");
        setWorkflowStatus(data.workflow_status || "running");
        setWorkflowApprovalRequired(Boolean(data.approval_required));
        setWorkflowHistory(data.workflow_history || []);
      }
      const statusData = statusResponse?.data;
      setGovernanceStatus(statusData?.governance || null);
      const approvalsData = approvalsResponse?.data;
      setWorkflowApprovals(approvalsData?.approvals || []);
      await refreshRunEvents(runId);
    } catch (error) {
      console.error("Failed to sync workflow:", error);
    }
  }, [refreshRunEvents]);

  useEffect(() => {
    if (!workflowRunId) return;
    syncWorkflow(workflowRunId);
    const interval = setInterval(() => {
      syncWorkflow(workflowRunId);
    }, 5000);
    return () => clearInterval(interval);
  }, [workflowRunId, syncWorkflow]);

  const stageOutputsByStage = useMemo(() => {
    return (runEvents || []).reduce((acc, event) => {
      if (!["agent.output", "orchestrator.output"].includes(event.event_type)) return acc;
      const payload = event.payload || {};
      const stageKey = String(payload.stage || event.stage || "unknown");
      const team = (payload.team || (event.event_type === "orchestrator.output" ? "orchestrator" : "system")).toLowerCase();
      const agent = payload.agent || payload.agent_id || payload.agent_name || "";
      if (!acc[stageKey]) acc[stageKey] = { items: [] };
      acc[stageKey].items.push({
        id: `${stageKey}-${acc[stageKey].items.length}`,
        team,
        agent,
        payload,
        eventType: event.event_type,
        created_at: event.created_at,
      });
      return acc;
    }, {});
  }, [runEvents]);

  const stageKeys = useMemo(() => Object.keys(stageOutputsByStage).sort(), [stageOutputsByStage]);

  useEffect(() => {
    if (!selectedStageKey && stageKeys.length) {
      setSelectedStageKey(stageKeys[stageKeys.length - 1]);
    }
  }, [stageKeys, selectedStageKey]);

  const selectedStageItems = stageOutputsByStage[selectedStageKey]?.items || [];
  const availableStageTeams = Array.from(new Set(selectedStageItems.map((item) => item.team))).filter(Boolean);
  const availableStageAgents = Array.from(new Set(selectedStageItems.map((item) => item.agent))).filter(Boolean);
  const filteredStageItems = selectedStageItems.filter((item) => {
    if (stageTeamFilter !== "all" && item.team !== stageTeamFilter) return false;
    if (stageAgentFilter !== "all" && item.agent !== stageAgentFilter) return false;
    return true;
  });

  const formatOutput = (outputs) => {
    if (!outputs) return "No output yet.";
    if (typeof outputs === "string") return outputs;
    try {
      return JSON.stringify(outputs, null, 2);
    } catch (error) {
      return String(outputs);
    }
  };

  const handleLifecycleAutoRun = async () => {
    setWorkflowBusy(true);
    try {
      let runId = workflowRunId;
      if (!runId) {
        const startResponse = await runAPI.start({ scenario_id: scenarioName || "demo", mode: "auto" });
        runId = startResponse?.data?.id;
        setWorkflowRunId(runId || "");
      }
      if (!runId) {
        toast.error("Failed to create workflow run");
        setWorkflowBusy(false);
        return;
      }
      const autoResponse = await workflowAPI.autoRun(runId, {
        actor_id: "current-user",
        max_steps: 25,
      });
      const data = autoResponse?.data;
      setWorkflowState(data?.workflow_state || "incident_created");
      setWorkflowStatus(data?.workflow_status || "running");
      setWorkflowApprovalRequired(Boolean(data?.approval_required));
      if (data?.transitions?.length) {
        setWorkflowHistory((prev) => [...prev, ...data.transitions]);
      }
      await syncWorkflow(runId);
      toast.success("Lifecycle workflow auto-run complete");
    } catch (error) {
      toast.error("Failed to auto-run lifecycle workflow");
    } finally {
      setWorkflowBusy(false);
    }
  };

  const handleWorkflowAdvance = async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.advance(workflowRunId, {
        actor_id: "current-user",
        mode: "manual",
      });
      const data = response?.data;
      setWorkflowState(data?.workflow_state || workflowState);
      if (data?.transitions?.length) {
        setWorkflowHistory((prev) => [...prev, ...data.transitions]);
      }
      await syncWorkflow(workflowRunId);
      toast.success("Workflow advanced");
    } catch (error) {
      toast.error("Failed to advance workflow");
    } finally {
      setWorkflowBusy(false);
    }
  };

  const handleWorkflowRefresh = async () => {
    try {
      await syncWorkflow(workflowRunId);
    } catch (error) {
      toast.error("Failed to refresh workflow state");
    }
  };

  const handleWorkflowFreeze = async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.freeze(workflowRunId, {
        actor_id: "current-user",
        notes: "Freeze issued from War Practice",
      });
      const data = response?.data;
      setWorkflowState(data?.workflow_state || "frozen");
      setWorkflowStatus(data?.workflow_status || "frozen");
      await syncWorkflow(workflowRunId);
      toast.success("Workflow frozen");
    } catch (error) {
      toast.error("Failed to freeze workflow");
    } finally {
      setWorkflowBusy(false);
    }
  };

  const handleWorkflowRollback = async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.rollback(workflowRunId, {
        actor_id: "current-user",
        notes: "Rollback issued from War Practice",
      });
      const data = response?.data;
      setWorkflowState(data?.workflow_state || "rolled_back");
      setWorkflowStatus(data?.workflow_status || "completed");
      await syncWorkflow(workflowRunId);
      toast.success("Workflow rolled back");
    } catch (error) {
      toast.error("Failed to rollback workflow");
    } finally {
      setWorkflowBusy(false);
    }
  };

  const handleWorkflowReset = async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.reset(workflowRunId, {
        actor_id: "current-user",
        notes: "Reset issued from War Practice",
      });
      const data = response?.data;
      setWorkflowState(data?.workflow_state || "incident_created");
      setWorkflowStatus(data?.workflow_status || "running");
      await syncWorkflow(workflowRunId);
      toast.success("Workflow reset");
    } catch (error) {
      toast.error("Failed to reset workflow");
    } finally {
      setWorkflowBusy(false);
    }
  };

  useEffect(() => {
    if (workflowRunId) {
      syncWorkflow(workflowRunId);
    } else {
      setGovernanceStatus(null);
      setWorkflowApprovals([]);
    }
  }, [workflowRunId, syncWorkflow]);

  const governanceBadgeClass = (status) => {
    if (status === "SAFE_TO_PROCEED") return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30";
    if (status === "PROCEED_WITH_REVIEW") return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30";
    if (status === "FREEZE_RELEASES") return "bg-red-500/15 text-red-300 border border-red-500/30";
    return "bg-slate-500/15 text-slate-200 border border-slate-500/30";
  };

  return (
    <div className="flex h-full flex-col gap-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Crosshair className="h-4 w-4 text-red-400" />
            Red Team Manual Simulation
          </div>
          <h1 className="text-2xl font-semibold text-white">War Practice Console</h1>
          <p className="text-sm text-muted-foreground">
            Configure a manual fraud scenario as Red Team. Blue team auto-runs detection and the standard
            approval workflow stays intact.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge className="bg-red-500/20 text-red-300">Red Operator</Badge>
          <Badge className="bg-blue-500/20 text-blue-300">Blue Auto-Detect</Badge>
          <Badge className="bg-emerald-500/20 text-emerald-300">Sandbox Mode</Badge>
        </div>
      </div>

      <Card className="border-border" data-testid="war-practice-registry">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">Registry Snapshot</CardTitle>
          <Badge variant="outline" className="border-border">
            {registrySnapshot?.agents?.length || 0} agents
          </Badge>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-muted-foreground">
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="border-border">
              {registrySnapshot?.teams?.length || 0} teams
            </Badge>
            <Badge variant="outline" className="border-border">
              {(registrySnapshot?.delegation_preview || []).length} on deck
            </Badge>
          </div>
          <div className="grid gap-2 md:grid-cols-3">
            {(registrySnapshot?.delegation_preview || []).slice(0, 3).map((item) => (
              <div key={item.agent_id} className="rounded-md border border-border bg-zinc-900/40 p-3">
                <div className="text-white text-xs font-medium">{item.agent_name}</div>
                <div className="text-[11px] text-muted-foreground">{item.role}</div>
              </div>
            ))}
            {!registrySnapshot?.delegation_preview?.length && (
              <div className="text-xs text-muted-foreground">Registry data not available.</div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <Card className="border-border">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Scenario Setup</CardTitle>
                <p className="text-xs text-muted-foreground">Define the attack narrative and payload scope.</p>
              </div>
              <Badge className="bg-red-500/15 text-red-300">Manual Mode</Badge>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="scenario-name">Scenario name</Label>
                <Input
                  id="scenario-name"
                  value={scenarioName}
                  onChange={(event) => setScenarioName(event.target.value)}
                  data-testid="war-practice-scenario-name"
                />
              </div>
              <div className="space-y-2">
                <Label>Preset</Label>
                <Select value={preset} onValueChange={setPreset}>
                  <SelectTrigger data-testid="war-practice-preset">
                    <SelectValue placeholder="Select preset" />
                  </SelectTrigger>
                  <SelectContent>
                    {SCENARIO_PRESETS.map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Primary payment rail</Label>
                <Select value={rail} onValueChange={setRail}>
                  <SelectTrigger data-testid="war-practice-rail">
                    <SelectValue placeholder="Select rail" />
                  </SelectTrigger>
                  <SelectContent>
                    {RAILS.map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="loss-target">Target exposure ($)</Label>
                <Input
                  id="loss-target"
                  type="number"
                  value={lossTarget}
                  onChange={(event) => setLossTarget(event.target.value)}
                  data-testid="war-practice-loss-target"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Scenario upload (optional JSON playbook)</Label>
                <div className="flex items-center gap-3">
                  <Input
                    type="file"
                    onChange={(event) => setUploadFileName(event.target.files?.[0]?.name || "")}
                    data-testid="war-practice-file"
                  />
                  <Badge variant="outline" className="text-xs">
                    {uploadFileName || "No file selected"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Attack Parameters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Attack complexity</Label>
                  <span className="text-xs text-muted-foreground">{attackComplexity[0]}/10</span>
                </div>
                <Slider
                  value={attackComplexity}
                  onValueChange={setAttackComplexity}
                  max={10}
                  step={1}
                  data-testid="war-practice-complexity"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Velocity (tx/min)</Label>
                  <span className="text-xs text-muted-foreground">{velocity[0]}</span>
                </div>
                <Slider
                  value={velocity}
                  onValueChange={setVelocity}
                  max={120}
                  step={2}
                  data-testid="war-practice-velocity"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Stealth factor</Label>
                  <span className="text-xs text-muted-foreground">{stealth[0]}%</span>
                </div>
                <Slider
                  value={stealth}
                  onValueChange={setStealth}
                  max={100}
                  step={5}
                  data-testid="war-practice-stealth"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Simulation turns</Label>
                  <span className="text-xs text-muted-foreground">{turns[0]} turns</span>
                </div>
                <Slider
                  value={turns}
                  onValueChange={setTurns}
                  max={30}
                  step={1}
                  data-testid="war-practice-turns"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label>Geo spread</Label>
                  <Slider
                    value={geoSpread}
                    onValueChange={setGeoSpread}
                    max={8}
                    step={1}
                    data-testid="war-practice-geo"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Mule density</Label>
                  <Slider
                    value={muleDensity}
                    onValueChange={setMuleDensity}
                    max={10}
                    step={1}
                    data-testid="war-practice-mule"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Decision mode</Label>
                  <Select value={decisionMode} onValueChange={setDecisionMode}>
                    <SelectTrigger data-testid="war-practice-decision">
                      <SelectValue placeholder="Select decision mode" />
                    </SelectTrigger>
                    <SelectContent>
                      {DECISION_MODES.map((item) => (
                        <SelectItem key={item} value={item}>
                          {item}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Identity & Channel Controls</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">Device risk emulation</p>
                  <p className="text-xs text-muted-foreground">Simulate risky device posture signals.</p>
                </div>
                <Switch
                  checked={deviceRisk}
                  onCheckedChange={setDeviceRisk}
                  data-testid="war-practice-device-risk"
                />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">Identity spoofing</p>
                  <p className="text-xs text-muted-foreground">Inject KYC mismatch / spoof signals.</p>
                </div>
                <Switch
                  checked={identitySpoof}
                  onCheckedChange={setIdentitySpoof}
                  data-testid="war-practice-identity-spoof"
                />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">Cooldown bypass attempts</p>
                  <p className="text-xs text-muted-foreground">Attempt to override cooling-off windows.</p>
                </div>
                <Switch
                  checked={cooldownBypass}
                  onCheckedChange={setCooldownBypass}
                  data-testid="war-practice-cooldown-bypass"
                />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">Sandbox-only execution</p>
                  <p className="text-xs text-muted-foreground">Keep execution in a safe isolated lab.</p>
                </div>
                <Switch
                  checked={sandboxOnly}
                  onCheckedChange={setSandboxOnly}
                  data-testid="war-practice-sandbox"
                />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border p-3 md:col-span-2">
                <div>
                  <p className="text-sm font-medium">Stream thinking visualizer</p>
                  <p className="text-xs text-muted-foreground">Show staged reasoning during run.</p>
                </div>
                <Switch
                  checked={streamThinking}
                  onCheckedChange={setStreamThinking}
                  data-testid="war-practice-streaming"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Operational Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Button
                  className="gap-2"
                  onClick={handleStart}
                  data-testid="war-practice-start"
                >
                  <Play className="h-4 w-4" />
                  Start
                </Button>
                <Button
                  variant="secondary"
                  className="gap-2"
                  onClick={handlePause}
                  data-testid="war-practice-pause"
                >
                  <Pause className="h-4 w-4" />
                  Pause
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={handleReset}
                  data-testid="war-practice-reset"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={handleQueueBattle}
                  data-testid="war-practice-queue"
                >
                  <Swords className="h-4 w-4" />
                  Queue Battle
                </Button>
              </div>
              <div className="rounded-md border border-border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-blue-400" />
                    <span className="text-sm font-medium">Blue Team Pipeline</span>
                  </div>
                  <Badge className={isRunning ? "bg-blue-500/20 text-blue-300" : "bg-muted text-muted-foreground"}>
                    {isRunning ? "Active" : "Idle"}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Detection runs automatically after each manual action. Outputs flow into the approvals queue.
                </p>
              </div>
              <div className="rounded-md border border-border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-400" />
                    <span className="text-sm font-medium">Safety Guardrails</span>
                  </div>
                  <Badge className="bg-emerald-500/20 text-emerald-300">Synthetic Only</Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  All exports are watermarked and restricted to synthetic simulation data.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border" data-testid="lifecycle-workflow-panel">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Lifecycle Workflow</CardTitle>
              <div className="flex items-center gap-2">
                {workflowApprovalRequired && (
                  <Badge className="bg-yellow-500/15 text-yellow-300 border border-yellow-500/30">
                    Approval Required
                  </Badge>
                )}
                {workflowRunId && (
                  <Badge className={governanceBadgeClass(governanceStatus?.status)}>
                    {(governanceStatus?.status || "Governance").replace(/_/g, " ")}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md border border-border p-3 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Run ID</span>
                  <span className="text-white truncate max-w-[180px]">
                    {workflowRunId || "Not started"}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>State</span>
                  <Badge className="bg-slate-500/15 text-slate-200 border border-slate-500/30">
                    {workflowState}
                  </Badge>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>Status</span>
                  <Badge className={workflowStatus === "awaiting_approval" ? "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30" : "bg-blue-500/15 text-blue-300 border border-blue-500/30"}>
                    {workflowStatus}
                  </Badge>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>Governance</span>
                  <Badge className={governanceBadgeClass(governanceStatus?.status)}>
                    {(governanceStatus?.status || "—").replace(/_/g, " ")}
                  </Badge>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>Approvals</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30">
                      Pending {approvalSummary.pending}
                    </Badge>
                    <Badge className="bg-red-500/15 text-red-300 border border-red-500/30">
                      Rejected {approvalSummary.rejected}
                    </Badge>
                  </div>
                </div>
                {workflowApprovalRequired && (
                  <div className="mt-2 text-yellow-300">Approval required to proceed.</div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                <Button
                  className="gap-2"
                  onClick={handleLifecycleAutoRun}
                  disabled={workflowBusy}
                  data-testid="workflow-auto-run"
                >
                  <Play className="h-4 w-4" />
                  Auto-Run
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={handleWorkflowAdvance}
                  disabled={workflowBusy}
                  data-testid="workflow-advance"
                >
                  <RotateCcw className="h-4 w-4" />
                  Advance
                </Button>
                <Button
                  variant="destructive"
                  className="gap-2"
                  onClick={handleWorkflowFreeze}
                  disabled={!workflowRunId || workflowBusy}
                  data-testid="workflow-freeze"
                >
                  <Snowflake className="h-4 w-4" />
                  Freeze
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={handleWorkflowRollback}
                  disabled={!workflowRunId || workflowBusy}
                  data-testid="workflow-rollback"
                >
                  <Undo2 className="h-4 w-4" />
                  Rollback
                </Button>
                <Button
                  variant="secondary"
                  className="gap-2"
                  onClick={handleWorkflowReset}
                  disabled={!workflowRunId || workflowBusy}
                  data-testid="workflow-reset"
                >
                  <RefreshCcw className="h-4 w-4" />
                  Reset
                </Button>
                <Button
                  variant="secondary"
                  className="gap-2 col-span-2 md:col-span-3"
                  onClick={handleWorkflowRefresh}
                  disabled={!workflowRunId}
                  data-testid="workflow-refresh"
                >
                  Refresh State
                </Button>
              </div>
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground">Recent transitions</p>
                <ScrollArea className="h-24 pr-3">
                  <ul className="mt-2 space-y-2 text-xs text-muted-foreground">
                    {(workflowHistory || []).slice(-5).map((item, idx) => (
                      <li key={`${item.state}-${idx}`} className="flex items-center justify-between">
                        <span className="text-white">{item.state}</span>
                        <span>{item.timestamp?.slice(11, 19)}</span>
                      </li>
                    ))}
                  </ul>
                </ScrollArea>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Run Telemetry Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-md border border-border p-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Activity className="h-3 w-3" /> Estimated risk
                  </div>
                  <div className="mt-2 text-2xl font-semibold text-red-300">{estimatedRisk}%</div>
                </div>
                <div className="rounded-md border border-border p-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <FlaskConical className="h-3 w-3" /> Expected detection
                  </div>
                  <div className="mt-2 text-2xl font-semibold text-blue-300">{Math.max(15, 100 - estimatedRisk)}%</div>
                </div>
              </div>
              <div className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Scenario rail coverage</span>
                  <Badge variant="outline" className="text-xs">{rail}</Badge>
                </div>
                <div className="mt-2 text-sm text-white">{preset} • {turns[0]} turns</div>
                <p className="text-xs text-muted-foreground">Loss target: ${Number(lossTarget || 0).toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Manual Run Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-48 pr-3">
                <ul className="space-y-3 text-sm">
                  {[
                    "Confirm synthetic-only dataset",
                    "Verify scenario parameters",
                    "Arm detection thresholds",
                    "Enable audit logging",
                    "Run through approvals queue",
                  ].map((item) => (
                    <li key={item} className="flex items-center justify-between rounded-md border border-border p-2">
                      <span>{item}</span>
                      <Badge variant="outline" className="text-xs">Pending</Badge>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="border-border" data-testid="war-practice-stage-outputs">
            <CardHeader className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle className="text-base">Stage Outputs Detail</CardTitle>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={selectedStageKey}
                  onValueChange={setSelectedStageKey}
                  disabled={!stageKeys.length}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select stage" />
                  </SelectTrigger>
                  <SelectContent>
                    {stageKeys.map((stage) => (
                      <SelectItem key={stage} value={stage}>
                        {stage}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={stageTeamFilter} onValueChange={setStageTeamFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Team" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All teams</SelectItem>
                    {availableStageTeams.map((team) => (
                      <SelectItem key={team} value={team}>
                        {team}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={stageAgentFilter}
                  onValueChange={setStageAgentFilter}
                  disabled={!availableStageAgents.length}
                >
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Agent" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All agents</SelectItem>
                    {availableStageAgents.map((agent) => (
                      <SelectItem key={agent} value={agent}>
                        {agent}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="grid gap-3">
              {filteredStageItems.length ? (
                filteredStageItems.map((item, idx) => (
                  <Collapsible key={item.id} defaultOpen={idx === 0}>
                    <CollapsibleTrigger className="flex w-full items-center justify-between rounded border border-border bg-black/30 px-2 py-1 text-xs">
                      <span className="text-muted-foreground">
                        {item.team} {item.agent ? `• ${item.agent}` : ""}
                      </span>
                      <ChevronDown className="h-3 w-3" />
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <ScrollArea className="h-40 rounded border border-border bg-black/40 p-2 mt-2">
                        <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                          {formatOutput(item.payload)}
                        </pre>
                      </ScrollArea>
                    </CollapsibleContent>
                  </Collapsible>
                ))
              ) : (
                <div className="text-xs text-muted-foreground">
                  {stageKeys.length
                    ? "No outputs match the selected filters."
                    : "Start a lifecycle run to capture orchestrator outputs per stage."}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-border">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Blue Team Response Feed (Preview)</CardTitle>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Sliders className="h-4 w-4" /> Auto-detection enabled
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-md border border-border p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Shield className="h-4 w-4 text-blue-400" /> Decision
            </div>
            <p className="mt-2 text-2xl font-semibold text-blue-300">
              {decisionMode.includes("Simulate Miss") ? "Allowed" : "Review"}
            </p>
            <p className="text-xs text-muted-foreground">Based on current manual parameters.</p>
          </div>
          <div className="rounded-md border border-border p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Activity className="h-4 w-4 text-emerald-400" /> Risk Score
            </div>
            <p className="mt-2 text-2xl font-semibold text-emerald-300">{estimatedRisk}</p>
            <p className="text-xs text-muted-foreground">Blue detection confidence window.</p>
          </div>
          <div className="rounded-md border border-border p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <FileUp className="h-4 w-4 text-yellow-300" /> Evidence Pack
            </div>
            <p className="mt-2 text-sm text-muted-foreground">Evidence will be generated after run completion.</p>
            <Button variant="outline" size="sm" className="mt-3" data-testid="war-practice-evidence">
              Generate draft evidence
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WarPractice;
