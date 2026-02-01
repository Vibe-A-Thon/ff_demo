import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Checkbox } from "../components/ui/checkbox";
import { Label } from "../components/ui/label";
import { evidenceAPI, battleAPI, agentAPI, runAPI, ragAPI, settingsAPI } from "../lib/api";
import { toast } from "sonner";
import {
  FileSearch,
  Download,
  FileText,
  Shield,
  Clock,
  Hash,
  Eye,
  RefreshCw,
  Folder,
  CheckCircle2,
  AlertTriangle,
  Copy,
  ExternalLink,
  Search,
  GitCompare,
  FileJson,
  FileDown,
  Eraser,
} from "lucide-react";

const EvidenceViewer = () => {
  const [evidencePacks, setEvidencePacks] = useState([]);
  const [selectedPack, setSelectedPack] = useState(null);
  const [battles, setBattles] = useState([]);
  const [selectedBattle, setSelectedBattle] = useState("");
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testStatusFilter, setTestStatusFilter] = useState("all");
  const [testQuery, setTestQuery] = useState("");
  const [logQuery, setLogQuery] = useState("");
  const [comparePackId, setComparePackId] = useState("");
  const [redactionEnabled, setRedactionEnabled] = useState(true);
  const [redactEmails, setRedactEmails] = useState(true);
  const [redactAccounts, setRedactAccounts] = useState(true);
  const [redactPhones, setRedactPhones] = useState(false);
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [expandedStages, setExpandedStages] = useState({});
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [artifactDrawerOpen, setArtifactDrawerOpen] = useState(false);
  const [artifactApprovals, setArtifactApprovals] = useState([]);
  const [artifactFilter, setArtifactFilter] = useState(null);
  const [packFilter, setPackFilter] = useState(null);
  const [ragEvalSummary, setRagEvalSummary] = useState(null);
  const [ragAlerts, setRagAlerts] = useState([]);
  const [ragSettings, setRagSettings] = useState(null);

  useEffect(() => {
    loadData();
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

  useEffect(() => {
    const loadRagSummary = async () => {
      try {
        const [historyRes, alertsRes, settingsRes] = await Promise.all([
          ragAPI.evaluationHistory({ limit: 1 }),
          ragAPI.evaluationAlerts({ limit: 5 }),
          settingsAPI.get(),
        ]);
        setRagEvalSummary(historyRes?.data?.items?.[0] || null);
        setRagAlerts(alertsRes?.data?.items || []);
        setRagSettings(settingsRes?.data?.rag || null);
      } catch (error) {
        setRagEvalSummary(null);
        setRagAlerts([]);
        setRagSettings(null);
      }
    };
    loadRagSummary();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [evidenceRes, battlesRes, runsRes] = await Promise.all([
        evidenceAPI.getAll(),
        battleAPI.getAll(),
        runAPI.getAll(),
      ]);
      setEvidencePacks(evidenceRes.data);
      setBattles(battlesRes.data);
      setRuns(runsRes.data || []);
      if (evidenceRes.data.length > 0) {
        setSelectedPack(evidenceRes.data[0]);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateEvidencePack = async () => {
    if (!selectedBattle) {
      toast.error("Please select a battle");
      return;
    }
    setGenerating(true);
    try {
      const response = await evidenceAPI.generate(selectedBattle);
      setEvidencePacks([...evidencePacks, response.data]);
      setSelectedPack(response.data);
      toast.success("Evidence pack generated!");
    } catch (error) {
      toast.error("Failed to generate evidence pack");
    } finally {
      setGenerating(false);
    }
  };

  const generateRunEvidencePack = async () => {
    if (!selectedRun) {
      toast.error("Please select a war loop run");
      return;
    }
    setGenerating(true);
    try {
      const response = await evidenceAPI.generateRun(selectedRun);
      setEvidencePacks([...evidencePacks, response.data]);
      setSelectedPack(response.data);
      toast.success("Evidence pack generated from war loop!");
    } catch (error) {
      toast.error("Failed to generate evidence pack from run");
    } finally {
      setGenerating(false);
    }
  };

  const exportPackAs = async (format) => {
    if (!selectedPack) return;
    if (format === "pdf") {
      const reportWindow = window.open("", "_blank", "noopener,noreferrer");
      if (!reportWindow) {
        toast.error("Popup blocked. Allow popups to export PDF.");
        return;
      }
      const redactedNarrative = applyRedaction(selectedPack.narrative || "");
      const logEntries = normalizeLogs(selectedPack);
      const logsText = logEntries.map((entry) => applyRedaction(formatLogEntry(entry))).join("\n\n");
      const tests = normalizeTests(selectedPack);
      const approvals = normalizeApprovals(selectedPack);
      reportWindow.document.write(`
        <html>
          <head>
            <title>Evidence Pack Report</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 24px; }
              h1, h2 { margin-bottom: 8px; }
              pre { background: #f4f4f4; padding: 12px; white-space: pre-wrap; }
              .section { margin-bottom: 20px; }
              table { width: 100%; border-collapse: collapse; }
              td, th { border: 1px solid #ddd; padding: 8px; }
              th { background: #f0f0f0; text-align: left; }
            </style>
          </head>
          <body>
            <h1>Evidence Pack Report</h1>
            <div class="section">
              <h2>Pack Metadata</h2>
              <table>
                <tr><th>ID</th><td>${selectedPack.id}</td></tr>
                <tr><th>Battle</th><td>${selectedPack.battle_id || "N/A"}</td></tr>
                <tr><th>Run</th><td>${selectedPack.run_id || "N/A"}</td></tr>
                <tr><th>Created</th><td>${new Date(selectedPack.created_at).toLocaleString()}</td></tr>
                <tr><th>Confidence</th><td>${Math.round(selectedPack.confidence * 100)}%</td></tr>
              </table>
            </div>
            <div class="section">
              <h2>XAI Narrative</h2>
              <p>${redactedNarrative}</p>
            </div>
            <div class="section">
              <h2>Approvals</h2>
              <pre>${approvals.map((item) => `${item.stage || item.role || "Approval"}: ${item.approver_id || item.approver || "Unknown"} (${item.status || "approved"})`).join("\n")}</pre>
            </div>
            <div class="section">
              <h2>Tests</h2>
              <pre>${tests.map((test) => `${test.name || test.id || "Test"} - ${test.status || "unknown"}`).join("\n")}</pre>
            </div>
            <div class="section">
              <h2>Logs</h2>
              <pre>${logsText}</pre>
            </div>
          </body>
        </html>
      `);
      reportWindow.document.close();
      reportWindow.focus();
      reportWindow.print();
      toast.success("PDF export opened. Save as PDF from the print dialog.");
      return;
    }
    try {
      const response = await evidenceAPI.export(selectedPack.id);
      const data = response.data;
      const exportData = data?.pack ? data.pack : data;
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data?.filename || `evidence-pack-${selectedPack.id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Evidence pack exported!");
    } catch (error) {
      toast.error("Export failed");
    }
  };

  const copyChecksum = () => {
    if (selectedPack?.checksum) {
      navigator.clipboard.writeText(selectedPack.checksum);
      toast.success("Checksum copied to clipboard!");
    }
  };

  const applyRedaction = (value) => {
    if (!redactionEnabled || !value) return value;
    let output = value;
    if (redactEmails) {
      output = output.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[REDACTED_EMAIL]");
    }
    if (redactPhones) {
      output = output.replace(/\b\+?\d{1,3}?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/g, "[REDACTED_PHONE]");
    }
    if (redactAccounts) {
      output = output.replace(/\b\d{10,18}\b/g, "[REDACTED_ACCOUNT]");
    }
    return output;
  };

  const normalizeTests = (pack) => {
    const raw = pack?.test_results || pack?.tests || pack?.testResults || [];
    if (Array.isArray(raw)) return raw;
    if (raw?.results && Array.isArray(raw.results)) return raw.results;
    if (raw?.unit || raw?.integration) {
      return [...(raw.unit || []), ...(raw.integration || [])];
    }
    return [];
  };

  const normalizeLogs = (pack) => {
    const raw = pack?.logs || [];
    if (Array.isArray(raw)) return raw;
    return [raw];
  };

  const getArtifactsFromPack = (pack) => {
    if (Array.isArray(pack?.artifacts) && pack.artifacts.length > 0) {
      return pack.artifacts;
    }
    const logs = normalizeLogs(pack);
    return logs
      .filter((entry) => ["agent.output", "orchestrator.output"].includes(entry?.event_type))
      .map((entry) => ({
        event_id: entry.id,
        event_type: entry.event_type,
        team: entry?.payload?.team,
        agent: entry?.payload?.agent,
        outputs: entry?.payload?.outputs || {},
        created_at: entry?.created_at,
      }));
  };

  const bucketArtifactsByStage = (artifacts, timeline) => {
    const buckets = {};
    if (!Array.isArray(artifacts)) return buckets;
    const stages = Array.isArray(timeline)
      ? [...timeline].filter((item) => item?.timestamp).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      : [];
    artifacts.forEach((artifact) => {
      let stageKey = "unknown";
      if (stages.length && artifact?.created_at) {
        const artifactTime = new Date(artifact.created_at).getTime();
        for (let i = 0; i < stages.length; i += 1) {
          const stageTime = new Date(stages[i].timestamp).getTime();
          if (artifactTime >= stageTime) {
            stageKey = stages[i].stage || stageKey;
          } else {
            break;
          }
        }
      }
      if (!buckets[stageKey]) buckets[stageKey] = [];
      buckets[stageKey].push(artifact);
    });
    return buckets;
  };

  const normalizeApprovals = (pack) => {
    const raw = pack?.approval_chain || pack?.approvals || [];
    if (Array.isArray(raw)) return raw;
    return [raw];
  };

  const buildStageTimeline = (pack) => {
    const summaries = pack?.stage_summaries || pack?.stageSummaries || [];
    if (Array.isArray(summaries) && summaries.length > 0) {
      return summaries.map((item, idx) => ({
        id: `${item.stage || "stage"}-${idx}`,
        stage: item.stage,
        step: item.step,
        timestamp: item.timestamp,
      }));
    }
    const logs = normalizeLogs(pack);
    const derived = logs
      .filter((entry) => (entry?.event_type || entry?.eventType) === "stage.changed")
      .map((entry, idx) => ({
        id: `${entry?.payload?.stage || "stage"}-${idx}`,
        stage: entry?.payload?.stage,
        step: entry?.payload?.step,
        timestamp: entry?.created_at || entry?.timestamp,
      }));
    return derived;
  };

  const formatLogEntry = (entry) => {
    if (typeof entry === "string") return entry;
    try {
      return JSON.stringify(entry, null, 2);
    } catch (error) {
      return String(entry);
    }
  };

  const comparePack = evidencePacks.find((pack) => pack.id === comparePackId) || null;
  const tests = normalizeTests(selectedPack);
  const filteredTests = tests.filter((test) => {
    const status = (test.status || test.result || (test.passed ? "passed" : "failed") || "unknown").toLowerCase();
    if (testStatusFilter !== "all" && status !== testStatusFilter) return false;
    if (!testQuery) return true;
    const target = `${test.name || ""} ${test.id || ""} ${test.message || ""}`.toLowerCase();
    return target.includes(testQuery.toLowerCase());
  });

  const applyArtifactFilter = (stage) => {
    setArtifactFilter({ stage });
    toast.success(`Filtered artifacts for ${stage}`);
  };

  const clearArtifactFilter = () => {
    setArtifactFilter(null);
    toast.success("Artifact filter cleared");
  };

  const applyPackFilter = (type, value) => {
    if (!value) return;
    setPackFilter({ type, value });
    toast.success(`Filtered packs by ${type}`);
  };

  const clearPackFilter = () => {
    setPackFilter(null);
    toast.success("Pack filter cleared");
  };

  const filteredPacks = packFilter
    ? evidencePacks.filter((pack) => {
        if (packFilter.type === "run") return pack.run_id === packFilter.value;
        if (packFilter.type === "battle") return pack.battle_id === packFilter.value;
        if (packFilter.type === "parent") return pack.lineage?.parent_pack_id === packFilter.value;
        if (packFilter.type === "derived") return pack.lineage?.derived_from === packFilter.value;
        return true;
      })
    : evidencePacks;

  useEffect(() => {
    if (filteredPacks.length === 0) return;
    if (!selectedPack || !filteredPacks.find((pack) => pack.id === selectedPack.id)) {
      setSelectedPack(filteredPacks[0]);
    }
  }, [packFilter, evidencePacks, filteredPacks, selectedPack]);

  const effectivePack = selectedPack && filteredPacks.find((pack) => pack.id === selectedPack.id)
    ? selectedPack
    : filteredPacks[0] || selectedPack;

  const logEntries = normalizeLogs(effectivePack);
  const filteredLogs = logEntries.filter((entry) => {
    if (!logQuery) return true;
    return formatLogEntry(entry).toLowerCase().includes(logQuery.toLowerCase());
  });

  const approvalChain = normalizeApprovals(effectivePack);
  const approvalsByStage = approvalChain.reduce((acc, approval) => {
    const stage = approval.stage || approval.action || approval.approval_action;
    if (!stage) return acc;
    if (!acc[stage]) acc[stage] = [];
    acc[stage].push(approval);
    return acc;
  }, {});
  const xaiBundle = effectivePack?.xai_bundle || effectivePack?.xaiBundle || null;
  const stageTimeline = buildStageTimeline(effectivePack);
  const artifacts = getArtifactsFromPack(effectivePack || {});
  const filteredArtifacts = artifactFilter?.stage
    ? artifacts.filter((artifact) => {
        if (!artifact?.created_at) return true;
        const artifactTime = new Date(artifact.created_at).getTime();
        const stages = stageTimeline
          .filter((item) => item?.timestamp)
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        let activeStage = "unknown";
        for (let i = 0; i < stages.length; i += 1) {
          const stageTime = new Date(stages[i].timestamp).getTime();
          if (artifactTime >= stageTime) {
            activeStage = stages[i].stage || activeStage;
          } else {
            break;
          }
        }
        return activeStage === artifactFilter.stage;
      })
    : artifacts;
  const artifactsByStage = bucketArtifactsByStage(filteredArtifacts, stageTimeline);

  const openArtifactDrawer = (artifact, stage) => {
    setSelectedArtifact({ ...artifact, stage });
    setArtifactApprovals(approvalsByStage[stage] || []);
    setArtifactDrawerOpen(true);
  };

  const closeArtifactDrawer = () => {
    setArtifactDrawerOpen(false);
    setSelectedArtifact(null);
    setArtifactApprovals([]);
  };

  return (
    <div className="h-full flex" data-testid="evidence-viewer">
      {/* Pack List */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold mb-4">Evidence Packs</h2>
          {packFilter && (
            <div className="mb-3 flex items-center justify-between rounded border border-border bg-black/30 p-2 text-xs">
              <span>
                Filtering packs by {packFilter.type}: <span className="font-mono">{packFilter.value}</span>
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearPackFilter}
                data-testid="clear-pack-filter"
              >
                Clear
              </Button>
            </div>
          )}
          
          {/* Generate New */}
          <div className="space-y-2">
            <Select value={selectedBattle} onValueChange={setSelectedBattle}>
              <SelectTrigger data-testid="battle-select-evidence">
                <SelectValue placeholder="Select battle" />
              </SelectTrigger>
              <SelectContent>
                {battles.filter(b => b.status === "completed").map((battle) => (
                  <SelectItem key={battle.id} value={battle.id}>
                    {battle.scenario_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              className="w-full"
              onClick={generateEvidencePack}
              disabled={!selectedBattle || generating}
              data-testid="generate-evidence-btn"
              data-explain="Generate Evidence Pack"
              data-explain-title="Evidence pack generated"
              data-explain-summary="Creates a compliance-grade evidence bundle from a completed battle with rule triggers, scores, and artifacts."
              data-explain-rules="EV-001,EV-014"
              data-explain-evidence="Battle timeline,Rule hits,Score traces"
            >
              <FileSearch className={`h-4 w-4 mr-2 ${generating ? 'animate-spin' : ''}`} />
              Generate Pack
            </Button>
            <Select value={selectedRun} onValueChange={setSelectedRun}>
              <SelectTrigger data-testid="run-select-evidence">
                <SelectValue placeholder="Select war loop run" />
              </SelectTrigger>
              <SelectContent>
                {runs.map((run) => (
                  <SelectItem key={run.id} value={run.id}>
                    {run.scenario_id} • {run.id.slice(0, 8)}...
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              className="w-full"
              variant="secondary"
              onClick={generateRunEvidencePack}
              disabled={!selectedRun || generating}
              data-testid="generate-evidence-run-btn"
              data-explain="Generate Evidence Pack (War Loop)"
              data-explain-title="War loop evidence pack generated"
              data-explain-summary="Builds evidence from war loop artifacts, approvals, and workflow history."
              data-explain-rules="EV-001,EV-014"
              data-explain-evidence="War loop artifacts,Approvals,Workflow history"
            >
              <FileSearch className={`h-4 w-4 mr-2 ${generating ? 'animate-spin' : ''}`} />
              Generate War Loop Pack
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {filteredPacks.map((pack) => (
              <div
                key={pack.id}
                onClick={() => setSelectedPack(pack)}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedPack?.id === pack.id
                    ? "border-yellow-500 bg-yellow-500/10"
                    : "border-border hover:border-zinc-600 bg-card"
                }`}
                data-testid={`evidence-pack-${pack.id}`}
              >
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4 text-yellow-400" />
                  <span className="font-mono text-sm truncate">
                    {pack.id.slice(0, 8)}...
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {new Date(pack.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {pack.triggered_rules?.length || 0} rules
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {Math.round(pack.confidence * 100)}% conf.
                  </Badge>
                </div>
              </div>
            ))}
            {filteredPacks.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <FileSearch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No evidence packs yet</p>
                <p className="text-sm">Generate from a battle or war loop run</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Pack Details */}
      <div className="flex-1 overflow-hidden">
        {selectedPack ? (
          <ScrollArea className="h-full">
            <div className="p-6 space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-2">
                    <FileSearch className="h-6 w-6 text-yellow-400" />
                    Evidence Pack
                  </h1>
                  <p className="text-muted-foreground mt-1 font-mono text-sm">
                    ID: {selectedPack.id}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => exportPackAs("json")}
                    data-testid="export-json-btn"
                    data-explain="Export Evidence JSON"
                    data-explain-title="Evidence export"
                    data-explain-summary="Downloads evidence metadata and artifacts as JSON for audit archival."
                    data-explain-rules="EV-021,EV-032"
                    data-explain-evidence="Checksum,Artifacts,Audit log"
                  >
                    <FileJson className="h-4 w-4 mr-2" />
                    Export JSON
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => exportPackAs("pdf")}
                    data-testid="export-pdf-btn"
                    data-explain="Export Evidence PDF"
                    data-explain-title="Evidence PDF report"
                    data-explain-summary="Opens a printable report for regulators with redactions applied."
                    data-explain-rules="EV-021,EV-032"
                    data-explain-evidence="Checksum,Artifacts,Audit log"
                  >
                    <FileDown className="h-4 w-4 mr-2" />
                    Export PDF
                  </Button>
                  <Button
                    onClick={() => exportPackAs("zip")}
                    data-testid="export-evidence-btn"
                    data-explain="Export Evidence Pack"
                    data-explain-title="Evidence export"
                    data-explain-summary="Packages evidence into a tamper-evident archive with checksum and audit trail."
                    data-explain-rules="EV-021,EV-032"
                    data-explain-evidence="Checksum,Artifacts,Audit log"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export ZIP
                  </Button>
                </div>
              </div>

              <Card className="border-border" data-testid="evidence-registry">
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

              <Card className="border-border" data-testid="evidence-rag-summary">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-400" />
                    RAG Evaluation Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {ragEvalSummary ? (
                    <>
                      <div className="grid gap-3 md:grid-cols-3">
                        <div className="rounded-md border border-border p-3">
                          <p className="text-xs text-muted-foreground">Faithfulness</p>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-mono text-foreground">
                              {ragEvalSummary?.metrics?.avg_faithfulness?.toFixed?.(3) ?? "—"}
                            </p>
                            {ragSettings && (
                              <Badge className={(ragEvalSummary?.metrics?.avg_faithfulness || 0) < (ragSettings.faithfulness_warn ?? 0.75)
                                ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                                : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                                {(ragEvalSummary?.metrics?.avg_faithfulness || 0) < (ragSettings.faithfulness_warn ?? 0.75) ? "WARN" : "OK"}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="rounded-md border border-border p-3">
                          <p className="text-xs text-muted-foreground">Relevancy</p>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-mono text-foreground">
                              {ragEvalSummary?.metrics?.avg_answer_relevancy?.toFixed?.(3) ?? "—"}
                            </p>
                            {ragSettings && (
                              <Badge className={(ragEvalSummary?.metrics?.avg_answer_relevancy || 0) < (ragSettings.relevancy_warn ?? 0.75)
                                ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                                : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                                {(ragEvalSummary?.metrics?.avg_answer_relevancy || 0) < (ragSettings.relevancy_warn ?? 0.75) ? "WARN" : "OK"}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="rounded-md border border-border p-3">
                          <p className="text-xs text-muted-foreground">Alerts</p>
                          <p className="text-sm font-mono text-foreground">
                            {ragAlerts.length}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Latest evaluation: {ragEvalSummary.created_at}
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">No RAG evaluation data available.</p>
                  )}
                </CardContent>
              </Card>

              {/* Redaction Controls */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eraser className="h-5 w-5 text-blue-400" />
                    Redaction Controls (PII Removal)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-6">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="redaction-enabled"
                        checked={redactionEnabled}
                        onCheckedChange={(value) => setRedactionEnabled(Boolean(value))}
                        data-testid="redaction-toggle"
                      />
                      <Label htmlFor="redaction-enabled">Enable redaction</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="redaction-email"
                        checked={redactEmails}
                        onCheckedChange={(value) => setRedactEmails(Boolean(value))}
                        data-testid="redaction-email"
                      />
                      <Label htmlFor="redaction-email">Mask emails</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="redaction-account"
                        checked={redactAccounts}
                        onCheckedChange={(value) => setRedactAccounts(Boolean(value))}
                        data-testid="redaction-account"
                      />
                      <Label htmlFor="redaction-account">Mask account numbers</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="redaction-phone"
                        checked={redactPhones}
                        onCheckedChange={(value) => setRedactPhones(Boolean(value))}
                        data-testid="redaction-phone"
                      />
                      <Label htmlFor="redaction-phone">Mask phone numbers</Label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border" data-testid="evidence-xai-bundle">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-yellow-400" />
                    XAI Bundle
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  {xaiBundle ? (
                    <>
                      <div>
                        <p className="text-sm font-semibold">Summary</p>
                        <p className="text-xs text-muted-foreground">{xaiBundle.summary}</p>
                      </div>
                      <div>
                        <p className="text-sm font-semibold">Details</p>
                        <p className="text-xs text-muted-foreground">{xaiBundle.details}</p>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        <div className="rounded-md border border-border bg-zinc-900/40 p-3">
                          <p className="text-xs font-semibold mb-2">Counterfactuals</p>
                          <ul className="space-y-2 text-xs text-muted-foreground">
                            {(xaiBundle.counterfactuals || []).map((item, idx) => (
                              <li key={`${item.label}-${idx}`}>
                                <span className="text-white">{item.label}</span>
                                <div>Expected: {item.expected_outcome}</div>
                              </li>
                            ))}
                            {(!xaiBundle.counterfactuals || xaiBundle.counterfactuals.length === 0) && (
                              <li>No counterfactuals provided.</li>
                            )}
                          </ul>
                        </div>
                        <div className="rounded-md border border-border bg-zinc-900/40 p-3">
                          <p className="text-xs font-semibold mb-2">Similar Cases</p>
                          <ul className="space-y-2 text-xs text-muted-foreground">
                            {(xaiBundle.similar_cases || []).map((item, idx) => (
                              <li key={`${item.case_id}-${idx}`}>
                                <span className="text-white">{item.case_id}</span>
                                <div>{item.summary}</div>
                              </li>
                            ))}
                            {(!xaiBundle.similar_cases || xaiBundle.similar_cases.length === 0) && (
                              <li>No similar cases.</li>
                            )}
                          </ul>
                        </div>
                      </div>
                      <div className="rounded-md border border-border bg-zinc-900/40 p-3">
                        <p className="text-xs font-semibold mb-2">Evidence Graph</p>
                        <div className="text-xs text-muted-foreground">
                          Nodes: {xaiBundle.evidence_graph?.nodes?.length || 0} • Edges: {xaiBundle.evidence_graph?.edges?.length || 0}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-xs text-muted-foreground">No XAI bundle attached to this pack.</div>
                  )}
                </CardContent>
              </Card>

              {/* XAI Narrative */}
              <Card className="border-border border-yellow-500/30 bg-yellow-500/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-yellow-400">
                    <FileText className="h-5 w-5" />
                    Gold Team Explanation (XAI Narrative)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{applyRedaction(selectedPack.narrative)}</p>
                </CardContent>
              </Card>

              {/* Metadata Grid */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <Shield className="h-4 w-4" />
                      <span className="text-sm">Triggered Rules</span>
                    </div>
                    <div className="space-y-1">
                      {selectedPack.triggered_rules?.length > 0 ? (
                        selectedPack.triggered_rules.map((rule, idx) => (
                          <Badge key={idx} variant="outline" className="mr-1 text-xs font-mono">
                            {rule}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground text-sm">No rules triggered</span>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="text-sm">Confidence Score</span>
                    </div>
                    <p className="text-3xl font-bold font-mono">
                      {Math.round(selectedPack.confidence * 100)}%
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <Clock className="h-4 w-4" />
                      <span className="text-sm">Created</span>
                    </div>
                    <p className="text-sm font-mono">
                      {new Date(selectedPack.created_at).toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Contributing Factors */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-400" />
                    Contributing Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedPack.contributing_factors?.map((factor, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                        <span className="font-medium">{factor.factor}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-zinc-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-orange-400 rounded-full"
                              style={{ width: `${factor.weight * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-mono w-12">
                            {Math.round(factor.weight * 100)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Checksum & Lineage */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hash className="h-5 w-5 text-green-400" />
                    Integrity & Lineage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-muted-foreground">Checksum (SHA-256)</label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="flex-1 p-2 bg-black/30 rounded font-mono text-xs break-all">
                          {selectedPack.checksum || "Not computed"}
                        </code>
                        <Button variant="ghost" size="icon" onClick={copyChecksum} data-testid="copy-checksum-btn">
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Battle Reference</label>
                      <p className="font-mono text-sm mt-1">{selectedPack.battle_id || "N/A"}</p>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">War Loop Run</label>
                      <p className="font-mono text-sm mt-1">{selectedPack.run_id || "N/A"}</p>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Lineage Metadata</label>
                      <div className="grid grid-cols-2 gap-3 mt-2 text-sm">
                        <div className="p-2 bg-black/30 rounded">
                          <p className="text-xs text-muted-foreground">Parent Pack</p>
                          <p className="font-mono">{selectedPack.lineage?.parent_pack_id || "N/A"}</p>
                        </div>
                        <div className="p-2 bg-black/30 rounded">
                          <p className="text-xs text-muted-foreground">Derived From</p>
                          <p className="font-mono">{selectedPack.lineage?.derived_from || "N/A"}</p>
                        </div>
                        <div className="p-2 bg-black/30 rounded">
                          <p className="text-xs text-muted-foreground">Rule Version</p>
                          <p className="font-mono">{selectedPack.lineage?.rule_version || selectedPack.rule_version || "N/A"}</p>
                        </div>
                        <div className="p-2 bg-black/30 rounded">
                          <p className="text-xs text-muted-foreground">Pack Fingerprint</p>
                          <p className="font-mono truncate">{selectedPack.lineage?.fingerprint || "N/A"}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Artifacts Timeline */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-cyan-300" />
                    Artifacts Timeline
                    {packFilter && (
                      <Badge variant="outline" className="text-xs">
                        Filtered pack
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {artifactFilter?.stage && (
                    <div className="mb-3 flex items-center justify-between rounded border border-border bg-black/30 p-2 text-xs">
                      <span>
                        Filtering by stage: <span className="font-mono">{artifactFilter.stage}</span>
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearArtifactFilter}
                        data-testid="clear-artifact-filter"
                      >
                        Clear filter
                      </Button>
                    </div>
                  )}
                  {stageTimeline.length > 0 ? (
                    <div className="space-y-3">
                      {stageTimeline.map((item) => (
                        <div key={item.id} className="p-3 rounded-lg border border-border bg-zinc-900/40">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                className="font-medium text-sm text-left hover:text-cyan-200"
                                onClick={() => applyArtifactFilter(item.stage)}
                                data-testid={`filter-stage-${item.stage || "unknown"}`}
                              >
                                {item.stage || "Stage"}
                              </button>
                              <Badge variant="outline" className="text-xs">
                                Step {item.step || "-"}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                Artifacts {artifactsByStage[item.stage]?.length || 0}
                              </Badge>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {item.timestamp ? new Date(item.timestamp).toLocaleString() : "N/A"}
                            </span>
                          </div>
                          <div className="mt-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setExpandedStages((prev) => ({
                                  ...prev,
                                  [item.stage]: !prev[item.stage],
                                }))
                              }
                              data-testid={`toggle-stage-${item.stage || "unknown"}`}
                            >
                              {expandedStages[item.stage] ? "Hide" : "Show"} artifacts
                            </Button>
                          </div>
                          {expandedStages[item.stage] && (
                            <div className="mt-3 space-y-2">
                              {(artifactsByStage[item.stage] || []).map((artifact, idx) => (
                                <div
                                  key={`${item.id}-artifact-${idx}`}
                                  className="rounded bg-black/30 p-2 text-xs"
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="text-[10px]">
                                        {artifact.event_type || "artifact"}
                                      </Badge>
                                      <span className="font-mono">
                                        {(artifact.team || "team").toUpperCase()} / {artifact.agent || "agent"}
                                      </span>
                                    </div>
                                    <span className="text-muted-foreground">
                                      {artifact.created_at
                                        ? new Date(artifact.created_at).toLocaleString()
                                        : "N/A"}
                                    </span>
                                  </div>
                                  <div className="mt-2 flex items-center gap-2">
                                    <Button
                                      variant="secondary"
                                      size="sm"
                                      onClick={() => openArtifactDrawer(artifact, item.stage)}
                                      data-testid={`view-artifact-${item.stage || "unknown"}-${idx}`}
                                    >
                                      View details
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => {
                                        navigator.clipboard.writeText(
                                          JSON.stringify(artifact.outputs || artifact, null, 2)
                                        );
                                        toast.success("Artifact JSON copied");
                                      }}
                                      data-testid={`copy-artifact-${item.stage || "unknown"}-${idx}`}
                                    >
                                      Copy JSON
                                    </Button>
                                  </div>
                                </div>
                              ))}
                              {(!artifactsByStage[item.stage] || artifactsByStage[item.stage].length === 0) && (
                                <div className="text-xs text-muted-foreground">No artifacts recorded.</div>
                              )}
                            </div>
                          )}
                          {approvalsByStage[item.stage]?.length > 0 && (
                            <div className="mt-3 space-y-2">
                              {approvalsByStage[item.stage].map((approval, idx) => (
                                <div
                                  key={`${item.id}-approval-${idx}`}
                                  className="flex items-center justify-between text-xs rounded bg-black/30 p-2"
                                >
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">
                                      {approval.approver_id || approval.approver || "Approver"}
                                    </span>
                                    <Badge variant="outline" className="text-[10px]">
                                      {approval.status || approval.action || "approved"}
                                    </Badge>
                                  </div>
                                  <span className="text-muted-foreground">
                                    {approval.timestamp ? new Date(approval.timestamp).toLocaleString() : "Pending"}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">No stage timeline available.</div>
                  )}
                </CardContent>
              </Card>

              {/* Approval Chain */}
              {approvalChain.length > 0 && (
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-400" />
                      Approval Chain
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {approvalChain.map((approval, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded">
                          <div className="mt-1 h-2 w-2 rounded-full bg-green-400" />
                          <div className="flex-1">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{approval.stage || approval.role || "Approval"}</span>
                                <Badge variant="outline" className="text-xs">
                                  {approval.status || "approved"}
                                </Badge>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {approval.timestamp ? new Date(approval.timestamp).toLocaleString() : "Pending"}
                              </span>
                            </div>
                            <p className="text-sm font-mono mt-1">{approval.approver_id || approval.approver || "Unknown approver"}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Test Results Gallery */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-400" />
                    Test Results Gallery
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-3 mb-4">
                    <Select value={testStatusFilter} onValueChange={setTestStatusFilter}>
                      <SelectTrigger className="w-40" data-testid="test-status-filter">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="passed">Passed</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="skipped">Skipped</SelectItem>
                        <SelectItem value="warning">Warning</SelectItem>
                        <SelectItem value="unknown">Unknown</SelectItem>
                      </SelectContent>
                    </Select>
                    <div className="relative flex-1 min-w-[200px]">
                      <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                      <Input
                        value={testQuery}
                        onChange={(event) => setTestQuery(event.target.value)}
                        placeholder="Search tests"
                        className="pl-9"
                        data-testid="test-search-input"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {filteredTests.length > 0 ? (
                      filteredTests.map((test, idx) => (
                        <div key={idx} className="p-3 bg-zinc-800/50 rounded-lg border border-border">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">
                              {test.name || test.id || `Test ${idx + 1}`}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                (test.status || test.result || (test.passed ? "passed" : "failed")) === "passed"
                                  ? "border-green-500/30 text-green-400"
                                  : "border-red-500/30 text-red-400"
                              }`}
                            >
                              {test.status || test.result || (test.passed ? "passed" : "failed")}
                            </Badge>
                          </div>
                          {test.message && (
                            <p className="text-xs text-muted-foreground mt-2">{applyRedaction(test.message)}</p>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 text-center text-muted-foreground py-6">
                        No test results match the current filters.
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Log Explorer */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-blue-400" />
                    Log Explorer
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-3 mb-4">
                    <div className="relative flex-1 min-w-[220px]">
                      <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                      <Input
                        value={logQuery}
                        onChange={(event) => setLogQuery(event.target.value)}
                        placeholder="Search logs"
                        className="pl-9"
                        data-testid="log-search-input"
                      />
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {filteredLogs.length} entries
                    </Badge>
                  </div>
                  <div className="bg-black/30 rounded-lg p-4 max-h-72 overflow-auto">
                    <pre className="font-mono text-xs whitespace-pre-wrap">
                      {filteredLogs.length > 0
                        ? filteredLogs.map((entry) => applyRedaction(formatLogEntry(entry))).join("\n\n")
                        : "No logs match the search query."}
                    </pre>
                  </div>
                </CardContent>
              </Card>

              {/* Comparison Tools */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GitCompare className="h-5 w-5 text-orange-400" />
                    Comparison Tools (Side-by-Side)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-3 mb-4">
                    <Select value={comparePackId} onValueChange={setComparePackId}>
                      <SelectTrigger className="w-72" data-testid="compare-pack-select">
                        <SelectValue placeholder="Select pack to compare" />
                      </SelectTrigger>
                      <SelectContent>
                        {evidencePacks
                          .filter((pack) => pack.id !== selectedPack.id)
                          .map((pack) => (
                            <SelectItem key={pack.id} value={pack.id}>
                              {pack.id.slice(0, 8)}... {new Date(pack.created_at).toLocaleDateString()}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {comparePack ? (
                    <div className="grid grid-cols-2 gap-4">
                      {[selectedPack, comparePack].map((pack, idx) => (
                        <div key={pack.id} className="p-4 border border-border rounded-lg bg-zinc-900/40">
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-mono text-xs">{pack.id.slice(0, 8)}...</span>
                            <Badge variant="outline" className="text-xs">
                              {idx === 0 ? "Primary" : "Comparison"}
                            </Badge>
                          </div>
                          <div className="space-y-2 text-sm">
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Confidence</span>
                              <span className="font-mono">{Math.round(pack.confidence * 100)}%</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Triggered Rules</span>
                              <span className="font-mono">{pack.triggered_rules?.length || 0}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Created</span>
                              <span className="font-mono text-xs">{new Date(pack.created_at).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">Select another pack to compare metrics and metadata.</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <FileSearch className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select an evidence pack to view details</p>
            </div>
          </div>
        )}
      </div>

      {/* Artifact Detail Drawer */}
      {artifactDrawerOpen && (
        <div className="fixed inset-0 z-50" data-testid="artifact-drawer">
          <div
            className="absolute inset-0 bg-black/70"
            onClick={closeArtifactDrawer}
            data-testid="artifact-drawer-overlay"
          />
          <div className="absolute right-0 top-0 h-full w-full max-w-xl border-l border-border bg-zinc-950 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold">Artifact Detail</h2>
                <p className="text-xs text-muted-foreground font-mono">
                  {selectedArtifact?.event_type || "artifact"}
                </p>
              </div>
              <Button variant="ghost" onClick={closeArtifactDrawer} data-testid="artifact-drawer-close">
                Close
              </Button>
            </div>
            <ScrollArea className="h-[calc(100%-64px)]">
              <div className="p-6 space-y-4">
                <div className="rounded border border-border bg-black/30 p-3 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-muted-foreground">Team</p>
                      <p className="font-mono">{selectedArtifact?.team || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Agent</p>
                      <p className="font-mono">{selectedArtifact?.agent || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Timestamp</p>
                      <p className="font-mono">
                        {selectedArtifact?.created_at
                          ? new Date(selectedArtifact.created_at).toLocaleString()
                          : "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Event</p>
                      <p className="font-mono">{selectedArtifact?.event_type || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Stage</p>
                      <p className="font-mono">{selectedArtifact?.stage || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Run</p>
                      <p className="font-mono">{selectedPack?.run_id || "N/A"}</p>
                    </div>
                  </div>
                </div>
                <div className="rounded border border-border bg-black/30 p-3 text-xs space-y-2">
                  <p className="text-sm font-medium">Lineage Links</p>
                    <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-muted-foreground">Evidence Pack</p>
                      <button
                        type="button"
                        className="font-mono text-left text-cyan-200 hover:text-cyan-100"
                        onClick={() => clearPackFilter()}
                        data-testid="lineage-pack-link"
                      >
                        {selectedPack?.id || "N/A"}
                      </button>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Battle</p>
                      <button
                        type="button"
                        className="font-mono text-left text-cyan-200 hover:text-cyan-100"
                        onClick={() => applyPackFilter("battle", selectedPack?.battle_id)}
                        data-testid="lineage-battle-link"
                      >
                        {selectedPack?.battle_id || "N/A"}
                      </button>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Parent Pack</p>
                      <button
                        type="button"
                        className="font-mono text-left text-cyan-200 hover:text-cyan-100"
                        onClick={() => applyPackFilter("parent", selectedPack?.lineage?.parent_pack_id)}
                        data-testid="lineage-parent-pack-link"
                      >
                        {selectedPack?.lineage?.parent_pack_id || "N/A"}
                      </button>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Derived From</p>
                      <button
                        type="button"
                        className="font-mono text-left text-cyan-200 hover:text-cyan-100"
                        onClick={() => applyPackFilter("derived", selectedPack?.lineage?.derived_from)}
                        data-testid="lineage-derived-link"
                      >
                        {selectedPack?.lineage?.derived_from || "N/A"}
                      </button>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Run</p>
                      <button
                        type="button"
                        className="font-mono text-left text-cyan-200 hover:text-cyan-100"
                        onClick={() => applyPackFilter("run", selectedPack?.run_id)}
                        data-testid="lineage-run-link"
                      >
                        {selectedPack?.run_id || "N/A"}
                      </button>
                    </div>
                  </div>
                </div>
                <div className="rounded border border-border bg-black/30 p-3 text-xs space-y-2">
                  <p className="text-sm font-medium">Related Approvals</p>
                  {artifactApprovals.length > 0 ? (
                    <div className="space-y-2">
                      {artifactApprovals.map((approval, idx) => (
                        <div key={`artifact-approval-${idx}`} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-[10px]">
                              {approval.status || approval.action || "approved"}
                            </Badge>
                            <span className="font-mono">
                              {approval.approver_id || approval.approver || "Unknown"}
                            </span>
                          </div>
                          <span className="text-muted-foreground">
                            {approval.timestamp ? new Date(approval.timestamp).toLocaleString() : "Pending"}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-muted-foreground">No approvals recorded for this stage.</div>
                  )}
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium">Artifact Output</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(
                          JSON.stringify(selectedArtifact?.outputs || selectedArtifact, null, 2)
                        );
                        toast.success("Artifact JSON copied");
                      }}
                      data-testid="artifact-drawer-copy"
                    >
                      Copy JSON
                    </Button>
                  </div>
                  <pre className="text-xs bg-black/40 border border-border rounded p-3 overflow-auto whitespace-pre-wrap">
                    {JSON.stringify(selectedArtifact?.outputs || selectedArtifact, null, 2)}
                  </pre>
                </div>
              </div>
            </ScrollArea>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvidenceViewer;
