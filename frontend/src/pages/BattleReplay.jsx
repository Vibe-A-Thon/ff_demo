import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Slider } from "../components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../components/ui/dropdown-menu";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../components/ui/collapsible";
import { battleAPI, agentAPI, brcAPI } from "../lib/api";
import { toast } from "sonner";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Clock,
  Activity,
  Shield,
  Sword,
  DollarSign,
  Brain,
  GitCompare,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Share2,
  Link2,
  FileDown,
  FileUp,
  ChevronDown,
} from "lucide-react";

// Comparison Card Component
const ComparisonCard = ({ label, beforeValue, afterValue, format = "number", icon: Icon, color }) => {
  const formatValue = (val) => {
    if (format === "currency") return `$${val?.toLocaleString() || 0}`;
    if (format === "percent") return `${val || 0}%`;
    if (format === "minutes") return `${val || 0}m`;
    return val || 0;
  };

  const before = beforeValue || 0;
  const after = afterValue || 0;
  const diff = format === "currency" || format === "minutes" 
    ? before - after  // Lower is better for money and time
    : after - before; // Higher is better for rate and patterns
  const improved = diff > 0;

  return (
    <Card className="border-border glass-panel">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Icon className={`h-4 w-4 ${color}`} />
          <span className="text-sm text-muted-foreground">{label}</span>
        </div>
        <div className="grid grid-cols-3 gap-2 items-center">
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Before</p>
            <p className="font-mono font-semibold">{formatValue(before)}</p>
          </div>
          <div className="text-center">
            {improved ? (
              <TrendingUp className="h-5 w-5 text-green-400 mx-auto" />
            ) : diff < 0 ? (
              <TrendingDown className="h-5 w-5 text-red-400 mx-auto" />
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">After</p>
            <p className={`font-mono font-semibold ${improved ? 'text-green-400' : diff < 0 ? 'text-red-400' : ''}`}>
              {formatValue(after)}
            </p>
          </div>
        </div>
        {diff !== 0 && (
          <div className={`text-center mt-2 text-xs ${improved ? 'text-green-400' : 'text-red-400'}`}>
            {improved ? '↑' : '↓'} {Math.abs(diff).toFixed(format === "percent" ? 1 : 0)}{format === "percent" ? '%' : format === "minutes" ? 'm' : ''}
            {' '}{improved ? 'improvement' : 'decline'}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Turn Comparison Component
const TurnComparison = ({ beforeTurn, afterTurn, turnIndex }) => {
  if (!beforeTurn && !afterTurn) return null;

  return (
    <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-900/50 rounded-lg">
      {/* Before */}
      <div className={`p-3 rounded-lg border ${beforeTurn ? 'border-red-500/30 bg-red-500/5' : 'border-border'}`}>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className="border-red-500 text-red-400">Before</Badge>
          <span className="text-xs text-muted-foreground">Turn {turnIndex + 1}</span>
          {beforeTurn?.stage && (
            <Badge variant="outline" className="border-zinc-600 text-zinc-300">
              {beforeTurn.stage}
            </Badge>
          )}
        </div>
        {beforeTurn ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Sword className="h-3 w-3 text-red-400" />
              <span className="text-sm">{beforeTurn.red_team?.action || 'N/A'}</span>
              {beforeTurn.red_team?.success && (
                <Badge className="bg-red-500/20 text-red-400 text-xs">Success</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-3 w-3 text-blue-400" />
              <span className="text-sm">{beforeTurn.blue_team?.action || 'N/A'}</span>
              {beforeTurn.blue_team?.blocked && (
                <Badge className="bg-blue-500/20 text-blue-400 text-xs">Blocked</Badge>
              )}
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">No data</p>
        )}
      </div>

      {/* After */}
      <div className={`p-3 rounded-lg border ${afterTurn ? 'border-green-500/30 bg-green-500/5' : 'border-border'}`}>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className="border-green-500 text-green-400">After</Badge>
          <span className="text-xs text-muted-foreground">Turn {turnIndex + 1}</span>
          {afterTurn?.stage && (
            <Badge variant="outline" className="border-zinc-600 text-zinc-300">
              {afterTurn.stage}
            </Badge>
          )}
        </div>
        {afterTurn ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Sword className="h-3 w-3 text-red-400" />
              <span className="text-sm">{afterTurn.red_team?.action || 'N/A'}</span>
              {afterTurn.red_team?.success && (
                <Badge className="bg-red-500/20 text-red-400 text-xs">Success</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-3 w-3 text-blue-400" />
              <span className="text-sm">{afterTurn.blue_team?.action || 'N/A'}</span>
              {afterTurn.blue_team?.blocked && (
                <Badge className="bg-blue-500/20 text-blue-400 text-xs">Blocked</Badge>
              )}
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">No data</p>
        )}
      </div>
    </div>
  );
};

const BattleReplay = () => {
  const [battles, setBattles] = useState([]);
  const [beforeBattle, setBeforeBattle] = useState(null);
  const [afterBattle, setAfterBattle] = useState(null);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState([1]);
  const [syncPlayback, setSyncPlayback] = useState(true);
  const playbackRef = useRef(null);
  const fileInputRef = useRef(null);
  const [brcFile, setBrcFile] = useState(null);
  const [brcValidation, setBrcValidation] = useState(null);
  const [brcPreview, setBrcPreview] = useState(null);
  const [isValidatingBrc, setIsValidatingBrc] = useState(false);
  const [isPreviewingBrc, setIsPreviewingBrc] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [stageTeamFilter, setStageTeamFilter] = useState("all");
  const [stageAgentFilter, setStageAgentFilter] = useState("all");
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const brcFileRef = useRef(null);

  useEffect(() => {
    loadBattles();
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
      if (playbackRef.current) clearInterval(playbackRef.current);
    };
  }, []);

  const loadBattles = async () => {
    try {
      const response = await battleAPI.getAll();
      const completedBattles = response.data.filter(b => 
        b.status === "completed" && b.turns && b.turns.length > 0
      );
      setBattles(completedBattles);
      
      // Auto-select first two battles for comparison
      if (completedBattles.length >= 2) {
        setBeforeBattle(completedBattles[0]);
        setAfterBattle(completedBattles[1]);
      } else if (completedBattles.length === 1) {
        setBeforeBattle(completedBattles[0]);
      }
    } catch (error) {
      console.error("Failed to load battles:", error);
    }
  };

  const maxTurns = Math.max(
    beforeBattle?.turns?.length || 0,
    afterBattle?.turns?.length || 0
  );

  // Playback control
  useEffect(() => {
    if (isPlaying && maxTurns > 0) {
      const interval = 2000 / playbackSpeed[0];
      playbackRef.current = setInterval(() => {
        setCurrentTurn(prev => {
          if (prev >= maxTurns - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, interval);
    } else {
      if (playbackRef.current) clearInterval(playbackRef.current);
    }
    return () => {
      if (playbackRef.current) clearInterval(playbackRef.current);
    };
  }, [isPlaying, playbackSpeed, maxTurns]);

  const togglePlayback = () => {
    if (currentTurn >= maxTurns - 1) {
      setCurrentTurn(0);
    }
    setIsPlaying(!isPlaying);
  };

  const stepForward = () => {
    if (currentTurn < maxTurns - 1) {
      setCurrentTurn(currentTurn + 1);
    }
  };

  const stepBackward = () => {
    if (currentTurn > 0) {
      setCurrentTurn(currentTurn - 1);
    }
  };

  const reset = () => {
    setCurrentTurn(0);
    setIsPlaying(false);
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Share link copied");
  };

  const handleImportBrc = async (event) => {
    const file = event?.target?.files?.[0] || brcFile;
    if (!file) return;
    setIsImporting(true);
    try {
      if (!brcFile) {
        setBrcFile(file);
      }
      const validateForm = new FormData();
      validateForm.append("file", file);
      const validateResponse = await brcAPI.validate(validateForm);
      setBrcValidation(validateResponse.data);
      if (!validateResponse.data?.valid) {
        toast.error("BRC validation failed");
        return;
      }

      const previewForm = new FormData();
      previewForm.append("file", file);
      const previewResponse = await brcAPI.preview(previewForm);
      setBrcPreview(previewResponse.data);

      const formData = new FormData();
      formData.append("file", file);
      const response = await battleAPI.importBrc(formData);
      toast.success("BRC imported");
      await loadBattles();
      if (response?.data) {
        setAfterBattle(response.data);
        setBeforeBattle((prev) => prev || response.data);
      }
    } catch (error) {
      toast.error("Failed to import BRC");
    } finally {
      setIsImporting(false);
      if (event?.target) event.target.value = "";
    }
  };

  const handleSelectBrcFile = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBrcFile(file);
    setBrcValidation(null);
    setBrcPreview(null);
  };

  const handleValidateBrc = async () => {
    if (!brcFile) return;
    setIsValidatingBrc(true);
    try {
      const formData = new FormData();
      formData.append("file", brcFile);
      const response = await brcAPI.validate(formData);
      setBrcValidation(response.data);
      if (response.data?.valid) {
        toast.success("BRC validation passed");
      } else {
        toast.error("BRC validation failed");
      }
    } catch (error) {
      toast.error("Failed to validate BRC");
    } finally {
      setIsValidatingBrc(false);
    }
  };

  const handlePreviewBrc = async () => {
    if (!brcFile) return;
    setIsPreviewingBrc(true);
    try {
      const formData = new FormData();
      formData.append("file", brcFile);
      const response = await brcAPI.preview(formData);
      setBrcPreview(response.data);
      toast.success("BRC preview ready");
    } catch (error) {
      toast.error("Failed to preview BRC");
    } finally {
      setIsPreviewingBrc(false);
    }
  };

  const handleDownloadSummary = () => {
    const summary = {
      generated_at: new Date().toISOString(),
      before: {
        id: beforeBattle?.id,
        scenario: beforeBattle?.scenario_name,
        metrics: beforeFinalMetrics,
      },
      after: {
        id: afterBattle?.id,
        scenario: afterBattle?.scenario_name,
        metrics: afterFinalMetrics,
      },
    };
    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "battle-replay-summary.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success("Summary downloaded");
  };

  const handleExportGif = () => {
    toast.info("Generating highlight GIF...");
    setTimeout(() => toast.success("Demo GIF ready (mock export)"), 1200);
  };

  const beforeTurn = beforeBattle?.turns?.[currentTurn];
  const afterTurn = afterBattle?.turns?.[currentTurn];
  const renderStagePayload = (payload) => {
    if (!payload) return "No output captured.";
    try {
      return JSON.stringify(payload, null, 2);
    } catch (error) {
      return String(payload);
    }
  };

  const buildStageEntries = (turn) => {
    if (!turn?.stage_outputs) return [];
    return Object.entries(turn.stage_outputs)
      .filter(([team]) => team)
      .map(([team, payload]) => ({
        team,
        agent: payload?.agent || payload?.agent_id || payload?.agent_name || "",
        payload,
      }));
  };

  const filterStageEntries = (entries) => {
    return entries.filter((entry) => {
      if (stageTeamFilter !== "all" && entry.team !== stageTeamFilter) return false;
      if (stageAgentFilter !== "all" && entry.agent !== stageAgentFilter) return false;
      return true;
    });
  };

  const rawBeforeEntries = buildStageEntries(beforeTurn);
  const rawAfterEntries = buildStageEntries(afterTurn);
  const beforeEntries = filterStageEntries(rawBeforeEntries);
  const afterEntries = filterStageEntries(rawAfterEntries);
  const availableAgents = Array.from(
    new Set([...rawBeforeEntries, ...rawAfterEntries].map((entry) => entry.agent).filter(Boolean))
  );

  // Calculate final metrics
  const beforeFinalMetrics = beforeBattle?.metrics || {};
  const afterFinalMetrics = afterBattle?.metrics || {};

  return (
    <div className="h-full flex flex-col" data-testid="battle-replay">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <GitCompare className="h-5 w-5 text-blue-400" />
              Battle Replay & Comparison
            </h1>
            <p className="text-sm text-muted-foreground">Compare battle performance before and after rule changes</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".brc,application/octet-stream"
              className="hidden"
              onChange={handleImportBrc}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isImporting}
              data-testid="import-brc-btn"
            >
              <FileUp className="h-4 w-4 mr-2" />
              Import BRC
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" data-testid="share-replay-btn">
                  <Share2 className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Share Options</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleCopyShareLink}>
                  <Link2 className="h-4 w-4 mr-2" />
                  Copy replay link
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExportGif}>
                  <Share2 className="h-4 w-4 mr-2" />
                  Export highlight GIF
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDownloadSummary}>
                  <FileDown className="h-4 w-4 mr-2" />
                  Download summary JSON
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-6">
          {/* Battle Selection */}
          <div className="grid grid-cols-2 gap-4 p-4 border-b border-border bg-zinc-900/50">
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Before (Baseline)</Label>
          <Select
            value={beforeBattle?.id || ""}
            onValueChange={(id) => {
              setBeforeBattle(battles.find(b => b.id === id));
              setCurrentTurn(0);
            }}
          >
            <SelectTrigger data-testid="before-battle-select">
              <SelectValue placeholder="Select baseline battle" />
            </SelectTrigger>
            <SelectContent>
              {battles.map((battle) => (
                <SelectItem key={battle.id} value={battle.id} disabled={battle.id === afterBattle?.id}>
                  {battle.scenario_name} ({battle.turns?.length || 0} turns)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">After (Comparison)</Label>
          <Select
            value={afterBattle?.id || ""}
            onValueChange={(id) => {
              setAfterBattle(battles.find(b => b.id === id));
              setCurrentTurn(0);
            }}
          >
            <SelectTrigger data-testid="after-battle-select">
              <SelectValue placeholder="Select comparison battle" />
            </SelectTrigger>
            <SelectContent>
              {battles.map((battle) => (
                <SelectItem key={battle.id} value={battle.id} disabled={battle.id === beforeBattle?.id}>
                  {battle.scenario_name} ({battle.turns?.length || 0} turns)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="px-4 pb-4 border-b border-border bg-zinc-900/50">
        <Card className="border-border" data-testid="battle-replay-registry">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Registry Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-muted-foreground">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="border-border">
                {registrySnapshot?.teams?.length || 0} teams
              </Badge>
              <Badge variant="outline" className="border-border">
                {registrySnapshot?.agents?.length || 0} agents
              </Badge>
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              {(registrySnapshot?.delegation_preview || []).slice(0, 3).map((item) => (
                <div key={item.agent_id} className="rounded-md border border-border bg-zinc-900/40 p-2">
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
      </div>

      {/* Playback Controls */}
      <div className="p-4 border-b border-border bg-zinc-900/50">
        <Card className="border-border mb-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              BRC Validation & Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              ref={brcFileRef}
              type="file"
              accept=".brc,application/octet-stream"
              className="hidden"
              onChange={handleSelectBrcFile}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => brcFileRef.current?.click()}
              >
                <FileUp className="h-4 w-4 mr-2" />
                Choose BRC
              </Button>
              <span className="text-xs text-muted-foreground">
                {brcFile ? brcFile.name : "No file selected"}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleValidateBrc}
                disabled={!brcFile || isValidatingBrc}
              >
                Validate
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handlePreviewBrc}
                disabled={!brcFile || isPreviewingBrc}
              >
                Preview
              </Button>
            </div>
            {brcValidation && (
              <div className="text-xs space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className={brcValidation.valid ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}>
                    {brcValidation.valid ? "Valid" : "Invalid"}
                  </Badge>
                  {brcValidation.warnings?.length ? (
                    <Badge className="bg-amber-500/20 text-amber-400">Warnings {brcValidation.warnings.length}</Badge>
                  ) : null}
                </div>
                {brcValidation.errors?.length ? (
                  <ul className="list-disc list-inside text-red-400">
                    {brcValidation.errors.map((error) => (
                      <li key={error}>{error}</li>
                    ))}
                  </ul>
                ) : null}
                {brcValidation.warnings?.length ? (
                  <ul className="list-disc list-inside text-amber-400">
                    {brcValidation.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            )}
            {brcPreview && (
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Artifacts: {brcPreview.artifact_count || 0}</div>
                <div>Stage files: {brcPreview.stage_files?.length || 0}</div>
                <div>Battle type: {brcPreview.manifest?.battle_type || "—"}</div>
                <div>Run ID: {brcPreview.manifest?.run_id || "—"}</div>
                {brcPreview.stage_summary && (
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(brcPreview.stage_summary).map(([stage, count]) => (
                      <Badge key={stage} variant="outline" className="border-zinc-700 text-zinc-300">
                        {stage}: {count}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-2 block">Before (Baseline)</Label>
            <Select
              value={beforeBattle?.id || ""}
              onValueChange={(id) => {
                setBeforeBattle(battles.find(b => b.id === id));
                setCurrentTurn(0);
              }}
            >
              <SelectTrigger data-testid="before-battle-select">
                <SelectValue placeholder="Select baseline battle" />
              </SelectTrigger>
              <SelectContent>
                {battles.map((battle) => (
                  <SelectItem key={battle.id} value={battle.id} disabled={battle.id === afterBattle?.id}>
                    {battle.scenario_name} ({battle.turns?.length || 0} turns)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-2 block">After (Updated)</Label>
            <Select
              value={afterBattle?.id || ""}
              onValueChange={(id) => {
                setAfterBattle(battles.find(b => b.id === id));
                setCurrentTurn(0);
              }}
            >
              <SelectTrigger data-testid="after-battle-select">
                <SelectValue placeholder="Select updated battle" />
              </SelectTrigger>
              <SelectContent>
                {battles.map((battle) => (
                  <SelectItem key={battle.id} value={battle.id} disabled={battle.id === beforeBattle?.id}>
                    {battle.scenario_name} ({battle.turns?.length || 0} turns)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="px-4 py-2 bg-zinc-900/30">
        <div className="flex items-center gap-4">
          <span className="text-sm font-mono w-20">Turn {currentTurn + 1}/{maxTurns}</span>
          <Slider
            value={[currentTurn]}
            onValueChange={([v]) => setCurrentTurn(v)}
            min={0}
            max={Math.max(0, maxTurns - 1)}
            step={1}
            className="flex-1"
          />
        </div>
      </div>

      {/* Main Content */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          {/* Metrics Comparison */}
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Final Metrics Comparison
            </h3>
            <div className="grid grid-cols-4 gap-4">
              <ComparisonCard
                label="Success Rate"
                beforeValue={beforeFinalMetrics.success_rate}
                afterValue={afterFinalMetrics.success_rate}
                format="percent"
                icon={Shield}
                color="text-green-400"
              />
              <ComparisonCard
                label="Money at Risk"
                beforeValue={beforeFinalMetrics.money_at_risk}
                afterValue={afterFinalMetrics.money_at_risk}
                format="currency"
                icon={DollarSign}
                color="text-red-400"
              />
              <ComparisonCard
                label="Time to Immunity"
                beforeValue={beforeFinalMetrics.time_to_immunity}
                afterValue={afterFinalMetrics.time_to_immunity}
                format="minutes"
                icon={Clock}
                color="text-blue-400"
              />
              <ComparisonCard
                label="Patterns Learned"
                beforeValue={beforeFinalMetrics.patterns_learned}
                afterValue={afterFinalMetrics.patterns_learned}
                format="number"
                icon={Brain}
                color="text-purple-400"
              />
            </div>
          </div>

          {/* Turn-by-Turn Comparison */}
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Turn-by-Turn Comparison
            </h3>
            <TurnComparison
              beforeTurn={beforeTurn}
              afterTurn={afterTurn}
              turnIndex={currentTurn}
            />
          </div>

          {/* Stage Outputs */}
          <Card className="border-border">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Stage Outputs Detail
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Select value={stageTeamFilter} onValueChange={setStageTeamFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Team" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All teams</SelectItem>
                      <SelectItem value="red">Red</SelectItem>
                      <SelectItem value="blue">Blue</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select
                    value={stageAgentFilter}
                    onValueChange={setStageAgentFilter}
                    disabled={!availableAgents.length}
                  >
                    <SelectTrigger className="w-[160px]">
                      <SelectValue placeholder="Agent" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All agents</SelectItem>
                      {availableAgents.map((agent) => (
                        <SelectItem key={agent} value={agent}>
                          {agent}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-border bg-zinc-900/40 p-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge className="bg-red-500/20 text-red-400">Before</Badge>
                  <Badge variant="outline" className="border-zinc-600 text-zinc-300">
                    {beforeTurn?.stage || "Stage"}
                  </Badge>
                </div>
                <div className="grid gap-3">
                  {beforeEntries.length ? (
                    beforeEntries.map((entry, idx) => (
                      <Collapsible key={`${entry.team}-${idx}`} defaultOpen={idx === 0}>
                        <CollapsibleTrigger className="flex w-full items-center justify-between rounded border border-border bg-black/30 px-2 py-1 text-xs">
                          <span className="text-muted-foreground capitalize">
                            {entry.team} {entry.agent ? `• ${entry.agent}` : ""}
                          </span>
                          <ChevronDown className="h-3 w-3" />
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <ScrollArea className="h-32 rounded border border-border bg-black/40 p-2 mt-2">
                            <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                              {renderStagePayload(entry.payload)}
                            </pre>
                          </ScrollArea>
                        </CollapsibleContent>
                      </Collapsible>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground">No outputs for filters.</div>
                  )}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-zinc-900/40 p-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge className="bg-blue-500/20 text-blue-300">After</Badge>
                  <Badge variant="outline" className="border-zinc-600 text-zinc-300">
                    {afterTurn?.stage || "Stage"}
                  </Badge>
                </div>
                <div className="grid gap-3">
                  {afterEntries.length ? (
                    afterEntries.map((entry, idx) => (
                      <Collapsible key={`${entry.team}-${idx}`} defaultOpen={idx === 0}>
                        <CollapsibleTrigger className="flex w-full items-center justify-between rounded border border-border bg-black/30 px-2 py-1 text-xs">
                          <span className="text-muted-foreground capitalize">
                            {entry.team} {entry.agent ? `• ${entry.agent}` : ""}
                          </span>
                          <ChevronDown className="h-3 w-3" />
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <ScrollArea className="h-32 rounded border border-border bg-black/40 p-2 mt-2">
                            <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                              {renderStagePayload(entry.payload)}
                            </pre>
                          </ScrollArea>
                        </CollapsibleContent>
                      </Collapsible>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground">No outputs for filters.</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Learning Progress */}
          {(beforeBattle || afterBattle) && (
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-green-400" />
                  Learning Progress Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-zinc-800/50 rounded-lg">
                    <h4 className="text-sm font-medium mb-2">Before Battle Summary</h4>
                    {beforeBattle ? (
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <p>Total Turns: {beforeBattle.turns?.length || 0}</p>
                        <p>Red Team Wins: {beforeBattle.turns?.filter(t => t.red_team?.success).length || 0}</p>
                        <p>Blue Team Blocks: {beforeBattle.turns?.filter(t => t.blue_team?.blocked).length || 0}</p>
                        <p>Final TTI: {beforeBattle.metrics?.time_to_immunity || 0}m</p>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No battle selected</p>
                    )}
                  </div>
                  <div className="p-4 bg-zinc-800/50 rounded-lg">
                    <h4 className="text-sm font-medium mb-2">After Battle Summary</h4>
                    {afterBattle ? (
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <p>Total Turns: {afterBattle.turns?.length || 0}</p>
                        <p>Red Team Wins: {afterBattle.turns?.filter(t => t.red_team?.success).length || 0}</p>
                        <p>Blue Team Blocks: {afterBattle.turns?.filter(t => t.blue_team?.blocked).length || 0}</p>
                        <p>Final TTI: {afterBattle.metrics?.time_to_immunity || 0}m</p>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No battle selected</p>
                    )}
                  </div>
                </div>
                
                {beforeBattle && afterBattle && (
                  <div className={`mt-4 p-4 rounded-lg ${
                    (afterFinalMetrics.time_to_immunity || 10) < (beforeFinalMetrics.time_to_immunity || 10)
                      ? 'bg-green-500/10 border border-green-500/30'
                      : 'bg-yellow-500/10 border border-yellow-500/30'
                  }`}>
                    <p className="text-sm">
                      {(afterFinalMetrics.time_to_immunity || 10) < (beforeFinalMetrics.time_to_immunity || 10) ? (
                        <>
                          <strong className="text-green-400">Improvement Detected:</strong> Time to Immunity decreased from{' '}
                          {beforeFinalMetrics.time_to_immunity || 0}m to {afterFinalMetrics.time_to_immunity || 0}m,
                          showing the system is learning {' '}
                          {Math.round(((beforeFinalMetrics.time_to_immunity || 10) - (afterFinalMetrics.time_to_immunity || 10)) / (beforeFinalMetrics.time_to_immunity || 10) * 100)}% faster.
                        </>
                      ) : (
                        <>
                          <strong className="text-yellow-400">No Significant Improvement:</strong> Time to Immunity remained similar or increased.
                          Consider reviewing rule configurations.
                        </>
                      )}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default BattleReplay;
