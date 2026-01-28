import React, { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Progress } from "../components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import { battleAPI, aiAPI, createBattleWebSocket } from "../lib/api";
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
} from "lucide-react";

// Thinking Visualizer Component
const ThinkingVisualizer = ({ team, thinking, isStreaming }) => {
  const stages = ["Recon", "Ideation", "Evaluation", "Action"];
  const currentStage = thinking ? stages.findIndex(s => thinking.includes(s)) : -1;

  return (
    <div className={`rounded-lg border p-4 ${team === 'red' ? 'border-red-500/30 gradient-red' : 'border-blue-500/30 gradient-blue'}`}>
      <div className="flex items-center gap-2 mb-3">
        {team === 'red' ? <Sword className="h-4 w-4 text-red-400" /> : <Shield className="h-4 w-4 text-blue-400" />}
        <span className={`text-sm font-semibold ${team === 'red' ? 'text-red-400' : 'text-blue-400'}`}>
          {team === 'red' ? 'RED TEAM' : 'BLUE TEAM'} THINKING
        </span>
        {isStreaming && <span className="live-indicator w-2 h-2 rounded-full bg-green-500" />}
      </div>

      {/* Stage Progress */}
      <div className="flex gap-1 mb-4">
        {stages.map((stage, idx) => (
          <div key={stage} className="flex-1">
            <div className={`h-1 rounded-full ${idx <= currentStage ? (team === 'red' ? 'bg-red-500' : 'bg-blue-500') : 'bg-zinc-700'}`} />
            <span className="text-xs text-muted-foreground mt-1 block">{stage}</span>
          </div>
        ))}
      </div>

      {/* Thinking Stream */}
      <div className="font-mono text-sm bg-black/30 rounded p-3 min-h-[100px] max-h-[200px] overflow-auto">
        {thinking ? (
          <span className={isStreaming ? 'cursor-blink' : ''}>{thinking}</span>
        ) : (
          <span className="text-muted-foreground">Waiting for battle to start...</span>
        )}
      </div>
    </div>
  );
};

// Battle Timeline Component
const BattleTimeline = ({ turns, onJumpTo }) => {
  return (
    <ScrollArea className="h-full">
      <div className="space-y-2 p-2">
        {turns.map((turn, idx) => (
          <div
            key={idx}
            onClick={() => onJumpTo(idx)}
            className="flex items-center gap-3 p-3 rounded-lg border border-border bg-card hover:bg-zinc-800 cursor-pointer transition-colors"
            data-testid={`turn-${idx}`}
          >
            <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-mono">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={turn.red_team?.success ? 'border-red-500 text-red-400' : 'border-zinc-600'}>
                  <Sword className="h-3 w-3 mr-1" />
                  {turn.red_team?.action || 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className={turn.blue_team?.blocked ? 'border-blue-500 text-blue-400' : 'border-zinc-600'}>
                  <Shield className="h-3 w-3 mr-1" />
                  {turn.blue_team?.action || 'N/A'}
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

// Metrics Strip Component
const MetricsStrip = ({ metrics }) => {
  const items = [
    { label: "Success Rate", value: `${metrics.success_rate || 0}%`, icon: Activity, color: "text-green-400" },
    { label: "Money at Risk", value: `$${(metrics.money_at_risk || 0).toLocaleString()}`, icon: DollarSign, color: "text-red-400" },
    { label: "Time to Immunity", value: `${metrics.time_to_immunity || 0}m`, icon: Clock, color: "text-blue-400" },
    { label: "Patterns Learned", value: metrics.patterns_learned || 0, icon: Brain, color: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 p-4 border-b border-border bg-card">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="flex items-center gap-3" data-testid={`metric-${item.label.toLowerCase().replace(/\s/g, '-')}`}>
            <div className={`p-2 rounded-lg bg-zinc-800 ${item.color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{item.label}</p>
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
  const [speed, setSpeed] = useState([50]);
  const [redThinking, setRedThinking] = useState("");
  const [blueThinking, setBlueThinking] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(0);
  const wsRef = useRef(null);
  const autoPlayRef = useRef(null);

  useEffect(() => {
    loadBattles();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    };
  }, []);

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
      toast.success("New battle created!");
    } catch (error) {
      toast.error("Failed to create battle");
    }
  };

  const startBattle = async () => {
    if (!selectedBattle) return;
    try {
      await battleAPI.start(selectedBattle.id);
      setIsRunning(true);
      setSelectedBattle({ ...selectedBattle, status: "running" });
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
      if (wsRef.current) wsRef.current.close();
      setSelectedBattle({ ...selectedBattle, status: "completed" });
      toast.success("Battle stopped!");
    } catch (error) {
      toast.error("Failed to stop battle");
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current) wsRef.current.close();
    
    wsRef.current = createBattleWebSocket(selectedBattle.id);
    
    wsRef.current.onopen = () => {
      console.log("WebSocket connected");
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
      }
    };

    wsRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  const runTurn = async () => {
    if (!selectedBattle || !isRunning) return;
    
    setIsStreaming(true);
    
    // Get AI thinking for both teams
    try {
      const [redResponse, blueResponse] = await Promise.all([
        aiAPI.think({ team: "red", stage: "attack", context: `Turn ${currentTurn + 1}` }),
        aiAPI.think({ team: "blue", stage: "defense", context: `Turn ${currentTurn + 1}` })
      ]);
      
      setRedThinking(redResponse.data.thinking);
      setBlueThinking(blueResponse.data.thinking);
    } catch (error) {
      // Use fallback thinking
      setRedThinking(`[RED - Turn ${currentTurn + 1}] Analyzing vulnerabilities... Executing attack vector...`);
      setBlueThinking(`[BLUE - Turn ${currentTurn + 1}] Monitoring patterns... Deploying countermeasures...`);
    }

    // Send turn command via WebSocket or simulate locally
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "run_turn", turn_number: currentTurn + 1 }));
    } else {
      // Simulate locally
      const turn = simulateTurn(currentTurn + 1);
      setSelectedBattle(prev => ({
        ...prev,
        turns: [...(prev.turns || []), turn],
        metrics: turn.metrics
      }));
      setCurrentTurn(prev => prev + 1);
    }

    setTimeout(() => setIsStreaming(false), 1000);
  };

  const simulateTurn = (turnNumber) => {
    const redActions = ["Account Takeover", "Velocity Attack", "Device Spoofing", "Credential Stuffing"];
    const blueActions = ["Pattern Detection", "Velocity Check", "Device Fingerprinting", "ML Score"];
    const redSuccess = Math.random() < 0.4;

    return {
      type: "turn_update",
      turn_number: turnNumber,
      red_team: { action: redActions[Math.floor(Math.random() * redActions.length)], success: redSuccess },
      blue_team: { action: blueActions[Math.floor(Math.random() * blueActions.length)], blocked: !redSuccess },
      metrics: {
        success_rate: Math.floor(60 + Math.random() * 35),
        money_at_risk: Math.floor(1000 + Math.random() * 49000),
        time_to_immunity: Math.max(1, 10 - Math.floor(turnNumber / 2)),
        patterns_learned: turnNumber
      }
    };
  };

  useEffect(() => {
    if (autoPlay && isRunning) {
      const interval = Math.max(500, 2000 - speed[0] * 15);
      autoPlayRef.current = setInterval(runTurn, interval);
    } else {
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    }
    return () => {
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    };
  }, [autoPlay, isRunning, speed]);

  const jumpToTurn = (index) => {
    setCurrentTurn(index);
    const turn = selectedBattle?.turns?.[index];
    if (turn) {
      setRedThinking(`[RED - Turn ${index + 1}] ${turn.red_team?.action || 'N/A'}`);
      setBlueThinking(`[BLUE - Turn ${index + 1}] ${turn.blue_team?.action || 'N/A'}`);
    }
  };

  return (
    <div className="h-full flex flex-col" data-testid="war-room">
      {/* Metrics Strip */}
      <MetricsStrip metrics={selectedBattle?.metrics || {}} />

      {/* Controls */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-4">
          <Select
            value={selectedBattle?.id || ""}
            onValueChange={(id) => setSelectedBattle(battles.find(b => b.id === id))}
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
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Speed:</span>
            <div className="w-32">
              <Slider value={speed} onValueChange={setSpeed} min={0} max={100} step={10} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isRunning ? (
              <Button onClick={startBattle} disabled={!selectedBattle} data-testid="start-battle-btn">
                <Play className="h-4 w-4 mr-2" />
                Start
              </Button>
            ) : (
              <>
                <Button
                  variant={autoPlay ? "destructive" : "default"}
                  onClick={() => setAutoPlay(!autoPlay)}
                  data-testid="autoplay-btn"
                >
                  {autoPlay ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                  {autoPlay ? "Pause" : "Auto"}
                </Button>
                <Button variant="outline" onClick={runTurn} disabled={autoPlay} data-testid="step-btn">
                  <SkipForward className="h-4 w-4 mr-2" />
                  Step
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
        <div className="flex-1 p-6 border-r border-border overflow-auto">
          <ThinkingVisualizer team="red" thinking={redThinking} isStreaming={isStreaming} />
        </div>

        {/* Timeline */}
        <div className="w-80 border-r border-border bg-zinc-900/50">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Battle Timeline
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedBattle?.turns?.length || 0} turns
            </p>
          </div>
          <BattleTimeline turns={selectedBattle?.turns || []} onJumpTo={jumpToTurn} />
        </div>

        {/* Blue Team Panel */}
        <div className="flex-1 p-6 overflow-auto">
          <ThinkingVisualizer team="blue" thinking={blueThinking} isStreaming={isStreaming} />
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
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Activity className={`h-4 w-4 ${isRunning ? 'text-green-400 live-indicator' : ''}`} />
          {isRunning ? 'Battle in progress' : 'Ready'}
        </div>
      </div>
    </div>
  );
};

export default WarRoom;
