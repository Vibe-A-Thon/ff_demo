import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Checkbox } from "../components/ui/checkbox";
import { Label } from "../components/ui/label";
import { evidenceAPI, battleAPI } from "../lib/api";
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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [evidenceRes, battlesRes] = await Promise.all([
        evidenceAPI.getAll(),
        battleAPI.getAll(),
      ]);
      setEvidencePacks(evidenceRes.data);
      setBattles(battlesRes.data);
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

  const normalizeApprovals = (pack) => {
    const raw = pack?.approval_chain || pack?.approvals || [];
    if (Array.isArray(raw)) return raw;
    return [raw];
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

  const logEntries = normalizeLogs(selectedPack);
  const filteredLogs = logEntries.filter((entry) => {
    if (!logQuery) return true;
    return formatLogEntry(entry).toLowerCase().includes(logQuery.toLowerCase());
  });

  const approvalChain = normalizeApprovals(selectedPack);

  return (
    <div className="h-full flex" data-testid="evidence-viewer">
      {/* Pack List */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold mb-4">Evidence Packs</h2>
          
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
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {evidencePacks.map((pack) => (
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
            {evidencePacks.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <FileSearch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No evidence packs yet</p>
                <p className="text-sm">Generate from a battle</p>
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
                      <p className="font-mono text-sm mt-1">{selectedPack.battle_id}</p>
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
    </div>
  );
};

export default EvidenceViewer;
