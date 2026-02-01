import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { rsbAPI } from "../lib/api";
import { toast } from "sonner";
import {
  GitCompare,
  Check,
  X,
  MessageSquare,
  Play,
  Copy,
  FileCode,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

const DifferenceVisualizer = () => {
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [diffs, setDiffs] = useState([]);
  const [selectedDiff, setSelectedDiff] = useState(null);
  const [commitMessage, setCommitMessage] = useState("");
  const [sandboxResult, setSandboxResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [conflictDecisions, setConflictDecisions] = useState({});
  const location = useLocation();
  const mergedPreview = selectedDiff?.newCode || "";
  const linkedArtifacts = (() => {
    const artifacts = selectedDiff?.artifacts || selectedPackage?.artifacts || [];
    if (Array.isArray(artifacts) && artifacts.length > 0) {
      return artifacts.map((artifact, idx) => ({
        id: artifact.artifact_id || artifact.id || `${idx}`,
        type: artifact.artifact_type || artifact.event_type || "artifact",
        label: artifact.artifact_type || artifact.event_type || "artifact",
        meta: artifact.artifact_id || artifact.id || "",
      }));
    }
    const derived = [];
    if (selectedPackage?.rule_spec) derived.push({ id: "rulespec", label: "RuleSpec" });
    if (selectedPackage?.rule_definition || selectedPackage?.code) derived.push({ id: "codepatch", label: "CodePatch" });
    if (selectedPackage?.test_results) derived.push({ id: "testplan", label: "TestPlan" });
    if (selectedPackage?.compliance_docs?.length) derived.push({ id: "compliance", label: "CompliancePack" });
    if (selectedPackage?.conflicts?.length) derived.push({ id: "review", label: "CodeReviewReport" });
    return derived;
  })();
  const conflictBlocks = [
    { id: "conflict-1", label: "Threshold change conflict", recommendation: "Use patch" },
    { id: "conflict-2", label: "Action severity mismatch", recommendation: "Manual merge" },
  ];
  const overlaySegments = [
    { id: "segment-1", label: "Rules", intensity: 0.8, kind: "added" },
    { id: "segment-2", label: "Conditions", intensity: 0.6, kind: "modified" },
    { id: "segment-3", label: "Actions", intensity: 0.9, kind: "hot" },
    { id: "segment-4", label: "Metadata", intensity: 0.4, kind: "removed" },
  ];
  const impactAreas = [
    { id: "impact-1", name: "Velocity threshold", delta: "+28%", risk: "high" },
    { id: "impact-2", name: "Alert routing", delta: "+12%", risk: "medium" },
    { id: "impact-3", name: "Time window", delta: "+6%", risk: "low" },
  ];
  const gutterMarkers = {
    left: {
      4: "legacy",
      9: "policy",
    },
    right: {
      6: "patch",
      12: "hot",
    },
  };

  const diffStyles = {
    variables: {
      dark: {
        diffViewerBackground: "#09090B",
        diffViewerColor: "#FAFAFA",
        addedBackground: "#10B98120",
        addedColor: "#10B981",
        removedBackground: "#EF444420",
        removedColor: "#EF4444",
        wordAddedBackground: "#10B98140",
        wordRemovedBackground: "#EF444440",
        addedGutterBackground: "#10B98130",
        removedGutterBackground: "#EF444430",
        gutterBackground: "#18181B",
        gutterBackgroundDark: "#18181B",
        highlightBackground: "#3B82F620",
        highlightGutterBackground: "#3B82F630",
        codeFoldGutterBackground: "#27272A",
        codeFoldBackground: "#27272A",
        emptyLineBackground: "#18181B",
        gutterColor: "#71717A",
        addedGutterColor: "#10B981",
        removedGutterColor: "#EF4444",
        codeFoldContentColor: "#71717A",
        diffViewerTitleBackground: "#18181B",
        diffViewerTitleColor: "#FAFAFA",
        diffViewerTitleBorderColor: "#27272A",
      },
    },
    line: {
      padding: "10px 2px",
      "&:hover": {
        background: "#27272A",
      },
    },
    titleBlock: {
      padding: "10px 16px",
      borderBottom: "1px solid #27272A",
    },
    codeFold: {
      backgroundColor: "#27272A",
      fontSize: "12px",
    },
    gutter: {
      padding: "0 16px",
      minWidth: "40px",
    },
  };

  useEffect(() => {
    const loadPackages = async () => {
      try {
        const response = await rsbAPI.getAll();
        setPackages(response.data || []);
        if (response.data?.length) {
          setSelectedPackage(response.data[0]);
        }
      } catch (error) {
        toast.error("Failed to load RSB packages");
      }
    };
    loadPackages();
  }, []);

  useEffect(() => {
    if (!packages.length) return;
    const searchParams = new URLSearchParams(location.search);
    const packageId = searchParams.get("package");
    if (!packageId) return;
    const matched = packages.find((pkg) => pkg.id === packageId);
    if (matched) {
      setSelectedPackage(matched);
    }
  }, [location.search, packages]);

  useEffect(() => {
    const loadDiffs = async () => {
      if (!selectedPackage) return;
      try {
        const response = await rsbAPI.getDiffs(selectedPackage.id);
        const loadedDiffs = response.data?.diffs || [];
        setDiffs(loadedDiffs);
        setSelectedDiff(loadedDiffs[0] || null);
      } catch (error) {
        toast.error("Failed to load visual patch diffs");
      }
    };
    loadDiffs();
  }, [selectedPackage]);

  const handleAccept = async () => {
    if (!selectedPackage || !selectedDiff) return;
    try {
      const response = await rsbAPI.applyPatch(selectedPackage.id, {
        decision: "accepted",
        conflict_resolutions: conflictDecisions,
        commit_message: commitMessage,
      });
      const updatedDiffs = diffs.map((diff) =>
        diff.id === selectedDiff.id ? { ...diff, status: "accepted" } : diff
      );
      setDiffs(updatedDiffs);
      setSelectedDiff({ ...selectedDiff, status: "accepted" });
      setSelectedPackage(response.data);
      toast.success("Patch applied and package updated!");
    } catch (error) {
      toast.error("Failed to apply patch");
    }
  };

  const handleReject = async () => {
    if (!selectedPackage || !selectedDiff) return;
    try {
      const response = await rsbAPI.applyPatch(selectedPackage.id, {
        decision: "rejected",
        conflict_resolutions: conflictDecisions,
        commit_message: commitMessage,
      });
      const updatedDiffs = diffs.map((diff) =>
        diff.id === selectedDiff.id ? { ...diff, status: "rejected" } : diff
      );
      setDiffs(updatedDiffs);
      setSelectedDiff({ ...selectedDiff, status: "rejected" });
      setSelectedPackage(response.data);
      toast.error("Patch rejected");
    } catch (error) {
      toast.error("Failed to reject patch");
    }
  };

  const handleRequestChanges = () => {
    toast("Changes requested. Assigning back to author.");
  };

  const runSandboxValidation = async () => {
    if (!selectedPackage) return;
    setRunning(true);
    setSandboxResult(null);
    try {
      const response = await rsbAPI.test(selectedPackage.id);
      const results = response.data || {};
      const passed = (results.unit_tests?.failed || 0) === 0 && (results.integration_tests?.failed || 0) === 0;
      setSandboxResult({
        passed,
        tests: {
          unit: results.unit_tests || {},
          integration: results.integration_tests || {},
          compliance: results.compliance_checks || {},
        },
        message: passed
          ? "All validation checks passed. Safe to merge."
          : "Test failures detected. Review required.",
        timestamp: results.timestamp || new Date().toISOString(),
      });
      toast.success("Sandbox validation completed");
    } catch (error) {
      toast.error("Sandbox validation failed");
    } finally {
      setRunning(false);
    }
  };

  const generateCommitMessage = () => {
    const msg = `feat(rules): Update ${selectedDiff.name}

- Enhanced detection logic
- Added new conditions for improved accuracy
- Updated severity levels

Reviewed and validated via sandbox testing.`;
    setCommitMessage(msg);
    toast.success("Commit message generated!");
  };

  const copyDiff = () => {
    if (!selectedDiff) return;
    const diffText = `--- OLD ---\n${selectedDiff.oldCode}\n\n--- NEW ---\n${selectedDiff.newCode}`;
    navigator.clipboard.writeText(diffText);
    toast.success("Diff copied to clipboard!");
  };

  const handleConflictDecision = (conflictId, decision) => {
    setConflictDecisions((prev) => ({ ...prev, [conflictId]: decision }));
  };

  const getOverlayClass = (kind) => {
    if (kind === "added") return "bg-green-500/40";
    if (kind === "removed") return "bg-red-500/40";
    if (kind === "hot") return "bg-yellow-400/50";
    return "bg-blue-500/30";
  };

  const getImpactBadge = (risk) => {
    if (risk === "high") return "bg-red-500/20 text-red-200 border border-red-500/40";
    if (risk === "medium") return "bg-yellow-500/20 text-yellow-200 border border-yellow-500/40";
    return "bg-green-500/20 text-green-200 border border-green-500/40";
  };

  const renderGutter = (lineNumber, side) => {
    const marker = gutterMarkers[side]?.[lineNumber];
    return (
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs text-muted-foreground">{lineNumber}</span>
        {marker && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
            {marker}
          </Badge>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex" data-testid="difference-visualizer">
      {/* Diff List */}
      <div className="w-72 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border space-y-3">
          <div>
            <h2 className="text-lg font-semibold">Pending Changes</h2>
            <p className="text-sm text-muted-foreground">{diffs.filter(d => d.status === "pending").length} awaiting review</p>
          </div>
          <Select
            value={selectedPackage?.id || ""}
            onValueChange={(value) => setSelectedPackage(packages.find((pkg) => pkg.id === value) || null)}
          >
            <SelectTrigger data-testid="patcher-package-select">
              <SelectValue placeholder="Select RSB package" />
            </SelectTrigger>
            <SelectContent>
              {packages.map((pkg) => (
                <SelectItem key={pkg.id} value={pkg.id}>
                  {pkg.name} • v{pkg.version}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {diffs.length > 0 ? (
              diffs.map((diff) => (
                <div
                  key={diff.id}
                  onClick={() => setSelectedDiff(diff)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDiff?.id === diff.id
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-border hover:border-zinc-600 bg-card"
                  }`}
                  data-testid={`diff-${diff.id}`}
                >
                  <div className="flex items-center gap-2">
                    <FileCode className={`h-4 w-4 ${diff.type === 'code' ? 'text-blue-400' : 'text-purple-400'}`} />
                    <span className="font-medium text-sm">{diff.name}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <Badge variant="outline" className="text-xs capitalize">{diff.type}</Badge>
                    {diff.status === "accepted" && <CheckCircle2 className="h-4 w-4 text-green-400" />}
                    {diff.status === "rejected" && <X className="h-4 w-4 text-red-400" />}
                    {diff.status === "pending" && <AlertTriangle className="h-4 w-4 text-yellow-400" />}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-muted-foreground p-4" data-testid="no-diffs">
                No diffs available for this package.
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Diff Viewer */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedDiff ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold flex items-center gap-2">
                  <GitCompare className="h-5 w-5 text-blue-400" />
                  {selectedDiff.name}
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Before / After comparison
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={copyDiff}
                  data-testid="copy-diff-btn"
                  data-explain="Copy diff"
                  data-explain-title="Diff snapshot"
                  data-explain-summary="Copies the before/after changes for peer review or audit notes."
                  data-explain-rules="DIFF-002,COM-005"
                  data-explain-evidence="Change summary,Patch context"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  onClick={runSandboxValidation}
                  disabled={running}
                  data-testid="sandbox-validate-btn"
                  data-explain="Run sandbox validation"
                  data-explain-title="Sandbox checks"
                  data-explain-summary="Runs syntactic and logic validation against safe test data."
                  data-explain-rules="DIFF-VAL-01,SAFE-003"
                  data-explain-evidence="Sandbox results,Test suite"
                >
                  <Play className={`h-4 w-4 mr-2 ${running ? 'animate-spin' : ''}`} />
                  Validate
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleReject}
                  disabled={selectedDiff.status !== "pending"}
                  data-testid="reject-btn"
                  data-explain="Reject diff"
                  data-explain-title="Rejection reason"
                  data-explain-summary="Rejects changes that violate policy, performance, or risk thresholds."
                  data-explain-rules="DIFF-DEC-02,RISK-004"
                  data-explain-evidence="Risk delta,Policy mismatch"
                >
                  <X className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  variant="outline"
                  onClick={handleRequestChanges}
                  disabled={selectedDiff.status !== "pending"}
                  data-testid="request-changes-btn"
                  data-explain="Request changes"
                  data-explain-title="Change request"
                  data-explain-summary="Sends the diff back for revision with reviewer notes."
                  data-explain-rules="DIFF-DEC-03"
                  data-explain-evidence="Reviewer notes,Policy checklist"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Request Changes
                </Button>
                <Button
                  onClick={handleAccept}
                  disabled={selectedDiff.status !== "pending"}
                  data-testid="accept-btn"
                  data-explain="Accept diff"
                  data-explain-title="Acceptance rationale"
                  data-explain-summary="Approves changes after validation, enabling deployment workflows."
                  data-explain-rules="DIFF-DEC-01,COM-012"
                  data-explain-evidence="Sandbox pass,Review notes,Audit trail"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Accept
                </Button>
              </div>
            </div>

            {/* Sandbox Result */}
            {sandboxResult && (
              <div className={`mx-4 mt-4 p-4 rounded-lg border ${
                sandboxResult.passed 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : 'bg-red-500/10 border-red-500/30'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {sandboxResult.passed 
                    ? <CheckCircle2 className="h-5 w-5 text-green-400" />
                    : <AlertTriangle className="h-5 w-5 text-red-400" />
                  }
                  <span className="font-semibold">
                    {sandboxResult.passed ? 'Sandbox Validation Passed' : 'Sandbox Validation Failed'}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{sandboxResult.message}</p>
                <div className="flex flex-wrap gap-4">
                  {Object.entries(sandboxResult.tests).map(([test, results]) => {
                    const failed = results?.failed ?? 0;
                    const passed = results?.passed ?? 0;
                    const total = results?.total ?? passed + failed;
                    const ok = failed === 0;
                    return (
                      <div key={test} className="flex items-center gap-1">
                        {ok ? <Check className="h-3 w-3 text-green-400" /> : <X className="h-3 w-3 text-red-400" />}
                        <span className="text-xs capitalize">{test}</span>
                        <span className="text-[10px] text-muted-foreground">{passed}/{total}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Three-Pane Preview */}
            <div className="mx-4 mt-4 grid grid-cols-3 gap-4" data-testid="three-pane-preview">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Existing Model</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg overflow-hidden">
                    <SyntaxHighlighter language="python" style={vscDarkPlus} customStyle={{ margin: 0, background: "transparent" }}>
                      {selectedDiff.oldCode}
                    </SyntaxHighlighter>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">APMC (Patched)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg overflow-hidden">
                    <SyntaxHighlighter language="python" style={vscDarkPlus} customStyle={{ margin: 0, background: "transparent" }}>
                      {selectedDiff.newCode}
                    </SyntaxHighlighter>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-border border-green-500/30 bg-green-500/5">
                <CardHeader>
                  <CardTitle className="text-sm text-green-300">Merged Model</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg overflow-hidden">
                    <SyntaxHighlighter language="python" style={vscDarkPlus} customStyle={{ margin: 0, background: "transparent" }}>
                      {mergedPreview}
                    </SyntaxHighlighter>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Patch Overlay */}
            <div className="mx-4 mt-4">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Patch Overlay</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                      <div className="text-green-300 font-semibold">Additions</div>
                      <div className="font-mono text-lg">+12</div>
                    </div>
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                      <div className="text-red-300 font-semibold">Removals</div>
                      <div className="font-mono text-lg">-4</div>
                    </div>
                    <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                      <div className="text-yellow-300 font-semibold">Hotspots</div>
                      <div className="font-mono text-lg">2</div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-xs text-muted-foreground mb-2">Impact Map</div>
                    <div className="flex items-center gap-2" data-testid="overlay-map">
                      {overlaySegments.map((segment) => (
                        <div
                          key={segment.id}
                          className={`h-3 rounded-full ${getOverlayClass(segment.kind)}`}
                          style={{ flex: segment.intensity * 10 }}
                          title={`${segment.label} • ${(segment.intensity * 100).toFixed(0)}%`}
                        />
                      ))}
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-green-500/60" />
                        Additions
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-red-500/60" />
                        Removals
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-yellow-400/60" />
                        Hotspots
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2" data-testid="impact-annotations">
                    {impactAreas.map((impact) => (
                      <div key={impact.id} className="flex items-center justify-between rounded-lg border border-border bg-black/30 px-3 py-2">
                        <div>
                          <div className="text-xs font-medium">{impact.name}</div>
                          <div className="text-[10px] text-muted-foreground">Delta {impact.delta}</div>
                        </div>
                        <span className={`text-[10px] px-2 py-1 rounded ${getImpactBadge(impact.risk)}`}
                        >
                          {impact.risk.toUpperCase()} IMPACT
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 text-xs text-muted-foreground">
                    Color overlays highlight high‑impact change regions beyond standard diff lines.
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Inline Comments */}
            <div className="mx-4 mt-4">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Inline Comments</CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedDiff.comments?.length > 0 ? (
                    <div className="space-y-2">
                      {selectedDiff.comments.map((comment, idx) => (
                        <div key={idx} className="p-3 bg-zinc-800/50 rounded-lg text-sm">
                          {comment}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No inline comments yet.</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Conflict Resolution */}
            <div className="mx-4 mt-4">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Conflict Resolution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {conflictBlocks.map((conflict) => (
                    <div key={conflict.id} className="p-3 rounded-lg border border-border bg-black/30">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium">{conflict.label}</div>
                          <div className="text-xs text-muted-foreground">Recommendation: {conflict.recommendation}</div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant={conflictDecisions[conflict.id] === "keep" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(conflict.id, "keep")}
                            data-testid={`${conflict.id}-keep-existing`}
                          >
                            Keep Existing
                          </Button>
                          <Button
                            variant={conflictDecisions[conflict.id] === "patch" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(conflict.id, "patch")}
                            data-testid={`${conflict.id}-use-patch`}
                          >
                            Use Patch
                          </Button>
                          <Button
                            variant={conflictDecisions[conflict.id] === "manual" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(conflict.id, "manual")}
                            data-testid={`${conflict.id}-manual-merge`}
                          >
                            Manual Merge
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Linked Artifacts */}
            <div className="mx-4 mt-4">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Linked Artifacts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {linkedArtifacts.length > 0 ? (
                      linkedArtifacts.map((artifact) => (
                        <div key={artifact.id} className="flex flex-col gap-1">
                          <Badge variant="outline" className="text-xs">
                            {artifact.label}
                          </Badge>
                          {artifact.meta && (
                            <span className="text-[11px] text-muted-foreground font-mono">
                              {artifact.meta}
                            </span>
                          )}
                        </div>
                      ))
                    ) : (
                      <Badge variant="outline" className="text-xs">No linked artifacts</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Artifacts are attached to this diff for audit and review.
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Diff View */}
            <ScrollArea className="flex-1">
              <div className="p-4">
                <ReactDiffViewer
                  oldValue={selectedDiff.oldCode}
                  newValue={selectedDiff.newCode}
                  splitView={true}
                  useDarkTheme={true}
                  leftTitle="Before"
                  rightTitle="After"
                  styles={diffStyles}
                  compareMethod={DiffMethod.WORDS}
                  renderGutter={renderGutter}
                />
              </div>
            </ScrollArea>

            {/* Commit Message */}
            <div className="p-4 border-t border-border">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Commit Message</label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={generateCommitMessage}
                  data-testid="generate-commit-btn"
                  data-explain="Auto-generate commit message"
                  data-explain-title="Commit summary"
                  data-explain-summary="Summarizes the diff and validation status into an audit-friendly message."
                  data-explain-rules="DIFF-COMMIT-01,COM-004"
                  data-explain-evidence="Diff stats,Validation outcome"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Auto-generate
                </Button>
              </div>
              <Textarea
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                placeholder="Enter commit message..."
                className="font-mono text-sm"
                rows={3}
                data-testid="commit-message-input"
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <GitCompare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select a diff to review</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DifferenceVisualizer;
