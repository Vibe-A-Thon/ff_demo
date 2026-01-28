import React, { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Progress } from "../components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { battleAPI, aiAPI, createBattleWebSocket } from "../lib/api";
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
const BattleTimeline = ({ turns, currentTurn, onJumpTo }) => {
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
const MetricsStrip = ({ metrics, alerts }) => {
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
    <div className="grid grid-cols-4 gap-4 p-4 border-b border-border bg-card">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div 
            key={item.key} 
            className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
              item.alert === 'critical' ? 'bg-red-500/10 border border-red-500/30 animate-pulse' :
              item.alert === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/30' : ''
            }`}
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
          </div>
        );
      })}
    </div>
  );
};

const WarRoom = () => {
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
  const wsRef = useRef(null);
  const autoPlayRef = useRef(null);
  const demoRef = useRef(null);
  
  const { checkMetrics, alertsEnabled, setAlertsEnabled } = useAlerts();

  useEffect(() => {
    loadBattles();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
      if (demoRef.current) clearTimeout(demoRef.current);
    };
  }, []);

  // Check metrics for alerts whenever they change
  useEffect(() => {
    if (selectedBattle?.metrics) {
      checkMetrics(selectedBattle.metrics);
    }
  }, [selectedBattle?.metrics, checkMetrics]);

  const loadBattles = async () => {
    try {
      const response = await battleAPI.getAll();
      setBattles(response.data);
      if (response.data.length > 0) {
        setSelectedBattle(response.data[0]);
      }
    } catch (error) {
      console.error("Failed to load battles:", error);
    }
  };

  const createNewBattle = async () => {
    try {
      const response = await battleAPI.create({
        scenario_name: `Battle ${battles.length + 1}`,
        parameters: { difficulty: "medium", max_turns: 20 }
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
        } else if (data.type === "thinking_chunk") {
          // Handle streaming thinking
          if (data.team === "red") {
            setRedStreamText(prev => prev + data.chunk);
          } else {
            setBlueStreamText(prev => prev + data.chunk);
          }
        } else if (data.type === "thinking_complete") {
          if (data.team === "red") {
            setRedThinking(prev => prev + redStreamText);
            setRedStreamText("");
          } else {
            setBlueThinking(prev => prev + blueStreamText);
            setBlueStreamText("");
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
  }, [selectedBattle]);

  const startBattle = async () => {
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
  };

  const stopBattle = async () => {
    if (!selectedBattle) return;
    try {
      await battleAPI.stop(selectedBattle.id);
      setIsRunning(false);
      setAutoPlay(false);
      setDemoMode(false);
      if (wsRef.current) wsRef.current.close();
      setSelectedBattle({ ...selectedBattle, status: "completed" });
      toast.success("Battle stopped!");
    } catch (error) {
      toast.error("Failed to stop battle");
    }
  };

  // Streaming AI thinking simulation
  const streamThinking = async (team, turnNum) => {
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
  };

  const runTurn = async () => {
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
      const turn = simulateTurn(turnNum);
      setSelectedBattle(prev => ({
        ...prev,
        turns: [...(prev.turns || []), turn],
        metrics: turn.metrics
      }));
      setCurrentTurn(turnNum);
    }

    setIsStreaming(false);
  };

  const simulateTurn = (turnNumber) => {
    const redActions = ["Account Takeover", "Velocity Attack", "Device Spoofing", "Credential Stuffing", "Social Engineering"];
    const blueActions = ["Pattern Detection", "Velocity Check", "Device Fingerprinting", "ML Score", "Rule Match"];
    const redSuccess = Math.random() < 0.35;

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
        money_at_risk: Math.floor(5000 + Math.random() * 45000),
        time_to_immunity: timeToImmunity,
        patterns_learned: turnNumber
      }
    };
  };

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
  }, [demoMode, isRunning]);

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
  }, [autoPlay, isRunning, speed, demoMode]);

  const jumpToTurn = (index) => {
    setCurrentTurn(index);
    const turn = selectedBattle?.turns?.[index];
    if (turn) {
      setRedThinking(`--- Replaying Turn ${index + 1} ---\n[ACTION] ${turn.red_team?.action || 'N/A'}\n[RESULT] ${turn.red_team?.success ? 'Attack succeeded' : 'Attack blocked'}`);
      setBlueThinking(`--- Replaying Turn ${index + 1} ---\n[ACTION] ${turn.blue_team?.action || 'N/A'}\n[RESULT] ${turn.blue_team?.blocked ? 'Successfully defended' : 'Defense bypassed'}`);
    }
  };

  const resetBattle = () => {
    setCurrentTurn(0);
    setRedThinking("");
    setBlueThinking("");
    if (selectedBattle) {
      setSelectedBattle({ ...selectedBattle, turns: [], metrics: { success_rate: 0, money_at_risk: 0, time_to_immunity: 10, patterns_learned: 0 } });
    }
    toast.info("Battle reset");
  };

  return (
    <div className="h-full flex flex-col" data-testid="war-room">
      {/* Metrics Strip */}
      <MetricsStrip metrics={selectedBattle?.metrics || {}} />

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

          <Button variant="outline" onClick={createNewBattle} data-testid="create-battle-btn">
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
        </div>

        <div className="flex items-center gap-4">
          {/* Alerts Toggle */}
          <div className="flex items-center gap-2">
            <Switch
              checked={alertsEnabled}
              onCheckedChange={setAlertsEnabled}
              id="alerts-toggle"
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
              <Slider value={speed} onValueChange={setSpeed} min={0} max={100} step={10} />
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
            />
            <Label htmlFor="demo-mode" className="text-sm">Demo</Label>
          </div>

          <div className="h-6 w-px bg-border" />

          {/* Battle Controls */}
          <div className="flex items-center gap-2">
            {!isRunning ? (
              <Button onClick={startBattle} disabled={!selectedBattle} data-testid="start-battle-btn">
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
                  data-testid="autoplay-btn"
                >
                  {autoPlay ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                  {autoPlay ? "Pause" : "Auto"}
                </Button>
                <Button variant="outline" onClick={runTurn} disabled={autoPlay || demoMode || isStreaming} data-testid="step-btn">
                  <SkipForward className="h-4 w-4 mr-2" />
                  Step
                </Button>
                <Button variant="ghost" onClick={resetBattle} data-testid="reset-btn">
                  <RotateCcw className="h-4 w-4" />
                </Button>
                <Button variant="destructive" onClick={stopBattle} data-testid="stop-battle-btn">
                  Stop
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Battle Area */}
      <div className="flex-1 flex overflow-hidden">
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
          </div>
          <div className="flex-1 overflow-hidden">
            <BattleTimeline 
              turns={selectedBattle?.turns || []} 
              currentTurn={currentTurn}
              onJumpTo={jumpToTurn} 
            />
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
