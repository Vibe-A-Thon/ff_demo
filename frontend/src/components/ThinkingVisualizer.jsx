/**
 * ThinkingVisualizer - 7-Stage Attack Pipeline Visualization
 * 
 * Displays the Red Team attack thinking process through 7 distinct stages:
 * 1. RECONNAISSANCE - Scanning defenses
 * 2. IDEATION - Generative AI brainstorming
 * 3. PLANNING - Selecting tools
 * 4. EVASION - Mutating payloads
 * 5. EXECUTION - Running attack
 * 6. REFLECTION - Did it work?
 * 7. LEARNING - Updating RAG
 */

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { ScrollArea } from "./ui/scroll-area";
import {
  Search,
  Lightbulb,
  Target,
  Shield,
  Play,
  Eye,
  BookOpen,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  ChevronRight,
} from "lucide-react";

// Stage definitions with metadata
const THINKING_STAGES = [
  {
    id: "reconnaissance",
    name: "RECONNAISSANCE",
    description: "Scanning defense topology and patterns",
    icon: Search,
    color: "#3B82F6",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    textColor: "text-blue-400",
    actions: ["Mapping defense rules", "Identifying weak points", "Analyzing response patterns"],
  },
  {
    id: "ideation",
    name: "IDEATION",
    description: "Generative AI brainstorming attack vectors",
    icon: Lightbulb,
    color: "#F59E0B",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    textColor: "text-amber-400",
    actions: ["Querying attack memory", "Generating novel approaches", "Cross-referencing taxonomy"],
  },
  {
    id: "planning",
    name: "PLANNING",
    description: "Selecting optimal tools and sequence",
    icon: Target,
    color: "#8B5CF6",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    textColor: "text-purple-400",
    actions: ["Tool selection", "Attack chain design", "Timing optimization"],
  },
  {
    id: "evasion",
    name: "EVASION",
    description: "Mutating payloads to bypass detection",
    icon: Shield,
    color: "#EF4444",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    textColor: "text-red-400",
    actions: ["Signature mutation", "Polymorphic encoding", "Anti-detection layers"],
  },
  {
    id: "execution",
    name: "EXECUTION",
    description: "Running the attack against target",
    icon: Play,
    color: "#10B981",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    textColor: "text-emerald-400",
    actions: ["Launching payload", "Monitoring response", "Executing attack chain"],
  },
  {
    id: "reflection",
    name: "REFLECTION",
    description: "Analyzing attack outcome",
    icon: Eye,
    color: "#06B6D4",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
    textColor: "text-cyan-400",
    actions: ["Success evaluation", "Defense analysis", "Gap identification"],
  },
  {
    id: "learning",
    name: "LEARNING",
    description: "Updating RAG with findings",
    icon: BookOpen,
    color: "#EC4899",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
    textColor: "text-pink-400",
    actions: ["Storing to vector DB", "Pattern extraction", "Memory consolidation"],
  },
];

// Status types for stages
const StageStatus = {
  PENDING: "pending",
  ACTIVE: "active",
  COMPLETED: "completed",
  FAILED: "failed",
};

// Individual stage card component
const StageCard = ({ stage, status, logs, isExpanded, onClick, progress }) => {
  const Icon = stage.icon;
  const isActive = status === StageStatus.ACTIVE;
  const isCompleted = status === StageStatus.COMPLETED;
  const isFailed = status === StageStatus.FAILED;

  return (
    <div
      className={`
        relative rounded-lg border transition-all duration-300 cursor-pointer
        ${stage.bgColor} ${stage.borderColor}
        ${isActive ? "ring-2 ring-offset-2 ring-offset-background" : ""}
        ${isExpanded ? "col-span-full" : ""}
        hover:scale-[1.02] hover:shadow-lg
      `}
      style={{
        boxShadow: isActive ? `0 0 20px ${stage.color}40` : undefined,
        borderColor: isActive ? stage.color : undefined,
      }}
      onClick={onClick}
    >
      {/* Active pulse animation */}
      {isActive && (
        <div
          className="absolute inset-0 rounded-lg animate-pulse opacity-30"
          style={{ backgroundColor: stage.color }}
        />
      )}

      <div className="relative p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              className={`p-2 rounded-lg ${stage.bgColor}`}
              style={{ backgroundColor: `${stage.color}20` }}
            >
              <Icon className="h-4 w-4" style={{ color: stage.color }} />
            </div>
            <div>
              <h3 className={`text-xs font-bold tracking-wider ${stage.textColor}`}>
                [{stage.name}]
              </h3>
              <p className="text-[10px] text-muted-foreground">{stage.description}</p>
            </div>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            {status === StageStatus.PENDING && (
              <Clock className="h-4 w-4 text-muted-foreground" />
            )}
            {isActive && (
              <Loader2 className="h-4 w-4 animate-spin" style={{ color: stage.color }} />
            )}
            {isCompleted && (
              <CheckCircle2 className="h-4 w-4 text-green-400" />
            )}
            {isFailed && (
              <AlertCircle className="h-4 w-4 text-red-400" />
            )}
          </div>
        </div>

        {/* Progress bar for active stage */}
        {isActive && (
          <div className="mb-3">
            <Progress
              value={progress}
              className="h-1"
              style={{
                backgroundColor: `${stage.color}20`,
              }}
            />
          </div>
        )}

        {/* Stage actions */}
        <div className="space-y-1">
          {stage.actions.map((action, idx) => (
            <div
              key={idx}
              className={`
                flex items-center gap-2 text-[10px] py-1 px-2 rounded
                ${isActive && idx <= Math.floor(progress / 33) ? stage.bgColor : ""}
                ${isCompleted ? "line-through text-muted-foreground" : "text-muted-foreground"}
              `}
            >
              <ChevronRight className="h-3 w-3" />
              <span>{action}</span>
              {isActive && idx <= Math.floor(progress / 33) && (
                <Loader2 className="h-3 w-3 ml-auto animate-spin" style={{ color: stage.color }} />
              )}
              {isCompleted && (
                <CheckCircle2 className="h-3 w-3 ml-auto text-green-400" />
              )}
            </div>
          ))}
        </div>

        {/* Expanded log view */}
        {isExpanded && logs && logs.length > 0 && (
          <div className="mt-4 border-t border-border/50 pt-3">
            <ScrollArea className="h-32">
              <div className="space-y-1 font-mono text-[10px]">
                {logs.map((log, idx) => (
                  <div key={idx} className="flex gap-2">
                    <span className="text-muted-foreground">{log.timestamp}</span>
                    <span style={{ color: stage.color }}>{log.message}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>
    </div>
  );
};

// Main ThinkingVisualizer component
const ThinkingVisualizer = ({
  battleId,
  isStreaming = false,
  onStageComplete,
  initialStage = null,
  autoProgress = true,
  compact = false,
}) => {
  const [currentStage, setCurrentStage] = useState(0);
  const [stageStatuses, setStageStatuses] = useState(
    THINKING_STAGES.reduce((acc, stage, idx) => ({
      ...acc,
      [stage.id]: idx === 0 ? StageStatus.ACTIVE : StageStatus.PENDING,
    }), {})
  );
  const [stageProgress, setStageProgress] = useState({});
  const [stageLogs, setStageLogs] = useState({});
  const [expandedStage, setExpandedStage] = useState(null);
  const [overallProgress, setOverallProgress] = useState(0);
  const streamIntervalRef = useRef(null);

  // Simulate streaming progress for demo
  useEffect(() => {
    if (!isStreaming || !autoProgress) return;

    streamIntervalRef.current = setInterval(() => {
      setStageProgress((prev) => {
        const currentStageDef = THINKING_STAGES[currentStage];
        if (!currentStageDef) return prev;

        const currentProgress = prev[currentStageDef.id] || 0;
        const newProgress = Math.min(currentProgress + Math.random() * 15 + 5, 100);

        // Add log entry
        if (Math.random() > 0.5) {
          const logMessages = [
            `Analyzing pattern ${Math.floor(Math.random() * 100)}...`,
            `Processing node ${Math.floor(Math.random() * 50)}...`,
            `Evaluating condition ${Math.floor(Math.random() * 20)}...`,
            `Detected anomaly in sequence...`,
            `Optimizing attack vector...`,
          ];
          const message = logMessages[Math.floor(Math.random() * logMessages.length)];
          setStageLogs((prevLogs) => ({
            ...prevLogs,
            [currentStageDef.id]: [
              ...(prevLogs[currentStageDef.id] || []),
              {
                timestamp: new Date().toLocaleTimeString(),
                message,
              },
            ].slice(-10),
          }));
        }

        return { ...prev, [currentStageDef.id]: newProgress };
      });
    }, 500);

    return () => clearInterval(streamIntervalRef.current);
  }, [isStreaming, autoProgress, currentStage]);

  // Handle stage completion
  useEffect(() => {
    const currentStageDef = THINKING_STAGES[currentStage];
    if (!currentStageDef) return;

    const currentProgress = stageProgress[currentStageDef.id] || 0;

    if (currentProgress >= 100) {
      // Complete current stage
      setStageStatuses((prev) => ({
        ...prev,
        [currentStageDef.id]: StageStatus.COMPLETED,
      }));

      // Notify parent
      if (onStageComplete) {
        onStageComplete(currentStageDef.id, currentStage);
      }

      // Move to next stage if available
      if (currentStage < THINKING_STAGES.length - 1) {
        const nextStage = currentStage + 1;
        setCurrentStage(nextStage);
        setStageStatuses((prev) => ({
          ...prev,
          [THINKING_STAGES[nextStage].id]: StageStatus.ACTIVE,
        }));
      }
    }
  }, [stageProgress, currentStage, onStageComplete]);

  // Calculate overall progress
  useEffect(() => {
    const completedStages = Object.values(stageStatuses).filter(
      (s) => s === StageStatus.COMPLETED
    ).length;
    const currentProgress = stageProgress[THINKING_STAGES[currentStage]?.id] || 0;
    const overall = ((completedStages + currentProgress / 100) / THINKING_STAGES.length) * 100;
    setOverallProgress(overall);
  }, [stageStatuses, stageProgress, currentStage]);

  // Public API to set stage programmatically
  const setStage = (stageId, status = StageStatus.ACTIVE) => {
    const stageIdx = THINKING_STAGES.findIndex((s) => s.id === stageId);
    if (stageIdx !== -1) {
      setCurrentStage(stageIdx);
      setStageStatuses((prev) => ({
        ...prev,
        [stageId]: status,
      }));
    }
  };

  // Handle stage click
  const handleStageClick = (stageId) => {
    setExpandedStage(expandedStage === stageId ? null : stageId);
  };

  if (compact) {
    // Compact horizontal view
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              Red Team Thinking Pipeline
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              {Math.round(overallProgress)}% Complete
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="py-2">
          <div className="flex items-center gap-2">
            {THINKING_STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const status = stageStatuses[stage.id];
              const isActive = status === StageStatus.ACTIVE;
              const isCompleted = status === StageStatus.COMPLETED;

              return (
                <div
                  key={stage.id}
                  className={`
                    relative flex items-center justify-center p-2 rounded-lg transition-all
                    ${stage.bgColor} ${stage.borderColor} border
                    ${isActive ? "ring-2 ring-offset-1 ring-offset-background scale-110" : ""}
                  `}
                  style={{
                    boxShadow: isActive ? `0 0 15px ${stage.color}40` : undefined,
                  }}
                  title={`${stage.name}: ${stage.description}`}
                >
                  {isActive && (
                    <div
                      className="absolute inset-0 rounded-lg animate-pulse opacity-30"
                      style={{ backgroundColor: stage.color }}
                    />
                  )}
                  <Icon
                    className={`h-4 w-4 ${isActive ? "animate-pulse" : ""}`}
                    style={{ color: isCompleted ? "#10B981" : stage.color }}
                  />
                  {isCompleted && (
                    <CheckCircle2 className="absolute -top-1 -right-1 h-3 w-3 text-green-400 bg-background rounded-full" />
                  )}
                </div>
              );
            })}
          </div>
          <Progress value={overallProgress} className="mt-3 h-1" />
        </CardContent>
      </Card>
    );
  }

  // Full grid view
  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
              <span>Red Team Attack Pipeline</span>
            </div>
            {battleId && (
              <Badge variant="outline" className="font-mono text-xs">
                Battle: {battleId}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">
              Stage {currentStage + 1}/{THINKING_STAGES.length}
            </span>
            <Badge
              variant="outline"
              className="bg-gradient-to-r from-red-500/20 to-orange-500/20"
            >
              {Math.round(overallProgress)}% Complete
            </Badge>
          </div>
        </div>
        <Progress value={overallProgress} className="mt-3" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {THINKING_STAGES.map((stage, idx) => (
            <StageCard
              key={stage.id}
              stage={stage}
              status={stageStatuses[stage.id]}
              logs={stageLogs[stage.id]}
              progress={stageProgress[stage.id] || 0}
              isExpanded={expandedStage === stage.id}
              onClick={() => handleStageClick(stage.id)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default ThinkingVisualizer;
export { THINKING_STAGES, StageStatus };
