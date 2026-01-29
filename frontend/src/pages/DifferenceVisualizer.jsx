import React, { useState } from "react";
import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
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

// Sample diff data for demonstration
const sampleDiffs = [
  {
    id: "1",
    name: "VEL-001 Rule Update",
    type: "rule",
    oldCode: `{
  "name": "VEL-001",
  "description": "Velocity check for rapid transactions",
  "conditions": [
    {
      "field": "tx_count",
      "operator": ">",
      "value": 10
    }
  ],
  "actions": [
    {
      "type": "flag",
      "severity": "medium"
    }
  ],
  "priority": 1
}`,
    newCode: `{
  "name": "VEL-001",
  "description": "Enhanced velocity check for rapid transactions",
  "conditions": [
    {
      "field": "tx_count",
      "operator": ">",
      "value": 5
    },
    {
      "field": "time_window",
      "operator": "<",
      "value": 60
    }
  ],
  "actions": [
    {
      "type": "flag",
      "severity": "high"
    },
    {
      "type": "alert",
      "channel": "ops"
    }
  ],
  "priority": 1
}`,
    status: "pending",
    comments: [],
  },
  {
    id: "2",
    name: "Pattern ATO-99 Enhancement",
    type: "pattern",
    oldCode: `class ATODetector:
    def __init__(self):
        self.threshold = 3
    
    def detect(self, events):
        failed_logins = 0
        for event in events:
            if event.type == "login_failed":
                failed_logins += 1
        return failed_logins > self.threshold`,
    newCode: `class ATODetector:
    def __init__(self):
        self.threshold = 3
        self.time_window = 300  # 5 minutes
        self.ip_threshold = 2
    
    def detect(self, events):
        failed_logins = 0
        unique_ips = set()
        for event in events:
            if event.type == "login_failed":
                failed_logins += 1
                unique_ips.add(event.ip)
        
        # Multi-factor detection
        velocity_breach = failed_logins > self.threshold
        ip_anomaly = len(unique_ips) > self.ip_threshold
        
        return velocity_breach or ip_anomaly`,
    status: "pending",
    comments: [],
  },
];

const DifferenceVisualizer = () => {
  const [diffs, setDiffs] = useState(sampleDiffs);
  const [selectedDiff, setSelectedDiff] = useState(sampleDiffs[0]);
  const [commitMessage, setCommitMessage] = useState("");
  const [sandboxResult, setSandboxResult] = useState(null);
  const [running, setRunning] = useState(false);
  const mergedPreview = selectedDiff?.newCode || "";

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

  const handleAccept = () => {
    const updated = diffs.map(d => 
      d.id === selectedDiff.id ? { ...d, status: "accepted" } : d
    );
    setDiffs(updated);
    setSelectedDiff({ ...selectedDiff, status: "accepted" });
    toast.success("Changes accepted!");
  };

  const handleReject = () => {
    const updated = diffs.map(d => 
      d.id === selectedDiff.id ? { ...d, status: "rejected" } : d
    );
    setDiffs(updated);
    setSelectedDiff({ ...selectedDiff, status: "rejected" });
    toast.error("Changes rejected");
  };

  const handleRequestChanges = () => {
    toast("Changes requested. Assigning back to author.");
  };

  const runSandboxValidation = () => {
    setRunning(true);
    setSandboxResult(null);
    
    // Simulate sandbox validation
    setTimeout(() => {
      const passed = Math.random() > 0.3;
      setSandboxResult({
        passed,
        tests: {
          syntax: true,
          logic: passed,
          performance: passed,
          security: true,
        },
        message: passed 
          ? "All validation checks passed. Safe to merge." 
          : "Logic validation failed. Review required.",
        timestamp: new Date().toISOString(),
      });
      setRunning(false);
    }, 2000);
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
    const diffText = `--- OLD ---\n${selectedDiff.oldCode}\n\n--- NEW ---\n${selectedDiff.newCode}`;
    navigator.clipboard.writeText(diffText);
    toast.success("Diff copied to clipboard!");
  };

  return (
    <div className="h-full flex" data-testid="difference-visualizer">
      {/* Diff List */}
      <div className="w-72 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold">Pending Changes</h2>
          <p className="text-sm text-muted-foreground">{diffs.filter(d => d.status === "pending").length} awaiting review</p>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {diffs.map((diff) => (
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
                  <FileCode className={`h-4 w-4 ${diff.type === 'rule' ? 'text-blue-400' : 'text-purple-400'}`} />
                  <span className="font-medium text-sm">{diff.name}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <Badge variant="outline" className="text-xs capitalize">{diff.type}</Badge>
                  {diff.status === "accepted" && <CheckCircle2 className="h-4 w-4 text-green-400" />}
                  {diff.status === "rejected" && <X className="h-4 w-4 text-red-400" />}
                  {diff.status === "pending" && <AlertTriangle className="h-4 w-4 text-yellow-400" />}
                </div>
              </div>
            ))}
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
                <div className="flex gap-4">
                  {Object.entries(sandboxResult.tests).map(([test, passed]) => (
                    <div key={test} className="flex items-center gap-1">
                      {passed 
                        ? <Check className="h-3 w-3 text-green-400" />
                        : <X className="h-3 w-3 text-red-400" />
                      }
                      <span className="text-xs capitalize">{test}</span>
                    </div>
                  ))}
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
                  <pre className="p-3 bg-black/30 rounded-lg font-mono text-xs overflow-auto max-h-64">
                    {selectedDiff.oldCode}
                  </pre>
                </CardContent>
              </Card>
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">APMC (Patched)</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="p-3 bg-black/30 rounded-lg font-mono text-xs overflow-auto max-h-64">
                    {selectedDiff.newCode}
                  </pre>
                </CardContent>
              </Card>
              <Card className="border-border border-green-500/30 bg-green-500/5">
                <CardHeader>
                  <CardTitle className="text-sm text-green-300">Merged Model</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="p-3 bg-black/30 rounded-lg font-mono text-xs overflow-auto max-h-64">
                    {mergedPreview}
                  </pre>
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

            {/* Linked Artifacts */}
            <div className="mx-4 mt-4">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="text-sm">Linked Artifacts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs">RuleSpec</Badge>
                    <Badge variant="outline" className="text-xs">Tests</Badge>
                    <Badge variant="outline" className="text-xs">Evidence Pack</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Artifacts are attached to this diff for audit and review.</p>
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
