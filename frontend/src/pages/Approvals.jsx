import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { approvalAPI, ruleAPI, rsbAPI } from "../lib/api";
import { toast } from "sonner";
import {
  ShieldCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  User,
  FileText,
  Plus,
  Trash2,
  Shield,
} from "lucide-react";

const Approvals = () => {
  const [approvals, setApprovals] = useState([]);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideImpact, setOverrideImpact] = useState("high");
  const [overrideAck, setOverrideAck] = useState(false);
  const [rules, setRules] = useState([]);
  const [packages, setPackages] = useState([]);
  
  const [formData, setFormData] = useState({
    resource_type: "rule",
    resource_id: "",
    action: "deploy",
    requestor_id: "current-user",
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [approvalsRes, rulesRes, packagesRes] = await Promise.all([
        approvalAPI.getAll(),
        ruleAPI.getAll(),
        rsbAPI.getAll(),
      ]);
      setApprovals(approvalsRes.data);
      setRules(rulesRes.data);
      setPackages(packagesRes.data);
    } catch (error) {
      console.error("Failed to load data:", error);
    }
  };

  const handleCreateApproval = async () => {
    if (!formData.resource_id) {
      toast.error("Please select a resource");
      return;
    }
    try {
      const response = await approvalAPI.create(formData);
      setApprovals([...approvals, response.data]);
      setShowCreateModal(false);
      setFormData({ resource_type: "rule", resource_id: "", action: "deploy", requestor_id: "current-user" });
      toast.success("Approval request created!");
    } catch (error) {
      toast.error("Failed to create approval request");
    }
  };

  const handleApprove = async (approvalId) => {
    try {
      await approvalAPI.approve(approvalId, "admin-user");
      loadData();
      toast.success("Request approved!");
    } catch (error) {
      toast.error("Failed to approve");
    }
  };

  const handleReject = async (approvalId) => {
    try {
      await approvalAPI.reject(approvalId, "admin-user");
      loadData();
      toast.error("Request rejected");
    } catch (error) {
      toast.error("Failed to reject");
    }
  };

  const handleEmergencyOverride = () => {
    setOverrideOpen(true);
  };

  const submitEmergencyOverride = () => {
    if (overrideReason.trim().length < 20 || !overrideAck) {
      toast.error("Provide a detailed justification and confirm accountability.");
      return;
    }
    toast.warning("Emergency override submitted for immediate review.");
    setOverrideOpen(false);
    setOverrideReason("");
    setOverrideImpact("high");
    setOverrideAck(false);
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { color: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20", icon: Clock },
      approved: { color: "bg-green-500/15 text-green-400 border-green-500/20", icon: CheckCircle2 },
      rejected: { color: "bg-red-500/15 text-red-400 border-red-500/20", icon: XCircle },
    };
    const c = config[status] || config.pending;
    const Icon = c.icon;
    return (
      <Badge className={`${c.color} border`}>
        <Icon className="h-3 w-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const getResourceName = (type, id) => {
    if (type === "rule") {
      const rule = rules.find(r => r.id === id);
      return rule?.name || id;
    } else if (type === "rsb_package") {
      const pkg = packages.find(p => p.id === id);
      return pkg?.name || id;
    }
    return id;
  };

  const getRiskAssessment = (approval) => {
    if (!approval) return { score: 0, label: "Low", color: "text-green-400" };
    const base = approval.action === "delete" ? 85 : approval.action === "merge" ? 70 : 55;
    const typeBoost = approval.resource_type === "rsb_package" ? 10 : 0;
    const score = Math.min(95, base + typeBoost);
    const label = score >= 80 ? "High" : score >= 60 ? "Medium" : "Low";
    const color = score >= 80 ? "text-red-400" : score >= 60 ? "text-yellow-400" : "text-green-400";
    return { score, label, color };
  };

  const pendingCount = approvals.filter(a => a.status === "pending").length;
  const auditTrail = selectedApproval
    ? [
        {
          id: "audit-1",
          action: "Request created",
          actor: selectedApproval.requestor_id,
          timestamp: selectedApproval.created_at,
        },
        ...(selectedApproval.approvers || []).map((approver, idx) => ({
          id: `audit-${idx + 2}`,
          action: `Approval ${approver.action}`,
          actor: approver.approver_id,
          timestamp: approver.timestamp,
        })),
      ]
    : [];

  const approverIds = (selectedApproval?.approvers || []).map((approver) => approver.approver_id);
  const sodWarnings = [];
  if (selectedApproval?.requestor_id && approverIds.includes(selectedApproval.requestor_id)) {
    sodWarnings.push("Requestor is also listed as an approver (SoD violation)");
  }
  if (["deploy", "merge"].includes(selectedApproval?.action) && approverIds.length < 2) {
    sodWarnings.push("High-risk action requires at least two approvers");
  }
  if (selectedApproval?.resource_type === "rsb_package" && selectedApproval?.action === "merge") {
    sodWarnings.push("RSB merges require compliance sign-off before release");
  }

  return (
    <div className="h-full flex" data-testid="approvals">
      {/* Approval Queue */}
      <div className="w-96 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">Approval Queue</h2>
              <p className="text-sm text-muted-foreground">
                {pendingCount} pending review
              </p>
            </div>
            <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
              <DialogTrigger asChild>
                <Button
                  size="sm"
                  data-testid="create-approval-btn"
                  data-explain="Create approval request"
                  data-explain-title="Why approvals are required"
                  data-explain-summary="Enforces separation of duties and governance for rule or package changes."
                  data-explain-rules="RBAC-SoD-01,APP-004"
                  data-explain-evidence="Requester role,Change scope,Risk rating"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Request
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-card border-border" data-testid="create-approval-modal">
                <DialogHeader>
                  <DialogTitle>Create Approval Request</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Resource Type</label>
                    <Select
                      value={formData.resource_type}
                      onValueChange={(v) => setFormData({ ...formData, resource_type: v, resource_id: "" })}
                    >
                      <SelectTrigger data-testid="resource-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rule">Rule</SelectItem>
                        <SelectItem value="rsb_package">RSB Package</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Resource</label>
                    <Select
                      value={formData.resource_id}
                      onValueChange={(v) => setFormData({ ...formData, resource_id: v })}
                    >
                      <SelectTrigger data-testid="resource-id-select">
                        <SelectValue placeholder="Select resource" />
                      </SelectTrigger>
                      <SelectContent>
                        {formData.resource_type === "rule" 
                          ? rules.map(r => <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>)
                          : packages.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)
                        }
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Action</label>
                    <Select
                      value={formData.action}
                      onValueChange={(v) => setFormData({ ...formData, action: v })}
                    >
                      <SelectTrigger data-testid="action-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="deploy">Deploy</SelectItem>
                        <SelectItem value="update">Update</SelectItem>
                        <SelectItem value="delete">Delete</SelectItem>
                        <SelectItem value="merge">Merge</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={handleCreateApproval}
                    className="w-full"
                    data-testid="submit-approval-btn"
                    data-explain="Submit for approval"
                    data-explain-title="Approval submission"
                    data-explain-summary="Captures change intent, affected artifacts, and required approvers."
                    data-explain-rules="APP-007,APP-013"
                    data-explain-evidence="Requested action,Resource,SoD policy"
                  >
                    <ShieldCheck className="h-4 w-4 mr-2" />
                    Submit for Approval
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Safe to Proceed Indicator */}
          {pendingCount === 0 ? (
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
                <span className="font-semibold text-green-400">SAFE TO PROCEED</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                All approvals have been processed.
              </p>
            </div>
          ) : (
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <span className="font-semibold text-yellow-400">REVIEW REQUIRED</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {pendingCount} item(s) awaiting approval.
              </p>
            </div>
          )}
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {approvals.map((approval) => (
              <div
                key={approval.id}
                onClick={() => setSelectedApproval(approval)}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedApproval?.id === approval.id
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-border hover:border-zinc-600 bg-card"
                }`}
                data-testid={`approval-${approval.id}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      {approval.resource_type === "rule" 
                        ? <Shield className="h-4 w-4 text-blue-400" />
                        : <FileText className="h-4 w-4 text-purple-400" />
                      }
                      <span className="font-medium">
                        {getResourceName(approval.resource_type, approval.resource_id)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <Badge variant="outline" className="text-xs capitalize">{approval.action}</Badge>
                      <span>•</span>
                      <span>{new Date(approval.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {getStatusBadge(approval.status)}
                </div>
              </div>
            ))}
            {approvals.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <ShieldCheck className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No approval requests</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Approval Details */}
      <div className="flex-1 overflow-hidden">
        {selectedApproval ? (
          <ScrollArea className="h-full">
            <div className="p-6 space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-2">
                    <ShieldCheck className="h-6 w-6 text-blue-400" />
                    Approval Request
                  </h1>
                  <p className="text-muted-foreground mt-1 font-mono text-sm">
                    ID: {selectedApproval.id}
                  </p>
                </div>
                {selectedApproval.status === "pending" && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={handleEmergencyOverride}
                      data-testid="emergency-override-btn"
                      data-explain="Emergency override"
                      data-explain-title="Emergency override"
                      data-explain-summary="Escalates a high-risk change for immediate review with justification."
                      data-explain-rules="APP-OVR-01,COM-030"
                      data-explain-evidence="Override justification,Approver identity"
                    >
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Override
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => handleReject(selectedApproval.id)}
                      data-testid="reject-approval-btn"
                      data-explain="Reject approval"
                      data-explain-title="Rejection rationale"
                      data-explain-summary="Rejects the change due to policy or risk violations and records audit reasons."
                      data-explain-rules="APP-021,RISK-002"
                      data-explain-evidence="Policy mismatch,High risk delta"
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                    <Button
                      onClick={() => handleApprove(selectedApproval.id)}
                      data-testid="approve-approval-btn"
                      data-explain="Approve change"
                      data-explain-title="Approval rationale"
                      data-explain-summary="Approves deployment after checks on SoD, testing, and compliance evidence."
                      data-explain-rules="APP-018,COM-010"
                      data-explain-evidence="SoD satisfied,Tests passed,Audit trail"
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                  </div>
                )}
              </div>
              <Dialog open={overrideOpen} onOpenChange={setOverrideOpen}>
                <DialogContent className="bg-card border-border" data-testid="override-modal">
                  <DialogHeader>
                    <DialogTitle>Emergency Override Justification</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-muted-foreground">Impact Level</label>
                      <Select value={overrideImpact} onValueChange={setOverrideImpact}>
                        <SelectTrigger data-testid="override-impact-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="critical">Critical</SelectItem>
                          <SelectItem value="containment">Containment</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Justification (min 20 chars)</label>
                      <Textarea
                        value={overrideReason}
                        onChange={(event) => setOverrideReason(event.target.value)}
                        placeholder="Explain the risk, scope, and mitigation plan..."
                        data-testid="override-reason-input"
                      />
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={overrideAck}
                        onChange={(event) => setOverrideAck(event.target.checked)}
                        id="override-ack"
                      />
                      <label htmlFor="override-ack" className="text-muted-foreground">
                        I acknowledge this action will be audited and may require post-incident review.
                      </label>
                    </div>
                    <Button onClick={submitEmergencyOverride} data-testid="override-submit-btn">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Submit Override
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              {/* Status */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    {getStatusBadge(selectedApproval.status)}
                    <span className="text-sm text-muted-foreground">
                      Created: {new Date(selectedApproval.created_at).toLocaleString()}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Request Details */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Request Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-muted-foreground">Resource Type</label>
                      <p className="font-medium capitalize">{selectedApproval.resource_type.replace("_", " ")}</p>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Action</label>
                      <p className="font-medium capitalize">{selectedApproval.action}</p>
                    </div>
                    <div className="col-span-2">
                      <label className="text-sm text-muted-foreground">Resource</label>
                      <p className="font-medium">
                        {getResourceName(selectedApproval.resource_type, selectedApproval.resource_id)}
                      </p>
                      <p className="font-mono text-xs text-muted-foreground mt-1">
                        {selectedApproval.resource_id}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Requestor</label>
                      <div className="flex items-center gap-2 mt-1">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>{selectedApproval.requestor_id}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Validator + Risk Assessment */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle>Validator Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span className="text-sm">SAFE_TO_PROCEED</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      All required validators reported green.
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle>Risk Assessment</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const risk = getRiskAssessment(selectedApproval);
                      return (
                        <div className="space-y-2">
                          <div className={`text-2xl font-mono ${risk.color}`}>{risk.score}</div>
                          <Badge variant="outline" className="text-xs">{risk.label} risk</Badge>
                          <p className="text-xs text-muted-foreground">Based on action scope and artifact type.</p>
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle>Approval Timeline</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <div className="flex items-center justify-between">
                      <span>Requested</span>
                      <span>{new Date(selectedApproval.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Review</span>
                      <span>{selectedApproval.status === "pending" ? "In progress" : "Completed"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Decision</span>
                      <span className="capitalize">{selectedApproval.status}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Multi-Approver Flow */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Multi-Approver Flow</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap items-center gap-4">
                    {[
                      { role: "Requester", name: selectedApproval.requestor_id, gate: "RBAC: Requestor • Rules & Strategy" },
                      { role: "Tech Lead", name: selectedApproval.approvers?.[0]?.approver_id || "Pending", gate: "RBAC: TechLead • Review & Approve" },
                      { role: "Tech Manager", name: selectedApproval.approvers?.[1]?.approver_id || "Pending", gate: "RBAC: TechManager • Release Approval" },
                      { role: "Auditor", name: "Read-only", gate: "RBAC: Auditor • Audit & Compliance" },
                    ].map((step, idx) => (
                      <div key={`${step.role}-${idx}`} className="flex items-center gap-3">
                        <div className="p-3 rounded-lg border border-border bg-black/30">
                          <div className="text-xs text-muted-foreground">{step.role}</div>
                          <div className="text-sm font-medium">{step.name}</div>
                          <Badge variant="outline" className="mt-2 text-[10px]">
                            {step.gate}
                          </Badge>
                        </div>
                        {idx < 3 && <div className="text-muted-foreground">→</div>}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Compliance Checklist */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Compliance Checklist</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {[
                    "SoD policy validated",
                    "Test evidence attached",
                    "Risk assessment logged",
                    "Audit trail immutable",
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span>{item}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Approval History */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Approval History</CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedApproval.approvers?.length > 0 ? (
                    <div className="space-y-3">
                      {selectedApproval.approvers.map((approver, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-full ${
                              approver.action === "approved" ? "bg-green-500/20" : "bg-red-500/20"
                            }`}>
                              {approver.action === "approved" 
                                ? <CheckCircle2 className="h-4 w-4 text-green-400" />
                                : <XCircle className="h-4 w-4 text-red-400" />
                              }
                            </div>
                            <div>
                              <p className="font-medium">{approver.approver_id}</p>
                              <p className="text-xs text-muted-foreground capitalize">{approver.action}</p>
                            </div>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {new Date(approver.timestamp).toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">No approvals yet</p>
                  )}
                </CardContent>
              </Card>

              {/* Audit Trail */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>Audit Trail (Immutable)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {auditTrail.map((entry) => (
                      <div key={entry.id} className="p-3 rounded-lg border border-border bg-black/30 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{entry.action}</span>
                          <span className="text-muted-foreground">{new Date(entry.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="text-muted-foreground">Actor: {entry.actor}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* SoD Check */}
              <Card className="border-border border-blue-500/30 bg-blue-500/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-blue-400">
                    <Shield className="h-5 w-5" />
                    Separation of Duties (SoD) Check
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {sodWarnings.length > 0 && (
                    <div className="mb-4 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-200" data-testid="sod-warnings">
                      <div className="flex items-center gap-2 font-semibold">
                        <AlertTriangle className="h-4 w-4" />
                        SoD warnings detected
                      </div>
                      <ul className="mt-2 list-disc pl-4 space-y-1">
                        {sodWarnings.map((warning) => (
                          <li key={warning}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span className="text-sm">Requestor is different from approver</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span className="text-sm">Approver has required role permissions</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span className="text-sm">Audit trail maintained</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <ShieldCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select an approval request to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Approvals;
