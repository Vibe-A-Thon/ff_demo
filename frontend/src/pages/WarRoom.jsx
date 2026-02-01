import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useLocation } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Progress } from "../components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { battleAPI, aiAPI, createBattleWebSocket, runAPI, workflowAPI, agentAPI, ragAPI, settingsAPI, llmAPI } from "../lib/api";
import { useAlerts } from "../contexts/AlertContext";
import { toast } from "sonner";
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Zap,
  Shield,
  Sword,
  Activity,
  DollarSign,
  Clock,
  Brain,
  AlertTriangle,
  Radio,
  Wifi,
  WifiOff,
  Bell,
  BellOff,
  FastForward,
  Rewind,
  Snowflake,
  Undo2,
  RefreshCcw,
  Sparkles,
} from "lucide-react";

// Thinking Visualizer Component with Streaming
const ThinkingVisualizer = ({ team, thinking, isStreaming, streamingText }) => {
  const stages = ["Recon", "Ideation", "Evaluation", "Action"];
  const currentStage = thinking ? stages.findIndex(s => thinking.includes(s)) : -1;
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current && isStreaming) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thinking, streamingText, isStreaming]);

  return (
    <div className={`rounded-lg border p-4 h-full flex flex-col ${team === 'red' ? 'border-red-500/30 gradient-red' : 'border-blue-500/30 gradient-blue'}`}>
      <div className="flex items-center gap-2 mb-3">
        {team === 'red' ? <Sword className="h-4 w-4 text-red-400" /> : <Shield className="h-4 w-4 text-blue-400" />}
        <span className={`text-sm font-semibold ${team === 'red' ? 'text-red-400' : 'text-blue-400'}`}>
          {team === 'red' ? 'RED TEAM' : 'BLUE TEAM'} THINKING
        </span>
        {isStreaming && (
          <div className="flex items-center gap-1 ml-auto">
            <Radio className="h-3 w-3 text-green-400 animate-pulse" />
            <span className="text-xs text-green-400">LIVE</span>
          </div>
        )}
      </div>

      {/* Stage Progress */}
      <div className="flex gap-1 mb-4">
        {stages.map((stage, idx) => (
          <div key={stage} className="flex-1">
            <div className={`h-1 rounded-full transition-all duration-300 ${idx <= currentStage ? (team === 'red' ? 'bg-red-500' : 'bg-blue-500') : 'bg-zinc-700'}`} />
            <span className="text-xs text-muted-foreground mt-1 block">{stage}</span>
          </div>
        ))}
      </div>

      {/* Thinking Stream */}
      <div 
        ref={scrollRef}
        className="font-mono text-sm bg-black/30 rounded p-3 flex-1 overflow-auto min-h-[120px]"
      >
        {thinking || streamingText ? (
          <div className="whitespace-pre-wrap">
            {thinking}
            {isStreaming && streamingText && (
              <span className="text-green-400">{streamingText}</span>
            )}
            {isStreaming && <span className="cursor-blink">▋</span>}
          </div>
        ) : (
          <span className="text-muted-foreground">Waiting for battle to start...</span>
        )}
      </div>
    </div>
  );
};

// Battle Timeline Component
const BattleTimeline = ({ turns, currentTurn, onJumpTo, onHoverTurn }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current && turns.length > 0) {
      const activeElement = scrollRef.current.querySelector(`[data-turn="${turns.length - 1}"]`);
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [turns.length]);

  return (
    <ScrollArea className="h-full" ref={scrollRef}>
      <div className="space-y-2 p-2">
        {turns.map((turn, idx) => (
          <div
            key={idx}
            data-turn={idx}
            onClick={() => onJumpTo(idx)}
            onMouseEnter={() => onHoverTurn?.(idx)}
            onMouseLeave={() => onHoverTurn?.(null)}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
              idx === currentTurn 
                ? 'border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/10' 
                : 'border-border bg-card hover:bg-zinc-800'
            }`}
            data-testid={`turn-${idx}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono ${
              idx === currentTurn ? 'bg-blue-500 text-white' : 'bg-zinc-800'
            }`}>
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={turn.red_team?.success ? 'border-red-500 text-red-400' : 'border-zinc-600'}>
                  <Sword className="h-3 w-3 mr-1" />
                  {turn.red_team?.action?.slice(0, 15) || 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className={turn.blue_team?.blocked ? 'border-blue-500 text-blue-400' : 'border-zinc-600'}>
                  <Shield className="h-3 w-3 mr-1" />
                  {turn.blue_team?.action?.slice(0, 15) || 'N/A'}
                </Badge>
              </div>
            </div>
            {turn.red_team?.success ? (
              <AlertTriangle className="h-4 w-4 text-red-400" />
            ) : (
              <Shield className="h-4 w-4 text-green-400" />
            )}
          </div>
        ))}
        {turns.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            No turns yet. Start the battle!
          </div>
        )}
      </div>
    </ScrollArea>
  );
};

// Metrics Strip Component with Alert Indicators
const MetricsStrip = ({ metrics, onMetricClick }) => {
  const items = [
    { 
      key: "success_rate",
      label: "Success Rate", 
      value: `${metrics.success_rate || 0}%`, 
      icon: Activity, 
      color: "text-green-400",
      alert: (metrics.success_rate || 0) < 60 ? 'critical' : (metrics.success_rate || 0) < 75 ? 'warning' : null
    },
    { 
      key: "money_at_risk",
      label: "Money at Risk", 
      value: `$${(metrics.money_at_risk || 0).toLocaleString()}`, 
      icon: DollarSign, 
      color: "text-red-400",
      alert: (metrics.money_at_risk || 0) > 40000 ? 'critical' : (metrics.money_at_risk || 0) > 25000 ? 'warning' : null
    },
    { 
      key: "money_saved",
      label: "Money Saved", 
      value: `$${(metrics.money_saved || 0).toLocaleString()}`, 
      icon: Shield, 
      color: "text-green-400",
      alert: null
    },
    { 
      key: "time_to_immunity",
      label: "Time to Immunity", 
      value: `${metrics.time_to_immunity || 0}m`, 
      icon: Clock, 
      color: "text-blue-400",
      alert: (metrics.time_to_immunity || 0) > 8 ? 'critical' : (metrics.time_to_immunity || 0) > 5 ? 'warning' : null
    },
    { 
      key: "patterns_learned",
      label: "Patterns Learned", 
      value: metrics.patterns_learned || 0, 
      icon: Brain, 
      color: "text-purple-400",
      alert: null
    },
  ];

  return (
    <div className="grid grid-cols-5 gap-4 p-4 border-b border-border bg-card glass-panel">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.key}
            type="button"
            onClick={() => onMetricClick?.(item)}
            className={`flex items-center gap-3 p-2 rounded-lg transition-all text-left ${
              item.alert === 'critical' ? 'bg-red-500/10 border border-red-500/30 animate-pulse' :
              item.alert === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/30' : 'border border-transparent'
            } hover:border-zinc-600 hover:bg-zinc-800/60`}
            data-testid={`metric-${item.label.toLowerCase().replace(/\s/g, '-')}`}
          >
            <div className={`p-2 rounded-lg bg-zinc-800 ${item.color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                {item.label}
                {item.alert && <AlertTriangle className={`h-3 w-3 ${item.alert === 'critical' ? 'text-red-400' : 'text-yellow-400'}`} />}
              </p>
              <p className="text-lg font-semibold font-mono">{item.value}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
};

const useAnimatedNumber = (value, duration = 800) => {
  const [displayValue, setDisplayValue] = useState(value || 0);
  const previousValueRef = useRef(value || 0);

  useEffect(() => {
    const from = previousValueRef.current || 0;
    const to = value || 0;
    const startTime = performance.now();

    const tick = (now) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const nextValue = Math.round(from + (to - from) * progress);
      setDisplayValue(nextValue);
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        previousValueRef.current = to;
      }
    };

    requestAnimationFrame(tick);
  }, [value, duration]);

  return displayValue;
};

const WarRoom = () => {
  const location = useLocation();
  const lifecycleAutoRef = useRef(false);
  const initialBattleId = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return location.state?.battleId || params.get("battleId");
  }, [location]);
  const [battles, setBattles] = useState([]);
  const [selectedBattle, setSelectedBattle] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [autoPlay, setAutoPlay] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [speed, setSpeed] = useState([50]);
  const [redThinking, setRedThinking] = useState("");
  const [blueThinking, setBlueThinking] = useState("");
  const [redStreamText, setRedStreamText] = useState("");
  const [blueStreamText, setBlueStreamText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const [workflowRunId, setWorkflowRunId] = useState("");
  const [workflowState, setWorkflowState] = useState("incident_created");
  const [workflowStatus, setWorkflowStatus] = useState("idle");
  const [workflowHistory, setWorkflowHistory] = useState([]);
  const [workflowApprovalRequired, setWorkflowApprovalRequired] = useState(false);
  const [governanceStatus, setGovernanceStatus] = useState(null);
  const [workflowApprovals, setWorkflowApprovals] = useState([]);
  const [workflowBusy, setWorkflowBusy] = useState(false);
  const [runEvents, setRunEvents] = useState([]);
  const [blockedBursts, setBlockedBursts] = useState([]);
  const [scenarioName, setScenarioName] = useState("Custom Scenario");
  const [scenarioSteps, setScenarioSteps] = useState([]);
  const [hoverTurnIndex, setHoverTurnIndex] = useState(null);
  const [activeMetric, setActiveMetric] = useState(null);
  const [traceFilter, setTraceFilter] = useState("all");
  const [traceSearch, setTraceSearch] = useState("");
  const [runSummary, setRunSummary] = useState(null);
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [ragHealth, setRagHealth] = useState(null);
  const [ragSettings, setRagSettings] = useState(null);
  const [llmConfig, setLlmConfig] = useState(null);
  const [llmOverrides, setLlmOverrides] = useState({});
  const [llmTelemetry, setLlmTelemetry] = useState(null);
  const [llmSaving, setLlmSaving] = useState(false);
  const wsRef = useRef(null);
  const autoPlayRef = useRef(null);
  const demoRef = useRef(null);
  const redStreamRef = useRef("");
  const blueStreamRef = useRef("");
  
  const { checkMetrics, alertsEnabled, setAlertsEnabled } = useAlerts();

  const loadLlmConfig = useCallback(async () => {
    try {
      const response = await llmAPI.getConfig();
      setLlmConfig(response.data);
      setLlmOverrides(response.data?.overrides || {});
    } catch (error) {
      console.error("Failed to load LLM config:", error);
    }
  }, []);

  const loadLlmTelemetry = useCallback(async () => {
    try {
      const response = await llmAPI.getTelemetry();
      setLlmTelemetry(response.data);
    } catch (error) {
      console.error("Failed to load LLM telemetry:", error);
    }
  }, []);

  const saveLlmOverrides = useCallback(
    async (nextOverrides) => {
      setLlmSaving(true);
      try {
        const response = await llmAPI.updateConfig(nextOverrides);
        setLlmOverrides(response.data || {});
        toast.success("LLM routing updated");
      } catch (error) {
        toast.error("Failed to update LLM routing");
      } finally {
        setLlmSaving(false);
      }
    },
    []
  );

  const llmModels = useMemo(() => {
    return (llmConfig?.registry || []).sort((a, b) => a.model_id.localeCompare(b.model_id));
  }, [llmConfig]);

  const resolveTeamModel = useCallback(
    (teamId) => {
      const overrides = llmOverrides || {};
      const policy = llmConfig?.policy || {};
      return (
        overrides?.team_defaults?.[teamId] ||
        policy?.team_defaults?.[teamId] ||
        overrides?.global_default ||
        policy?.global_default ||
        ""
      );
    },
    [llmConfig, llmOverrides]
  );

  const resolveModelLabel = useCallback(
    (modelId) => {
      if (!modelId) return "";
      const model = llmModels.find((entry) => entry.model_id === modelId);
      return model ? `${model.model_id} (${model.provider})` : modelId;
    },
    [llmModels]
  );

  const handleTeamModelChange = useCallback(
    (teamId, modelId) => {
      const nextOverrides = {
        ...llmOverrides,
        team_defaults: {
          ...(llmOverrides?.team_defaults || {}),
          [teamId]: modelId,
        },
      };
      saveLlmOverrides(nextOverrides);
    },
    [llmOverrides, saveLlmOverrides]
  );

  const handleSimulateFailure = useCallback(
    (enabled, modelId) => {
      const nextOverrides = {
        ...llmOverrides,
        simulate_failure: {
          enabled: Boolean(enabled),
          model_ids: modelId ? [modelId] : [],
        },
      };
      saveLlmOverrides(nextOverrides);
    },
    [llmOverrides, saveLlmOverrides]
  );

  const loadBattles = useCallback(async () => {
    try {
      const response = await battleAPI.getAll();
      setBattles(response.data);
      if (response.data.length > 0) {
        const match = initialBattleId
          ? response.data.find((battle) => battle.id === initialBattleId)
          : null;
        setSelectedBattle(match || response.data[0]);
      }
    } catch (error) {
      console.error("Failed to load battles:", error);
    }
  }, [initialBattleId]);

  useEffect(() => {
    loadBattles();
    loadLlmConfig();
    loadLlmTelemetry();
    const loadRegistry = async () => {
      try {
        const response = await agentAPI.getRegistry();
        setRegistrySnapshot(response?.data || null);
      } catch (error) {
        setRegistrySnapshot(null);
      }
    };
    loadRegistry();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
      if (demoRef.current) clearTimeout(demoRef.current);
    };
  }, [loadBattles, loadLlmConfig, loadLlmTelemetry]);

  useEffect(() => {
    let interval;
    const loadRagHealth = async () => {
      try {
        const [historyRes, telemetryRes, settingsRes] = await Promise.all([
          ragAPI.evaluationHistory({ limit: 1 }),
          ragAPI.cacheTelemetry({ limit: 20 }),
          settingsAPI.get(),
        ]);
        const latest = historyRes?.data?.items?.[0] || null;
        const telemetry = telemetryRes?.data?.summary || null;
        setRagHealth({ latest, telemetry });
        setRagSettings(settingsRes?.data?.rag || null);
      } catch (error) {
        setRagHealth(null);
        setRagSettings(null);
      }
    };
    loadRagHealth();
    interval = window.setInterval(loadRagHealth, 20000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedBattle?.id) return;
    let isCancelled = false;
    const refreshBattle = async () => {
      try {
        const response = await battleAPI.get(selectedBattle.id);
        if (!isCancelled && response?.data) {
          setSelectedBattle((prev) => ({ ...prev, ...response.data }));
        }
      } catch (error) {
        // ignore transient refresh failures
      }
    };
    refreshBattle();
    const interval = setInterval(refreshBattle, 4000);
    return () => {
      isCancelled = true;
      clearInterval(interval);
    };
  }, [selectedBattle?.id]);

  // Check metrics for alerts whenever they change
  useEffect(() => {
    if (selectedBattle?.metrics) {
      checkMetrics(selectedBattle.metrics);
    }
  }, [selectedBattle?.metrics, checkMetrics]);

  const createNewBattle = async (scenarioOverride = null) => {
    try {
      const scenarioPayload = scenarioOverride || {};
      const scenarioTitle = scenarioPayload.name || `Battle ${battles.length + 1}`;
      const response = await battleAPI.create({
        scenario_name: scenarioTitle,
        parameters: {
          difficulty: "medium",
          max_turns: 20,
          scenario_steps: scenarioPayload.steps || [],
          builder_name: scenarioPayload.name || null,
        },
      });
      setBattles([...battles, response.data]);
      setSelectedBattle(response.data);
      setCurrentTurn(0);
      setRedThinking("");
      setBlueThinking("");
      toast.success("New battle created!");
    } catch (error) {
      toast.error("Failed to create battle");
    }
  };

  const scenarioBlocks = [
    { id: "entry-ato", label: "ATO Entry", type: "entry", description: "Credential + device anomaly" },
    { id: "velocity", label: "Velocity Spike", type: "attack", description: "Rapid burst transfers" },
    { id: "new-payee", label: "New Payee", type: "attack", description: "First-time beneficiary" },
    { id: "geo-shift", label: "Geo Shift", type: "signal", description: "Unusual location" },
    { id: "device-mismatch", label: "Device Mismatch", type: "signal", description: "New fingerprint" },
    { id: "step-up", label: "Step-Up Auth", type: "defense", description: "Trigger MFA" },
    { id: "block", label: "Block Transfer", type: "defense", description: "Hard stop" },
    { id: "review", label: "Escalate Review", type: "defense", description: "Manual review" },
  ];

  const onScenarioDragStart = (block) => (event) => {
    event.dataTransfer.setData("application/json", JSON.stringify(block));
    event.dataTransfer.effectAllowed = "move";
  };

  const onScenarioDrop = (event) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData("application/json");
    if (!raw) return;
    const block = JSON.parse(raw);
    setScenarioSteps((prev) => [...prev, block]);
  };

  const onScenarioDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const removeScenarioStep = (index) => {
    setScenarioSteps((prev) => prev.filter((_, idx) => idx !== index));
  };

  const clearScenario = () => {
    setScenarioSteps([]);
    toast.info("Scenario cleared");
  };

  const createScenarioBattle = async () => {
    if (scenarioSteps.length === 0) {
      toast.error("Add at least one block to the scenario");
      return;
    }
    await createNewBattle({ name: scenarioName, steps: scenarioSteps });
    toast.success("Scenario battle created");
  };

  const connectWebSocket = useCallback(() => {
    if (!selectedBattle) return;
    if (wsRef.current) wsRef.current.close();
    
    try {
      wsRef.current = createBattleWebSocket(selectedBattle.id);
      
      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
        setWsConnected(true);
        toast.success("Real-time connection established", { duration: 2000 });
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "turn_update") {
          setSelectedBattle(prev => ({
            ...prev,
            turns: [...(prev.turns || []), data],
            metrics: data.metrics
          }));
          setCurrentTurn(prev => prev + 1);
          if (data.blue_team?.blocked) {
            const fallbackTurn = (selectedBattle?.turns?.length || 0) + 1;
            triggerBlockedEffect(data.turn_number || fallbackTurn);
          }
        } else if (data.type === "thinking_chunk") {
          // Handle streaming thinking
          if (data.team === "red") {
            setRedStreamText((prev) => {
              const next = prev + data.chunk;
              redStreamRef.current = next;
              return next;
            });
          } else {
            setBlueStreamText((prev) => {
              const next = prev + data.chunk;
              blueStreamRef.current = next;
              return next;
            });
          }
        } else if (data.type === "thinking_complete") {
          if (data.team === "red") {
            setRedThinking((prev) => prev + redStreamRef.current);
            setRedStreamText("");
            redStreamRef.current = "";
          } else {
            setBlueThinking((prev) => prev + blueStreamRef.current);
            setBlueStreamText("");
            blueStreamRef.current = "";
          }
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setWsConnected(false);
      };

      wsRef.current.onclose = () => {
        setWsConnected(false);
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setWsConnected(false);
    }
   }, [selectedBattle, triggerBlockedEffect]);

  const triggerBlockedEffect = useCallback((turnNumber) => {
    const burstId = `${Date.now()}-${turnNumber}`;
    setBlockedBursts((prev) => [...prev, burstId]);
    toast.success(`Attack Blocked! Turn ${turnNumber}`, {
      icon: <Sparkles className="h-4 w-4 text-green-400" />,
      duration: 2000,
    });
    setTimeout(() => {
      setBlockedBursts((prev) => prev.filter((id) => id !== burstId));
    }, 900);
  }, []);

  const startBattle = useCallback(async () => {
    if (!selectedBattle) return;
    try {
      await battleAPI.start(selectedBattle.id);
      setIsRunning(true);
      setSelectedBattle({ ...selectedBattle, status: "running", turns: [] });
      setCurrentTurn(0);
      setRedThinking("");
      setBlueThinking("");
      connectWebSocket();
      toast.success("Battle started!");
    } catch (error) {
      toast.error("Failed to start battle");
    }
  }, [selectedBattle, connectWebSocket]);

  const stopBattle = async () => {
    if (!selectedBattle) return;
    try {
      await battleAPI.stop(selectedBattle.id);
      setIsRunning(false);
      setAutoPlay(false);
      setDemoMode(false);
      if (wsRef.current) wsRef.current.close();
      const completed = { ...selectedBattle, status: "completed" };
      setSelectedBattle(completed);
      setRunSummary({
        battle: completed.scenario_name,
        turns: completed.turns?.length || 0,
        successRate: completed.metrics?.success_rate || 0,
        moneySaved: completed.metrics?.money_saved || 0,
        timeToImmunity: completed.metrics?.time_to_immunity || 0,
        patterns: completed.metrics?.patterns_learned || 0,
      });
      toast.success("Battle stopped!");
    } catch (error) {
      toast.error("Failed to stop battle");
    }
  };

  // Streaming AI thinking simulation
  const streamThinking = useCallback(async (team, turnNum) => {
    const stages = ["Recon", "Ideation", "Evaluation", "Action"];
    const redThoughts = {
      "Recon": "Scanning target perimeter for vulnerabilities...\nIdentifying weak authentication endpoints...",
      "Ideation": "Generating attack vectors:\n- Credential stuffing via leaked DB\n- Session hijacking attempt\n- Device fingerprint spoofing",
      "Evaluation": "Assessing detection probability: 35%\nEstimated success rate: 42%\nRisk/reward ratio: Favorable",
      "Action": "Executing: Velocity-based attack pattern\nTarget: Payment gateway\nMasking techniques: Active"
    };
    const blueThoughts = {
      "Recon": "Monitoring incoming traffic patterns...\nAnalyzing behavioral anomalies...",
      "Ideation": "Defense strategies available:\n- ML model scoring\n- Rule engine activation\n- Device graph correlation",
      "Evaluation": "Threat confidence: 78%\nPattern match score: 0.89\nRecommended action: Block + Challenge",
      "Action": "Deploying countermeasures:\n- Velocity check triggered\n- Risk score elevated\n- Transaction flagged"
    };

    const thoughts = team === "red" ? redThoughts : blueThoughts;
    const setThinking = team === "red" ? setRedThinking : setBlueThinking;
    const setStream = team === "red" ? setRedStreamText : setBlueStreamText;

    setThinking(`\n--- Turn ${turnNum} ---\n`);
    
    for (const stage of stages) {
      setStream(`[${stage.toUpperCase()}]\n`);
      await new Promise(r => setTimeout(r, 200));
      
      const text = thoughts[stage];
      for (let i = 0; i < text.length; i++) {
        setStream(prev => prev + text[i]);
        await new Promise(r => setTimeout(r, 15 + Math.random() * 10));
      }
      
      setThinking(prev => prev + `[${stage.toUpperCase()}]\n${text}\n`);
      setStream("");
      await new Promise(r => setTimeout(r, 300));
    }
  }, []);

  const simulateTurn = useCallback((turnNumber, prevMetrics) => {
    const redActions = ["Account Takeover", "Velocity Attack", "Device Spoofing", "Credential Stuffing", "Social Engineering"];
    const blueActions = ["Pattern Detection", "Velocity Check", "Device Fingerprinting", "ML Score", "Rule Match"];
    const redSuccess = Math.random() < 0.35;

    const moneyAtRisk = Math.floor(5000 + Math.random() * 45000);
    const savedThisTurn = redSuccess ? 0 : Math.floor(moneyAtRisk * (0.6 + Math.random() * 0.3));
    const totalSaved = (prevMetrics.money_saved || 0) + savedThisTurn;

    // Time to immunity decreases over time (learning effect)
    const baseImmunity = Math.max(1, 10 - Math.floor(turnNumber / 3));
    const immunityVariation = Math.random() * 2 - 1;
    const timeToImmunity = Math.max(1, Math.round(baseImmunity + immunityVariation));

    return {
      type: "turn_update",
      turn_number: turnNumber,
      red_team: { action: redActions[Math.floor(Math.random() * redActions.length)], success: redSuccess },
      blue_team: { action: blueActions[Math.floor(Math.random() * blueActions.length)], blocked: !redSuccess },
      metrics: {
        success_rate: Math.floor(65 + Math.random() * 30),
        money_at_risk: moneyAtRisk,
        money_saved: totalSaved,
        time_to_immunity: timeToImmunity,
        patterns_learned: turnNumber
      }
    };
  }, []);

  const runTurn = useCallback(async () => {
    if (!selectedBattle || !isRunning) return;
    
    setIsStreaming(true);
    const turnNum = currentTurn + 1;
    
    // Stream thinking for both teams in parallel
    await Promise.all([
      streamThinking("red", turnNum),
      streamThinking("blue", turnNum)
    ]);

    // Send turn via WebSocket or simulate
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "run_turn", turn_number: turnNum }));
    } else {
      // Simulate locally
      const turn = simulateTurn(turnNum, selectedBattle?.metrics || {});
      setSelectedBattle(prev => ({
        ...prev,
        turns: [...(prev.turns || []), turn],
        metrics: turn.metrics
      }));
      setCurrentTurn(turnNum);
      if (turn.blue_team?.blocked) {
        triggerBlockedEffect(turnNum);
      }
    }

    setIsStreaming(false);
  }, [selectedBattle, isRunning, currentTurn, streamThinking, simulateTurn, triggerBlockedEffect]);

  useEffect(() => {
    const handleKey = (event) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      if (event.code === "Space") {
        event.preventDefault();
        if (!isRunning) {
          startBattle();
        } else {
          setAutoPlay((prev) => !prev);
          setDemoMode(false);
        }
      }
      if (event.key === "ArrowRight") {
        runTurn();
      }
      if (event.key === "ArrowLeft" && currentTurn > 0) {
        jumpToTurn(currentTurn - 1);
      }
      if (event.key.toLowerCase() === "d") {
        setDemoMode((prev) => !prev);
        setAutoPlay(false);
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isRunning, currentTurn, startBattle, runTurn, jumpToTurn]);

  // Demo Mode - Auto-runs battle with dramatic pacing
  const runDemoMode = useCallback(async () => {
    if (!demoMode || !isRunning) return;
    
    await runTurn();
    
    // Variable delay for dramatic effect
    const baseDelay = Math.max(800, 3000 - speed[0] * 20);
    const variation = Math.random() * 500;
    
    demoRef.current = setTimeout(() => {
      if (demoMode && isRunning) {
        runDemoMode();
      }
    }, baseDelay + variation);
  }, [demoMode, isRunning, speed, runTurn]);

  useEffect(() => {
    if (demoMode && isRunning) {
      runDemoMode();
    } else if (demoRef.current) {
      clearTimeout(demoRef.current);
    }
    return () => {
      if (demoRef.current) clearTimeout(demoRef.current);
    };
  }, [demoMode, isRunning, runDemoMode]);

  // Regular autoplay
  useEffect(() => {
    if (autoPlay && isRunning && !demoMode) {
      const interval = Math.max(500, 2000 - speed[0] * 15);
      autoPlayRef.current = setInterval(runTurn, interval);
    } else {
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    }
    return () => {
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    };
  }, [autoPlay, isRunning, speed, demoMode, runTurn]);

  const jumpToTurn = useCallback((index) => {
    setCurrentTurn(index);
    const turn = selectedBattle?.turns?.[index];
    if (turn) {
      setRedThinking(`--- Replaying Turn ${index + 1} ---\n[ACTION] ${turn.red_team?.action || 'N/A'}\n[RESULT] ${turn.red_team?.success ? 'Attack succeeded' : 'Attack blocked'}`);
      setBlueThinking(`--- Replaying Turn ${index + 1} ---\n[ACTION] ${turn.blue_team?.action || 'N/A'}\n[RESULT] ${turn.blue_team?.blocked ? 'Successfully defended' : 'Defense bypassed'}`);
    }
  }, [selectedBattle]);

  const resetBattle = () => {
    setCurrentTurn(0);
    setRedThinking("");
    setBlueThinking("");
    if (selectedBattle) {
      setSelectedBattle({ ...selectedBattle, turns: [], metrics: { success_rate: 0, money_at_risk: 0, money_saved: 0, time_to_immunity: 10, patterns_learned: 0 } });
    }
    toast.info("Battle reset");
  };

  const runWowFactor = () => {
    if (!isRunning) {
      startBattle();
    }
    setDemoMode(true);
    setAutoPlay(false);
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

  const handleLifecycleAutoRun = useCallback(async () => {
    setWorkflowBusy(true);
    try {
      let runId = workflowRunId;
      if (!runId) {
        const startResponse = await runAPI.start({ scenario_id: "war-room", mode: "auto" });
        runId = startResponse?.data?.id;
        setWorkflowRunId(runId || "");
      }
      if (!runId) {
        toast.error("Failed to create workflow run");
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
  }, [workflowRunId, syncWorkflow]);

  const handleWorkflowAdvance = useCallback(async () => {
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
  }, [workflowRunId, workflowState, syncWorkflow]);

  const handleWorkflowRefresh = useCallback(async () => {
    try {
      await syncWorkflow(workflowRunId);
    } catch (error) {
      toast.error("Failed to refresh workflow state");
    }
  }, [workflowRunId, syncWorkflow]);

  const handleWorkflowFreeze = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.freeze(workflowRunId, {
        actor_id: "current-user",
        notes: "Freeze issued from War Room",
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
  }, [workflowRunId, syncWorkflow]);

  const handleWorkflowRollback = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.rollback(workflowRunId, {
        actor_id: "current-user",
        notes: "Rollback issued from War Room",
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
  }, [workflowRunId, syncWorkflow]);

  const handleWorkflowReset = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a workflow run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const response = await workflowAPI.reset(workflowRunId, {
        actor_id: "current-user",
        notes: "Reset issued from War Room",
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
  }, [workflowRunId, syncWorkflow]);

  const handleRunReplay = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a lifecycle run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      await runAPI.replay(workflowRunId, { reset_events: true, clear_agent_tasks: true, clear_agent_artifacts: true });
      await syncWorkflow(workflowRunId);
      toast.success("Run replayed");
    } catch (error) {
      toast.error("Failed to replay run");
    } finally {
      setWorkflowBusy(false);
    }
  }, [workflowRunId, syncWorkflow]);

  const handleDeterministicReplay = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a lifecycle run first");
      return;
    }
    setWorkflowBusy(true);
    try {
      const runResponse = await runAPI.get(workflowRunId);
      const seedValue = runResponse?.data?.run?.seed;
      await runAPI.replay(workflowRunId, {
        seed: seedValue,
        reset_events: true,
        clear_agent_tasks: true,
        clear_agent_artifacts: true,
      });

      let nextStage = "init";
      let stepGuard = 0;
      while (nextStage !== "done" && stepGuard < 25) {
        const stepResponse = await runAPI.step(workflowRunId);
        nextStage = stepResponse?.data?.next_stage || "done";
        stepGuard += 1;
      }

      await syncWorkflow(workflowRunId);
      toast.success("Deterministic replay completed");
    } catch (error) {
      toast.error("Failed to replay war loop");
    } finally {
      setWorkflowBusy(false);
    }
  }, [workflowRunId, syncWorkflow]);

  const handleExportBrc = useCallback(async () => {
    if (!workflowRunId) {
      toast.error("Start a lifecycle run first");
      return;
    }
    try {
      const response = await runAPI.exportBrc(workflowRunId);
      const blob = new Blob([response.data], { type: "application/octet-stream" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `battle_${workflowRunId}.brc`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("BRC exported");
    } catch (error) {
      toast.error("Failed to export BRC");
    }
  }, [workflowRunId]);

  useEffect(() => {
    if (lifecycleAutoRef.current) return;
    const params = new URLSearchParams(location.search);
    if (params.get("lifecycle") === "auto") {
      lifecycleAutoRef.current = true;
      handleLifecycleAutoRun();
    }
  }, [location.search, handleLifecycleAutoRun]);

  useEffect(() => {
    if (workflowRunId) {
      syncWorkflow(workflowRunId);
    } else {
      setGovernanceStatus(null);
      setWorkflowApprovals([]);
    }
  }, [workflowRunId, syncWorkflow]);

  useEffect(() => {
    if (!workflowRunId) return;
    const interval = setInterval(() => {
      syncWorkflow(workflowRunId);
    }, 5000);
    return () => clearInterval(interval);
  }, [workflowRunId, syncWorkflow]);

  const metrics = selectedBattle?.metrics || {};
  const animatedMoneySaved = useAnimatedNumber(metrics.money_saved || 0);
  const displayMetrics = { ...metrics, money_saved: animatedMoneySaved };

  const orchestratorEvents = useMemo(
    () => (runEvents || []).filter((event) => event.event_type === "orchestrator.output"),
    [runEvents]
  );

  const latestOrchestratorByTeam = useMemo(() => {
    return orchestratorEvents.reduce((acc, event) => {
      const team = (event.payload?.team || "unknown").toLowerCase();
      if (!acc[team] || new Date(event.created_at) > new Date(acc[team].created_at)) {
        acc[team] = event;
      }
      return acc;
    }, {});
  }, [orchestratorEvents]);

  const stageDefinitions = useMemo(() => ([
    { team: "red", stage: "red_simulate_attack", label: "Red / Simulate Attack", color: "text-red-400", border: "border-red-500/30 bg-red-500/5", icon: Sword },
    { team: "blue", stage: "blue_detect_respond", label: "Blue / Detect & Respond", color: "text-blue-400", border: "border-blue-500/30 bg-blue-500/5", icon: Shield },
    { team: "purple", stage: "purple_tune_models", label: "Purple / Tune Models", color: "text-purple-400", border: "border-purple-500/30 bg-purple-500/5", icon: Brain },
    { team: "green", stage: "green_deploy_hotfix", label: "Green / Deploy Hotfix", color: "text-green-400", border: "border-green-500/30 bg-green-500/5", icon: Activity },
    { team: "black", stage: "black_failure_analysis", label: "Black / Failure Analysis", color: "text-slate-200", border: "border-slate-500/30 bg-slate-500/10", icon: AlertTriangle },
    { team: "orange", stage: "orange_review_approve", label: "Orange / Review & Approve", color: "text-orange-400", border: "border-orange-500/30 bg-orange-500/5", icon: Sparkles },
    { team: "gold", stage: "gold_monitor_metrics", label: "Gold / Monitor Metrics", color: "text-yellow-300", border: "border-yellow-500/30 bg-yellow-500/5", icon: DollarSign },
    { team: "white", stage: "white_compliance_audit", label: "White / Compliance Audit", color: "text-slate-100", border: "border-slate-400/30 bg-slate-400/10", icon: Clock },
  ]), []);

  const formatOutput = (outputs) => {
    if (!outputs) return "No output yet.";
    if (typeof outputs === "string") return outputs;
    try {
      return JSON.stringify(outputs, null, 2);
    } catch (error) {
      return String(outputs);
    }
  };

  const formatEventTime = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleTimeString();
  };

  const governanceBadgeClass = (status) => {
    if (status === "SAFE_TO_PROCEED") return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30";
    if (status === "PROCEED_WITH_REVIEW") return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30";
    if (status === "FREEZE_RELEASES") return "bg-red-500/15 text-red-300 border border-red-500/30";
    return "bg-slate-500/15 text-slate-200 border border-slate-500/30";
  };

  const approvalSummary = useMemo(() => {
    const approvals = workflowApprovals || [];
    return {
      pending: approvals.filter((item) => item.status === "pending").length,
      approved: approvals.filter((item) => item.status === "approved").length,
      rejected: approvals.filter((item) => item.status === "rejected").length,
      total: approvals.length,
    };
  }, [workflowApprovals]);

  const simulateFailure = llmOverrides?.simulate_failure || {};
  const simulateEnabled = Boolean(simulateFailure?.enabled);
  const simulateModelId = simulateFailure?.model_ids?.[0] || "";

  const telemetryByTeam = useMemo(() => {
    const entries = llmTelemetry?.teams || [];
    return entries.reduce((acc, entry) => {
      const key = entry.team_id || "unknown";
      if (!acc[key]) {
        acc[key] = entry;
      }
      return acc;
    }, {});
  }, [llmTelemetry]);

  return (
    <div className="h-full flex flex-col" data-testid="war-room">
      {/* Metrics Strip */}
      <MetricsStrip
        metrics={displayMetrics}
        onMetricClick={(item) => setActiveMetric(item)}
      />

      {/* Controls */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-zinc-900/50">
        <div className="flex items-center gap-4">
          <Select
            value={selectedBattle?.id || ""}
            onValueChange={(id) => {
              const battle = battles.find(b => b.id === id);
              setSelectedBattle(battle);
              setCurrentTurn(0);
              setRedThinking("");
              setBlueThinking("");
            }}
          >
            <SelectTrigger className="w-[200px]" data-testid="battle-select">
              <SelectValue placeholder="Select Battle" />
            </SelectTrigger>
            <SelectContent>
              {battles.map((battle) => (
                <SelectItem key={battle.id} value={battle.id}>
                  {battle.scenario_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            onClick={createNewBattle}
            data-testid="create-battle-btn"
            data-explain="Create new battle"
            data-explain-title="Battle initialization"
            data-explain-summary="Creates a simulated scenario with attacker/defender teams and baseline risk settings."
            data-explain-rules="SIM-INIT-01"
            data-explain-evidence="Scenario template,Seed data"
          >
            <Zap className="h-4 w-4 mr-2" />
            New Battle
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* WebSocket Status */}
          <div className="flex items-center gap-2 text-sm">
            {wsConnected ? (
              <Badge variant="outline" className="border-green-500 text-green-400">
                <Wifi className="h-3 w-3 mr-1" />
                Live
              </Badge>
            ) : (
              <Badge variant="outline" className="border-zinc-600">
                <WifiOff className="h-3 w-3 mr-1" />
                Local
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm">
            <Badge
              variant="outline"
              className={(() => {
                const hitRate = ragHealth?.telemetry?.hit_rate;
                const warn = Number(ragSettings?.hit_rate_warn ?? 0.6);
                const crit = Number(ragSettings?.hit_rate_crit ?? 0.4);
                if (hitRate === undefined || hitRate === null) return "border-purple-500 text-purple-300";
                if (hitRate <= crit) return "border-red-500 text-red-300";
                if (hitRate <= warn) return "border-yellow-500 text-yellow-300";
                return "border-green-500 text-green-300";
              })()}
            >
              <Brain className="h-3 w-3 mr-1" />
              RAG {ragHealth?.telemetry ? `${(ragHealth.telemetry.hit_rate * 100).toFixed(0)}% hit` : "health"}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {ragHealth?.latest?.created_at ? `Eval ${ragHealth.latest.created_at}` : "No eval"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Alerts Toggle */}
          <div className="flex items-center gap-2">
            <Switch
              checked={alertsEnabled}
              onCheckedChange={setAlertsEnabled}
              id="alerts-toggle"
              data-testid="alerts-toggle"
            />
            <Label htmlFor="alerts-toggle" className="text-sm flex items-center gap-1">
              {alertsEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
              Alerts
            </Label>
          </div>

          <div className="h-6 w-px bg-border" />

          {/* Speed Control */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Rewind className="h-4 w-4" />
            <div className="w-24">
              <Slider value={speed} onValueChange={setSpeed} min={0} max={100} step={10} data-testid="speed-slider" />
            </div>
            <FastForward className="h-4 w-4" />
          </div>

          {/* Demo Mode Toggle */}
          <div className="flex items-center gap-2">
            <Switch
              checked={demoMode}
              onCheckedChange={(checked) => {
                setDemoMode(checked);
                if (checked) setAutoPlay(false);
              }}
              id="demo-mode"
              disabled={!isRunning}
              data-testid="demo-toggle"
            />
            <Label htmlFor="demo-mode" className="text-sm">Demo</Label>
          </div>

          <Button
            variant="outline"
            onClick={runWowFactor}
            disabled={!selectedBattle}
            data-testid="wow-factor-btn"
            data-explain="Show wow factor"
            data-explain-title="Demo impact"
            data-explain-summary="Highlights best-case blocking outcomes and savings for the current scenario."
            data-explain-rules="SIM-DEMO-03"
            data-explain-evidence="Blocked attempts,Savings estimate"
          >
            <Sparkles className="h-4 w-4 mr-2 text-purple-400" />
            Wow Factor
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* Battle Controls */}
          <div className="flex items-center gap-2">
            {!isRunning ? (
              <Button
                onClick={startBattle}
                disabled={!selectedBattle}
                data-testid="start-battle-btn"
                data-explain="Start battle"
                data-explain-title="Simulation start"
                data-explain-summary="Begins the attack/defense simulation and streaming telemetry."
                data-explain-rules="SIM-RUN-01"
                data-explain-evidence="Battle setup,Scenario params"
              >
                <Play className="h-4 w-4 mr-2" />
                Start
              </Button>
            ) : (
              <>
                <Button
                  variant={autoPlay ? "default" : "outline"}
                  onClick={() => {
                    setAutoPlay(!autoPlay);
                    if (!autoPlay) setDemoMode(false);
                  }}
                  disabled={demoMode}
                  data-explain="Auto play"
                  data-explain-title="Automated turns"
                  data-explain-summary="Runs simulation turns continuously with telemetry updates."
                  data-explain-rules="SIM-AUTO-02"
                  data-explain-evidence="Turn cadence,Streaming status"
                  data-testid="autoplay-btn"
                >
                  {autoPlay ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                  {autoPlay ? "Pause" : "Auto"}
                </Button>
                <Button
                  variant="outline"
                  onClick={runTurn}
                  disabled={autoPlay || demoMode || isStreaming}
                  data-testid="step-btn"
                  data-explain="Run next turn"
                  data-explain-title="Manual step"
                  data-explain-summary="Advances the simulation by one turn for granular review."
                  data-explain-rules="SIM-STEP-01"
                  data-explain-evidence="Current turn state,Pending actions"
                >
                  <SkipForward className="h-4 w-4 mr-2" />
                  Step
                </Button>
                <Button variant="ghost" onClick={resetBattle} data-testid="reset-btn">
                  <RotateCcw className="h-4 w-4" />
                </Button>
                <Button
                  variant="destructive"
                  onClick={stopBattle}
                  data-testid="stop-battle-btn"
                  data-explain="Stop battle"
                  data-explain-title="Simulation stop"
                  data-explain-summary="Stops the run and freezes telemetry for review."
                  data-explain-rules="SIM-STOP-01"
                  data-explain-evidence="Run status,Turn summary"
                >
                  Stop
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="border-b border-border bg-card/40 px-6 py-4" data-testid="war-room-lifecycle">
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Lifecycle Workflow Controls</CardTitle>
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
          <CardContent className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-center justify-between">
                <span>Run ID</span>
                <span className="text-white truncate max-w-[220px]">
                  {workflowRunId || "Not started"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>State</span>
                <Badge className="bg-slate-500/15 text-slate-200 border border-slate-500/30">
                  {workflowState}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Status</span>
                <Badge className={workflowStatus === "awaiting_approval" ? "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30" : "bg-blue-500/15 text-blue-300 border border-blue-500/30"}>
                  {workflowStatus}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Governance</span>
                <Badge className={governanceBadgeClass(governanceStatus?.status)}>
                  {(governanceStatus?.status || "—").replace(/_/g, " ")}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
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
              <ScrollArea className="h-16 pr-3">
                <ul className="mt-2 space-y-1">
                  {(workflowHistory || []).slice(-4).map((item, idx) => (
                    <li key={`${item.state}-${idx}`} className="flex items-center justify-between">
                      <span className="text-white">{item.state}</span>
                      <span>{item.timestamp?.slice(11, 19)}</span>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
              <Button
                className="gap-2"
                onClick={handleLifecycleAutoRun}
                disabled={workflowBusy}
                data-testid="war-room-workflow-auto"
              >
                <Play className="h-4 w-4" />
                Auto-Run
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                onClick={handleWorkflowAdvance}
                disabled={workflowBusy}
                data-testid="war-room-workflow-advance"
              >
                <SkipForward className="h-4 w-4" />
                Advance
              </Button>
              <Button
                variant="destructive"
                className="gap-2"
                onClick={handleWorkflowFreeze}
                disabled={!workflowRunId || workflowBusy}
                data-testid="war-room-workflow-freeze"
              >
                <Snowflake className="h-4 w-4" />
                Freeze
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                onClick={handleWorkflowRollback}
                disabled={!workflowRunId || workflowBusy}
                data-testid="war-room-workflow-rollback"
              >
                <Undo2 className="h-4 w-4" />
                Rollback
              </Button>
              <Button
                variant="secondary"
                className="gap-2"
                onClick={handleWorkflowReset}
                disabled={!workflowRunId || workflowBusy}
                data-testid="war-room-workflow-reset"
              >
                <RefreshCcw className="h-4 w-4" />
                Reset
              </Button>
              <Button
                variant="secondary"
                className="gap-2"
                onClick={handleDeterministicReplay}
                disabled={!workflowRunId || workflowBusy}
                data-testid="war-room-workflow-replay-full"
              >
                <RotateCcw className="h-4 w-4" />
                Replay (Seeded)
              </Button>
              <Button
                variant="secondary"
                className="gap-2"
                onClick={handleRunReplay}
                disabled={!workflowRunId || workflowBusy}
                data-testid="war-room-run-replay"
              >
                <RotateCcw className="h-4 w-4" />
                Replay
              </Button>
              <Button
                variant="secondary"
                className="gap-2"
                onClick={handleExportBrc}
                disabled={!workflowRunId}
                data-testid="war-room-workflow-export"
              >
                Export BRC
              </Button>
              <Button
                variant="secondary"
                className="gap-2 col-span-2 md:col-span-3"
                onClick={handleWorkflowRefresh}
                disabled={!workflowRunId}
                data-testid="war-room-workflow-refresh"
              >
                Refresh State
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="border-b border-border bg-card/40 px-6 py-4" data-testid="war-room-llm-config">
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">LLM Provider Setup</CardTitle>
            <Badge className="bg-slate-500/15 text-slate-200 border border-slate-500/30">
              {llmModels.length ? `${llmModels.length} models` : "No models"}
            </Badge>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-[2fr_1fr]">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">Global Default</div>
                <Select
                  value={llmOverrides?.global_default || llmConfig?.policy?.global_default || ""}
                  onValueChange={(value) =>
                    saveLlmOverrides({
                      ...llmOverrides,
                      global_default: value,
                    })
                  }
                  disabled={llmSaving || !llmModels.length}
                >
                  <SelectTrigger className="w-[220px]">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {llmModels.map((model) => (
                      <SelectItem key={model.model_id} value={model.model_id}>
                        {model.model_id} • {model.provider}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {stageDefinitions.map((stage) => (
                  <div key={stage.team} className="flex items-center justify-between rounded-md border border-border bg-zinc-900/50 p-3">
                    <div className="flex items-center gap-2 text-xs">
                      <stage.icon className={`h-3 w-3 ${stage.color}`} />
                      <span className="text-white">{stage.team.toUpperCase()}</span>
                    </div>
                    <Select
                      value={resolveTeamModel(stage.team)}
                      onValueChange={(value) => handleTeamModelChange(stage.team, value)}
                      disabled={llmSaving || !llmModels.length}
                    >
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {llmModels.map((model) => (
                          <SelectItem key={`${stage.team}-${model.model_id}`} value={model.model_id}>
                            {model.model_id} • {model.provider}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-md border border-border bg-zinc-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold">Demo Fallback</div>
                    <div className="text-xs text-muted-foreground">Force a model failure to show fallback.</div>
                  </div>
                  <Switch
                    checked={simulateEnabled}
                    onCheckedChange={(checked) => handleSimulateFailure(checked, simulateModelId)}
                    data-testid="llm-simulate-failure"
                  />
                </div>
                <div className="mt-3">
                  <Label className="text-xs text-muted-foreground">Fail Model</Label>
                  <Select
                    value={simulateModelId}
                    onValueChange={(value) => handleSimulateFailure(simulateEnabled, value)}
                    disabled={llmSaving || !llmModels.length}
                  >
                    <SelectTrigger className="w-full mt-2">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {llmModels.map((model) => (
                        <SelectItem key={`fail-${model.model_id}`} value={model.model_id}>
                          {model.model_id} • {model.provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="rounded-md border border-border bg-zinc-900/50 p-4">
                <div className="text-sm font-semibold">Reliability Snapshot</div>
                <div className="text-xs text-muted-foreground">Schema validity • Fallbacks • P95 latency</div>
                <div className="mt-3 space-y-2">
                  {stageDefinitions.map((stage) => {
                    const stats = telemetryByTeam[stage.team] || {};
                    return (
                      <div key={`reliability-${stage.team}`} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <stage.icon className={`h-3 w-3 ${stage.color}`} />
                          <span className="text-white">{stage.team.toUpperCase()}</span>
                        </div>
                        <div className="text-muted-foreground">
                          {(stats.schema_valid_rate ? `${Math.round(stats.schema_valid_rate * 100)}%` : "—")}
                          {" • "}
                          {stats.fallbacks ?? 0} fb
                          {" • "}
                          {stats.p95_latency_ms ? `${Math.round(stats.p95_latency_ms)}ms` : "—"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="border-b border-border bg-card/40 px-6 py-4" data-testid="war-room-orchestrators">
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Orchestrator Outputs (by Stage)</CardTitle>
            <Badge className="bg-slate-500/15 text-slate-200 border border-slate-500/30">
              {workflowRunId ? `Run ${workflowRunId.slice(0, 8)}` : "No active run"}
            </Badge>
          </CardHeader>
          <CardContent>
            {!workflowRunId ? (
              <div className="text-xs text-muted-foreground">
                Start a lifecycle run to capture orchestrator outputs per stage.
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {stageDefinitions.map((stage) => {
                  const event = latestOrchestratorByTeam[stage.team];
                  const outputs = event?.payload?.outputs;
                  const agent = event?.payload?.agent;
                  const Icon = stage.icon;
                  return (
                    <Card key={stage.stage} className={`border ${stage.border}`}>
                      <CardHeader className="pb-2">
                        <CardTitle className={`text-xs flex items-center gap-2 ${stage.color}`}>
                          <Icon className="h-3 w-3" />
                          {stage.label}
                        </CardTitle>
                        <div className="text-[10px] text-muted-foreground flex items-center justify-between">
                          <span>Agent: {agent || "—"}</span>
                          <span>{formatEventTime(event?.created_at)}</span>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <ScrollArea className="h-32 pr-2">
                          <pre className="text-xs whitespace-pre-wrap font-mono">
                            {formatOutput(outputs)}
                          </pre>
                        </ScrollArea>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="border-b border-border bg-card/40 px-6 py-4" data-testid="war-room-registry">
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Registry Snapshot</CardTitle>
            <Badge className="bg-slate-500/15 text-slate-200 border border-slate-500/30">
              {(registrySnapshot?.agents || []).length} agents
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mb-3">
              <Badge variant="outline" className="border-border">
                {(registrySnapshot?.teams || []).length} teams
              </Badge>
              <Badge variant="outline" className="border-border">
                {(registrySnapshot?.delegation_preview || []).length} on deck
              </Badge>
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              {(registrySnapshot?.delegation_preview || []).slice(0, 3).map((item) => (
                <div key={item.agent_id} className="rounded-md border border-border bg-zinc-900/40 p-3">
                  <div className="text-sm font-medium text-white">{item.agent_name}</div>
                  <div className="text-xs text-muted-foreground">{item.role}</div>
                </div>
              ))}
              {!registrySnapshot?.delegation_preview?.length && (
                <div className="text-xs text-muted-foreground">Registry data not available.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metric Drilldown */}
      {activeMetric && (
        <div className="border-b border-border bg-zinc-900/70 px-6 py-4" data-testid="metric-drilldown">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">{activeMetric.label} Drilldown</h3>
              <p className="text-xs text-muted-foreground">Detailed context for the selected metric.</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setActiveMetric(null)} data-testid="metric-drilldown-close">
              Close
            </Button>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-sm">Current Value</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-mono">{activeMetric.value}</div>
                <p className="text-xs text-muted-foreground">Latest reading from live telemetry.</p>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-sm">Signal Drivers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-muted-foreground">
                <div>• Device mismatch spikes</div>
                <div>• Velocity anomalies</div>
                <div>• New payee creation</div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-sm">Recommended Action</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Badge variant="outline">Increase scrutiny</Badge>
                <p className="text-xs text-muted-foreground">Raise threshold or escalate to review.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Scenario Builder */}
      <div className="border-b border-border bg-card/40 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold">Scenario Builder</h3>
            <p className="text-xs text-muted-foreground">Drag blocks into the lane to assemble an attack flow.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={clearScenario} data-testid="scenario-clear-btn">
              Clear
            </Button>
            <Button size="sm" onClick={createScenarioBattle} data-testid="scenario-create-btn">
              Create Scenario Battle
            </Button>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-sm">Blocks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {scenarioBlocks.map((block) => (
                <div
                  key={block.id}
                  draggable
                  onDragStart={onScenarioDragStart(block)}
                  className="p-3 rounded-lg border border-border bg-zinc-900/60 cursor-move hover:border-zinc-600"
                  data-testid={`scenario-block-${block.id}`}
                >
                  <div className="text-sm font-medium">{block.label}</div>
                  <div className="text-xs text-muted-foreground">{block.description}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card
            className="border-border col-span-2"
            onDrop={onScenarioDrop}
            onDragOver={onScenarioDragOver}
            data-testid="scenario-dropzone"
          >
            <CardHeader>
              <CardTitle className="text-sm">Scenario Lane</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-3">
                <Input
                  value={scenarioName}
                  onChange={(event) => setScenarioName(event.target.value)}
                  placeholder="Scenario name"
                  data-testid="scenario-name-input"
                />
              </div>
              {scenarioSteps.length === 0 ? (
                <div className="border border-dashed border-border rounded-lg p-6 text-center text-xs text-muted-foreground">
                  Drop blocks here to build a scenario.
                </div>
              ) : (
                <div className="space-y-2">
                  {scenarioSteps.map((step, idx) => (
                    <div
                      key={`${step.id}-${idx}`}
                      className="flex items-center justify-between p-3 rounded-lg border border-border bg-black/30"
                      data-testid={`scenario-step-${idx}`}
                    >
                      <div>
                        <div className="text-sm font-medium">{idx + 1}. {step.label}</div>
                        <div className="text-xs text-muted-foreground">{step.description}</div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeScenarioStep(idx)}
                        data-testid={`scenario-remove-${idx}`}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Main Battle Area */}
      <div className="flex-1 flex overflow-hidden">
        {blockedBursts.map((burstId, idx) => (
          <div key={burstId} className="particle-burst">
            {Array.from({ length: 12 }).map((_, particleIndex) => (
              <span
                key={`${burstId}-${particleIndex}`}
                className="particle"
                style={{
                  "--x": `${Math.cos((particleIndex / 12) * Math.PI * 2) * 160}px`,
                  "--y": `${Math.sin((particleIndex / 12) * Math.PI * 2) * 120}px`,
                  animationDelay: `${particleIndex * 10}ms`,
                }}
              />
            ))}
          </div>
        ))}
        {/* Red Team Panel */}
        <div className="flex-1 p-4 border-r border-border overflow-hidden">
          <ThinkingVisualizer 
            team="red" 
            thinking={redThinking} 
            streamingText={redStreamText}
            isStreaming={isStreaming} 
          />
        </div>

        {/* Timeline */}
        <div className="w-72 border-r border-border bg-zinc-900/50 flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Battle Timeline
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedBattle?.turns?.length || 0} turns • Turn {currentTurn}
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {resolveTeamModel("red") && (
                <Badge variant="outline" className="border-red-500/50 text-red-300">
                  Red • {resolveModelLabel(resolveTeamModel("red"))}
                </Badge>
              )}
              {resolveTeamModel("blue") && (
                <Badge variant="outline" className="border-blue-500/50 text-blue-300">
                  Blue • {resolveModelLabel(resolveTeamModel("blue"))}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <BattleTimeline 
              turns={selectedBattle?.turns || []} 
              currentTurn={currentTurn}
              onJumpTo={jumpToTurn}
              onHoverTurn={setHoverTurnIndex}
            />
          </div>
          <div className="border-t border-border p-3 text-xs text-muted-foreground" data-testid="turn-hover-preview">
            {hoverTurnIndex !== null ? (
              <div>
                <div className="font-semibold">Turn {hoverTurnIndex + 1} Preview</div>
                <div className="mt-1">Red: {selectedBattle?.turns?.[hoverTurnIndex]?.red_team?.action || "N/A"}</div>
                <div>Blue: {selectedBattle?.turns?.[hoverTurnIndex]?.blue_team?.action || "N/A"}</div>
              </div>
            ) : (
              <div>Hover a turn to preview details.</div>
            )}
          </div>
        </div>

        {/* Blue Team Panel */}
        <div className="flex-1 p-4 overflow-hidden">
          <ThinkingVisualizer 
            team="blue" 
            thinking={blueThinking} 
            streamingText={blueStreamText}
            isStreaming={isStreaming} 
          />
        </div>
      </div>

      {/* Session Trace Viewer */}
      <div className="border-t border-border bg-zinc-900/60 px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold">Session Trace Viewer</h3>
            <p className="text-xs text-muted-foreground">Filter raw telemetry and decisions.</p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={traceFilter} onValueChange={setTraceFilter}>
              <SelectTrigger className="w-[160px]" data-testid="trace-filter-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="red">Red Team</SelectItem>
                <SelectItem value="blue">Blue Team</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
              </SelectContent>
            </Select>
            <Input
              value={traceSearch}
              onChange={(event) => setTraceSearch(event.target.value)}
              placeholder="Search trace"
              data-testid="trace-search-input"
            />
          </div>
        </div>
        <ScrollArea className="h-32" data-testid="trace-viewer">
          <div className="space-y-2 text-xs font-mono">
            {(selectedBattle?.turns || [])
              .filter((turn) => {
                if (traceFilter === "red") return turn.red_team;
                if (traceFilter === "blue") return turn.blue_team;
                if (traceFilter === "blocked") return turn.blue_team?.blocked;
                return true;
              })
              .filter((turn) => {
                if (!traceSearch) return true;
                const blob = `${turn.red_team?.action || ""} ${turn.blue_team?.action || ""}`.toLowerCase();
                return blob.includes(traceSearch.toLowerCase());
              })
              .map((turn, idx) => (
                <div key={idx} className="p-2 rounded border border-border bg-black/30">
                  <div>Turn {idx + 1} • Red: {turn.red_team?.action || "N/A"} • Blue: {turn.blue_team?.action || "N/A"}</div>
                  <div className="text-muted-foreground">Outcome: {turn.blue_team?.blocked ? "Blocked" : "Missed"}</div>
                </div>
              ))}
          </div>
        </ScrollArea>
      </div>

      {/* Run Summary */}
      {runSummary && (
        <div className="border-t border-border bg-card/60 px-6 py-4" data-testid="run-summary">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">Run Summary</h3>
              <p className="text-xs text-muted-foreground">Executive summary of the completed battle.</p>
            </div>
            <Badge variant="outline">Completed</Badge>
          </div>
          <div className="grid grid-cols-5 gap-4 mt-4 text-sm">
            <Card className="border-border">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground">Scenario</div>
                <div className="font-semibold">{runSummary.battle}</div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground">Turns</div>
                <div className="font-mono text-lg">{runSummary.turns}</div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground">Success Rate</div>
                <div className="font-mono text-lg">{runSummary.successRate}%</div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground">Money Saved</div>
                <div className="font-mono text-lg">${runSummary.moneySaved.toLocaleString()}</div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground">Time-to-Immunity</div>
                <div className="font-mono text-lg">{runSummary.timeToImmunity}m</div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div className="h-10 flex items-center justify-between px-6 border-t border-border bg-card text-sm">
        <div className="flex items-center gap-4">
          <Badge variant={selectedBattle?.status === 'running' ? 'default' : 'secondary'}>
            {selectedBattle?.status || 'No battle selected'}
          </Badge>
          <span className="text-muted-foreground font-mono">
            Turn: {currentTurn} / {selectedBattle?.parameters?.max_turns || '∞'}
          </span>
          {demoMode && (
            <Badge variant="outline" className="border-purple-500 text-purple-400">
              <Radio className="h-3 w-3 mr-1 animate-pulse" />
              DEMO MODE
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Activity className={`h-4 w-4 ${isRunning ? 'text-green-400 live-indicator' : ''}`} />
          {isStreaming ? 'AI Thinking...' : isRunning ? 'Battle in progress' : 'Ready'}
        </div>
      </div>
    </div>
  );
};

export default WarRoom;
