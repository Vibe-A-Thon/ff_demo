import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Progress } from "../components/ui/progress";
import Editor from "@monaco-editor/react";
import { ruleAPI } from "../lib/api";
import { toast } from "sonner";
import {
  FileCode,
  Plus,
  Play,
  Save,
  Trash2,
  Edit,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Code,
  Settings,
  Zap,
  Shield,
  Wand2,
  MessageSquare,
  GitBranch,
  History,
  ListChecks,
  Gauge,
  Search,
  FileText,
} from "lucide-react";

const RuleEditor = () => {
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testRunning, setTestRunning] = useState(false);
  const [codeValue, setCodeValue] = useState("");
  const [jsonValue, setJsonValue] = useState("{}");
  const [jsonError, setJsonError] = useState("");
  const [testStatusFilter, setTestStatusFilter] = useState("all");
  const [testQuery, setTestQuery] = useState("");
  const [edgeCases, setEdgeCases] = useState([]);
  const [comments, setComments] = useState([
    {
      id: "thread-1",
      author: "techlead@fraudforge",
      role: "TechLead",
      message: "Confirm threshold aligns with policy for high-risk accounts.",
      timestamp: new Date().toISOString(),
      replies: [
        {
          id: "reply-1",
          author: "devtest@fraudforge",
          role: "Dev/Test",
          message: "Updated threshold to match compliance guidance.",
          timestamp: new Date().toISOString(),
        },
      ],
    },
  ]);
  const [commentDraft, setCommentDraft] = useState("");
  const [replyDrafts, setReplyDrafts] = useState({});
  const [historyEntries, setHistoryEntries] = useState([]);
  
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    rule_type: "velocity",
    conditions: [],
    actions: [],
    priority: 0,
  });

  const [newCondition, setNewCondition] = useState({ field: "", operator: ">", value: "" });
  const [newAction, setNewAction] = useState({ type: "flag", severity: "medium" });

  useEffect(() => {
    loadRules();
  }, []);

  useEffect(() => {
    if (!selectedRule) return;
    const defaultCode = `def evaluate_${selectedRule.name?.toLowerCase()?.replace(/\W+/g, "_") || "rule"}(transaction):\n    # TODO: Implement rule logic\n    return {"decision": "allow", "reason": "default"}`;
    setCodeValue(selectedRule.code || defaultCode);
    setJsonValue(JSON.stringify(selectedRule, null, 2));
    setJsonError("");
    setHistoryEntries(
      selectedRule.version_history || [
        {
          id: "v1",
          version: selectedRule.version || 1,
          author: "purple-team",
          summary: "Initial draft",
          timestamp: selectedRule.created_at || new Date().toISOString(),
        },
      ]
    );
  }, [selectedRule]);

  const loadRules = async () => {
    try {
      const response = await ruleAPI.getAll();
      setRules(response.data);
      if (response.data.length > 0) {
        setSelectedRule(response.data[0]);
        setFormData(response.data[0]);
      }
    } catch (error) {
      console.error("Failed to load rules:", error);
    }
  };

  const handleSelectRule = (rule) => {
    setSelectedRule(rule);
    setFormData(rule);
    setIsEditing(false);
  };

  const handleCreateRule = async () => {
    if (!formData.name) {
      toast.error("Please enter a rule name");
      return;
    }
    const tempId = `temp-${Date.now()}`;
    const optimisticRule = {
      ...formData,
      id: tempId,
      status: "draft",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setRules((prev) => [optimisticRule, ...prev]);
    setSelectedRule(optimisticRule);
    try {
      const response = await ruleAPI.create(formData);
      setRules((prev) => prev.map((rule) => (rule.id === tempId ? response.data : rule)));
      setSelectedRule(response.data);
      setShowCreateModal(false);
      resetForm();
      toast.success("Rule created!");
    } catch (error) {
      setRules((prev) => prev.filter((rule) => rule.id !== tempId));
      toast.error("Failed to create rule");
    }
  };

  const handleUpdateRule = async () => {
    if (!selectedRule) return;
    const previousRules = rules;
    setRules((prev) => prev.map((rule) => (rule.id === selectedRule.id ? { ...rule, ...formData } : rule)));
    setSelectedRule((prev) => ({ ...prev, ...formData }));
    try {
      await ruleAPI.update(selectedRule.id, formData);
      loadRules();
      setIsEditing(false);
      toast.success("Rule updated!");
    } catch (error) {
      setRules(previousRules);
      toast.error("Failed to update rule");
    }
  };

  const handleDeleteRule = async (ruleId) => {
    const previousRules = rules;
    try {
      setRules((prev) => prev.filter((rule) => rule.id !== ruleId));
      if (selectedRule?.id === ruleId) {
        setSelectedRule(null);
      }
      await ruleAPI.delete(ruleId);
      toast.success("Rule deleted");
    } catch (error) {
      setRules(previousRules);
      toast.error("Failed to delete rule");
    }
  };

  const handleRunTest = async () => {
    if (!selectedRule) return;
    setTestRunning(true);
    try {
      const response = await ruleAPI.test(selectedRule.id);
      setSelectedRule({ ...selectedRule, test_results: response.data });
      setFormData({ ...formData, test_results: response.data });
      toast.success("Tests completed!");
    } catch (error) {
      toast.error("Test execution failed");
    } finally {
      setTestRunning(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      rule_type: "velocity",
      conditions: [],
      actions: [],
      priority: 0,
    });
  };

  const addCondition = () => {
    if (!newCondition.field || !newCondition.value) {
      toast.error("Fill in condition fields");
      return;
    }
    setFormData({
      ...formData,
      conditions: [...formData.conditions, { ...newCondition }],
    });
    setNewCondition({ field: "", operator: ">", value: "" });
  };

  const removeCondition = (index) => {
    setFormData({
      ...formData,
      conditions: formData.conditions.filter((_, i) => i !== index),
    });
  };

  const addAction = () => {
    setFormData({
      ...formData,
      actions: [...formData.actions, { ...newAction }],
    });
    setNewAction({ type: "flag", severity: "medium" });
  };

  const removeAction = (index) => {
    setFormData({
      ...formData,
      actions: formData.actions.filter((_, i) => i !== index),
    });
  };

  const getStatusBadge = (status) => {
    const config = {
      draft: { color: "bg-zinc-500/15 text-zinc-400", icon: Edit },
      active: { color: "bg-green-500/15 text-green-400", icon: CheckCircle2 },
      disabled: { color: "bg-red-500/15 text-red-400", icon: XCircle },
    };
    const c = config[status] || config.draft;
    const Icon = c.icon;
    return (
      <Badge className={`${c.color} border border-current/20`}>
        <Icon className="h-3 w-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const buildRulePreview = () => {
    const conditions = (formData.conditions || [])
      .map((cond) => `${cond.field} ${cond.operator} ${cond.value}`)
      .join(" AND ");
    const actions = (formData.actions || [])
      .map((action) => `${action.type.toUpperCase()} (${action.severity})`)
      .join(", ");
    if (!conditions && !actions) {
      return "Rule preview will appear here once conditions/actions are defined.";
    }
    return `IF ${conditions || "<no conditions>"} THEN ${actions || "<no actions>"}`;
  };

  const handleApplyJson = () => {
    try {
      const parsed = JSON.parse(jsonValue);
      setFormData(parsed);
      setJsonError("");
      toast.success("JSON applied to form");
    } catch (error) {
      setJsonError("Invalid JSON. Fix errors before applying.");
    }
  };

  const generateEdgeCases = () => {
    const generated = (formData.conditions || []).slice(0, 3).map((cond, idx) => ({
      id: `edge-${idx + 1}`,
      title: `${cond.field || "signal"} boundary case`,
      description: `Exercise ${cond.field || "signal"} with ${cond.operator} ${cond.value} at boundary limits.`,
      severity: idx === 0 ? "high" : "medium",
    }));
    setEdgeCases(generated.length > 0 ? generated : [
      {
        id: "edge-default",
        title: "Missing baseline history",
        description: "Validate rule behavior when baseline data is absent.",
        severity: "medium",
      },
    ]);
    toast.success("Edge cases generated");
  };

  const runProfiler = () => {
    toast.success("Profiler run complete. Performance estimates updated.");
  };

  const exportComplianceReport = () => {
    const report = {
      rule: formData.name,
      score: complianceScore,
      checks: complianceChecks,
      generated_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `compliance-report-${formData.name || "rule"}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success("Compliance report exported");
  };

  const handleAddComment = () => {
    if (!commentDraft.trim()) return;
    setComments([
      {
        id: `thread-${Date.now()}`,
        author: "auditor@fraudforge",
        role: "Auditor",
        message: commentDraft,
        timestamp: new Date().toISOString(),
        replies: [],
      },
      ...comments,
    ]);
    setCommentDraft("");
  };

  const handleAddReply = (threadId) => {
    const reply = replyDrafts[threadId];
    if (!reply?.trim()) return;
    setComments(
      comments.map((thread) =>
        thread.id === threadId
          ? {
              ...thread,
              replies: [
                ...thread.replies,
                {
                  id: `reply-${Date.now()}`,
                  author: "techlead@fraudforge",
                  role: "TechLead",
                  message: reply,
                  timestamp: new Date().toISOString(),
                },
              ],
            }
          : thread
      )
    );
    setReplyDrafts({ ...replyDrafts, [threadId]: "" });
  };

  const testResults =
    selectedRule?.test_results?.results ||
    selectedRule?.test_results?.cases ||
    selectedRule?.test_results?.details ||
    [];
  const filteredTests = testResults.filter((result) => {
    const status = (result.status || result.result || (result.passed ? "passed" : "failed") || "unknown").toLowerCase();
    if (testStatusFilter !== "all" && status !== testStatusFilter) return false;
    if (!testQuery) return true;
    const target = `${result.name || ""} ${result.id || ""} ${result.message || ""}`.toLowerCase();
    return target.includes(testQuery.toLowerCase());
  });

  const complianceChecks = [
    {
      id: "comp-desc",
      title: "Description provided",
      passed: Boolean(formData.description?.trim()),
    },
    {
      id: "comp-conditions",
      title: "At least one condition",
      passed: (formData.conditions || []).length > 0,
    },
    {
      id: "comp-actions",
      title: "At least one action",
      passed: (formData.actions || []).length > 0,
    },
    {
      id: "comp-priority",
      title: "Priority within policy range",
      passed: formData.priority >= 0 && formData.priority <= 10,
    },
  ];
  const complianceScore = Math.round(
    (complianceChecks.filter((check) => check.passed).length / complianceChecks.length) * 100
  );
  const estimatedLatency = 12 + (formData.conditions?.length || 0) * 3;
  const estimatedCost = 22 + (formData.actions?.length || 0) * 6;

  return (
    <div className="h-full flex" data-testid="rule-editor">
      {/* Rule List */}
      <div className="w-72 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Rules</h2>
            <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
              <DialogTrigger asChild>
                <Button size="sm" data-testid="create-rule-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  New
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-card border-border max-w-2xl" data-testid="create-rule-modal">
                <DialogHeader>
                  <DialogTitle>Create New Rule</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 max-h-[70vh] overflow-auto">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-muted-foreground">Name *</label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="e.g., VEL-002"
                        data-testid="rule-name-input"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Type</label>
                      <Select
                        value={formData.rule_type}
                        onValueChange={(v) => setFormData({ ...formData, rule_type: v })}
                      >
                        <SelectTrigger data-testid="rule-type-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="velocity">Velocity</SelectItem>
                          <SelectItem value="pattern">Pattern</SelectItem>
                          <SelectItem value="device">Device</SelectItem>
                          <SelectItem value="geo">Geolocation</SelectItem>
                          <SelectItem value="amount">Amount</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Description</label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Rule description..."
                      data-testid="rule-description-input"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Priority (0-10)</label>
                    <Input
                      type="number"
                      min="0"
                      max="10"
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                      data-testid="rule-priority-input"
                    />
                  </div>
                  <Button onClick={handleCreateRule} className="w-full" data-testid="confirm-create-rule-btn">
                    <Plus className="h-4 w-4 mr-2" />
                    Create Rule
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {rules.map((rule) => (
              <div
                key={rule.id}
                onClick={() => handleSelectRule(rule)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedRule?.id === rule.id
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-border hover:border-zinc-600 bg-card"
                }`}
                data-testid={`rule-${rule.id}`}
              >
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-400" />
                  <span className="font-medium">{rule.name}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <Badge variant="outline" className="text-xs capitalize">{rule.rule_type}</Badge>
                  {getStatusBadge(rule.status)}
                </div>
              </div>
            ))}
            {rules.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <FileCode className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No rules yet</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Rule Editor */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedRule ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold flex items-center gap-2">
                  <Shield className="h-5 w-5 text-blue-400" />
                  {selectedRule.name}
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Version {selectedRule.version || 1} • Last updated: {new Date(selectedRule.updated_at || selectedRule.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={handleRunTest}
                  disabled={testRunning}
                  data-testid="run-test-btn"
                >
                  <Play className={`h-4 w-4 mr-2 ${testRunning ? 'animate-spin' : ''}`} />
                  Run Tests
                </Button>
                {isEditing ? (
                  <Button onClick={handleUpdateRule} data-testid="save-rule-btn">
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                ) : (
                  <Button onClick={() => setIsEditing(true)} data-testid="edit-rule-btn">
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                )}
                <Button
                  variant="destructive"
                  onClick={() => handleDeleteRule(selectedRule.id)}
                  data-testid="delete-rule-btn"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <Tabs defaultValue="form" className="flex-1 flex flex-col overflow-hidden">
              <TabsList className="mx-4 mt-4 w-fit">
                <TabsTrigger value="form">
                  <Settings className="h-4 w-4 mr-2" />
                  Rule Form
                </TabsTrigger>
                <TabsTrigger value="code">
                  <Code className="h-4 w-4 mr-2" />
                  Code Studio
                </TabsTrigger>
                <TabsTrigger value="tests">
                  <Zap className="h-4 w-4 mr-2" />
                  Test Results
                </TabsTrigger>
                <TabsTrigger value="quality">
                  <ListChecks className="h-4 w-4 mr-2" />
                  Quality
                </TabsTrigger>
                <TabsTrigger value="collab">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Comments
                </TabsTrigger>
                <TabsTrigger value="history">
                  <History className="h-4 w-4 mr-2" />
                  Version History
                </TabsTrigger>
              </TabsList>

              <ScrollArea className="flex-1">
                <TabsContent value="form" className="p-4 m-0 space-y-6">
                  {/* Basic Info */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Basic Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-muted-foreground">Name</label>
                          <Input
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            disabled={!isEditing}
                          />
                        </div>
                        <div>
                          <label className="text-sm text-muted-foreground">Type</label>
                          <Select
                            value={formData.rule_type}
                            onValueChange={(v) => setFormData({ ...formData, rule_type: v })}
                            disabled={!isEditing}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="velocity">Velocity</SelectItem>
                              <SelectItem value="pattern">Pattern</SelectItem>
                              <SelectItem value="device">Device</SelectItem>
                              <SelectItem value="geo">Geolocation</SelectItem>
                              <SelectItem value="amount">Amount</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Description</label>
                        <Textarea
                          value={formData.description}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                          disabled={!isEditing}
                        />
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Priority</label>
                        <Input
                          type="number"
                          value={formData.priority}
                          onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                          disabled={!isEditing}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Conditions */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Conditions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 mb-4">
                        {formData.conditions?.map((cond, idx) => (
                          <div key={idx} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                            <span className="font-mono text-sm flex-1">
                              {cond.field} {cond.operator} {cond.value}
                            </span>
                            {isEditing && (
                              <Button variant="ghost" size="icon" onClick={() => removeCondition(idx)}>
                                <XCircle className="h-4 w-4 text-red-400" />
                              </Button>
                            )}
                          </div>
                        ))}
                        {(!formData.conditions || formData.conditions.length === 0) && (
                          <p className="text-muted-foreground text-sm">No conditions defined</p>
                        )}
                      </div>
                      {isEditing && (
                        <div className="flex gap-2">
                          <Input
                            placeholder="Field"
                            value={newCondition.field}
                            onChange={(e) => setNewCondition({ ...newCondition, field: e.target.value })}
                          />
                          <Select
                            value={newCondition.operator}
                            onValueChange={(v) => setNewCondition({ ...newCondition, operator: v })}
                          >
                            <SelectTrigger className="w-24">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value=">">&gt;</SelectItem>
                              <SelectItem value="<">&lt;</SelectItem>
                              <SelectItem value="=">=</SelectItem>
                              <SelectItem value="!=">!=</SelectItem>
                              <SelectItem value=">=">&gt;=</SelectItem>
                              <SelectItem value="<=">&lt;=</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input
                            placeholder="Value"
                            value={newCondition.value}
                            onChange={(e) => setNewCondition({ ...newCondition, value: e.target.value })}
                          />
                          <Button onClick={addCondition}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Actions */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Actions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 mb-4">
                        {formData.actions?.map((action, idx) => (
                          <div key={idx} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                            <Badge variant="outline" className="capitalize">{action.type}</Badge>
                            <Badge className={`${
                              action.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                              action.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                              action.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-blue-500/20 text-blue-400'
                            }`}>
                              {action.severity}
                            </Badge>
                            {isEditing && (
                              <Button variant="ghost" size="icon" onClick={() => removeAction(idx)} className="ml-auto">
                                <XCircle className="h-4 w-4 text-red-400" />
                              </Button>
                            )}
                          </div>
                        ))}
                        {(!formData.actions || formData.actions.length === 0) && (
                          <p className="text-muted-foreground text-sm">No actions defined</p>
                        )}
                      </div>
                      {isEditing && (
                        <div className="flex gap-2">
                          <Select
                            value={newAction.type}
                            onValueChange={(v) => setNewAction({ ...newAction, type: v })}
                          >
                            <SelectTrigger className="flex-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="flag">Flag</SelectItem>
                              <SelectItem value="block">Block</SelectItem>
                              <SelectItem value="challenge">Challenge</SelectItem>
                              <SelectItem value="alert">Alert</SelectItem>
                            </SelectContent>
                          </Select>
                          <Select
                            value={newAction.severity}
                            onValueChange={(v) => setNewAction({ ...newAction, severity: v })}
                          >
                            <SelectTrigger className="flex-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="low">Low</SelectItem>
                              <SelectItem value="medium">Medium</SelectItem>
                              <SelectItem value="high">High</SelectItem>
                              <SelectItem value="critical">Critical</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button onClick={addAction}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="code" className="p-4 m-0 space-y-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Monaco Editor (Python/JSON)</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Tabs defaultValue="python" className="w-full">
                        <TabsList className="w-fit">
                          <TabsTrigger value="python" data-testid="code-tab-python">Python</TabsTrigger>
                          <TabsTrigger value="json" data-testid="code-tab-json">JSON</TabsTrigger>
                        </TabsList>
                        <TabsContent value="python" className="mt-4">
                          <Editor
                            height="360px"
                            theme="vs-dark"
                            language="python"
                            value={codeValue}
                            onChange={(value) => setCodeValue(value || "")}
                            options={{ minimap: { enabled: false } }}
                          />
                          <p className="text-xs text-muted-foreground mt-2">
                            Python rule logic used in execution sandbox.
                          </p>
                        </TabsContent>
                        <TabsContent value="json" className="mt-4">
                          <Editor
                            height="360px"
                            theme="vs-dark"
                            language="json"
                            value={jsonValue}
                            onChange={(value) => setJsonValue(value || "")}
                            options={{ minimap: { enabled: false } }}
                          />
                          {jsonError && (
                            <p className="text-xs text-red-400 mt-2" data-testid="json-error">
                              {jsonError}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-3">
                            <Button variant="outline" onClick={handleApplyJson} data-testid="apply-json-btn">
                              <Save className="h-4 w-4 mr-2" />
                              Apply JSON to Form
                            </Button>
                          </div>
                        </TabsContent>
                      </Tabs>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Live Rule Preview</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 bg-black/30 rounded-lg font-mono text-sm">
                        {buildRulePreview()}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="tests" className="p-4 m-0 space-y-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Test Runner & Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {selectedRule.test_results ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-3 gap-4">
                            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                              <p className="text-2xl font-bold font-mono text-green-400">
                                {selectedRule.test_results.passed}
                              </p>
                              <p className="text-sm text-muted-foreground">Passed</p>
                            </div>
                            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                              <p className="text-2xl font-bold font-mono text-red-400">
                                {selectedRule.test_results.failed}
                              </p>
                              <p className="text-sm text-muted-foreground">Failed</p>
                            </div>
                            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                              <p className="text-2xl font-bold font-mono text-blue-400">
                                {selectedRule.test_results.coverage}%
                              </p>
                              <p className="text-sm text-muted-foreground">Coverage</p>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-3">
                            <div>
                              <label className="text-sm text-muted-foreground">Execution Time</label>
                              <p className="font-mono">{selectedRule.test_results.execution_time}s</p>
                            </div>
                            <div>
                              <label className="text-sm text-muted-foreground">Last Run</label>
                              <p className="font-mono text-sm">
                                {new Date(selectedRule.test_results.timestamp).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-muted-foreground py-8">
                          <Zap className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p>No test results yet</p>
                        </div>
                      )}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button variant="outline" onClick={handleRunTest} data-testid="run-tests-panel-btn">
                          <Play className="h-4 w-4 mr-2" />
                          Run Tests
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Results Detail</CardTitle>
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
                        <div className="relative flex-1 min-w-[220px]">
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
                          filteredTests.map((result, idx) => (
                            <div key={idx} className="p-3 bg-zinc-800/50 rounded-lg border border-border">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-sm">
                                  {result.name || result.id || `Test ${idx + 1}`}
                                </span>
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${
                                    (result.status || result.result || (result.passed ? "passed" : "failed")) === "passed"
                                      ? "border-green-500/30 text-green-400"
                                      : "border-red-500/30 text-red-400"
                                  }`}
                                >
                                  {result.status || result.result || (result.passed ? "passed" : "failed")}
                                </Badge>
                              </div>
                              {result.message && (
                                <p className="text-xs text-muted-foreground mt-2">{result.message}</p>
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
                </TabsContent>

                <TabsContent value="quality" className="p-4 m-0 space-y-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Wand2 className="h-5 w-5 text-purple-400" />
                        Edge-Case Generator
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Button variant="outline" onClick={generateEdgeCases} data-testid="generate-edge-cases-btn">
                        <Wand2 className="h-4 w-4 mr-2" />
                        Generate Edge Cases
                      </Button>
                      <div className="mt-4 space-y-3">
                        {edgeCases.map((edge) => (
                          <div key={edge.id} className="p-3 bg-zinc-800/50 rounded-lg border border-border">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">{edge.title}</span>
                              <Badge variant="outline" className="text-xs capitalize">
                                {edge.severity}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">{edge.description}</p>
                          </div>
                        ))}
                        {edgeCases.length === 0 && (
                          <p className="text-sm text-muted-foreground">Generate edge cases to see suggested tests.</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Gauge className="h-5 w-5 text-blue-400" />
                        Performance Profiler
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Button variant="outline" onClick={runProfiler} data-testid="run-profiler-btn">
                        <Gauge className="h-4 w-4 mr-2" />
                        Run Profiler
                      </Button>
                      <div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Estimated Latency</span>
                          <span className="font-mono">{estimatedLatency}ms</span>
                        </div>
                        <Progress value={Math.min(100, estimatedLatency)} className="mt-2" />
                      </div>
                      <div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Compute Cost</span>
                          <span className="font-mono">{estimatedCost} RU</span>
                        </div>
                        <Progress value={Math.min(100, estimatedCost)} className="mt-2" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <ListChecks className="h-5 w-5 text-green-400" />
                        Compliance Checker
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm text-muted-foreground">Compliance Score</span>
                        <span className="font-mono text-lg">{complianceScore}%</span>
                      </div>
                      <Button variant="outline" size="sm" onClick={exportComplianceReport} data-testid="export-compliance-btn">
                        <FileText className="h-4 w-4 mr-2" />
                        Export Report
                      </Button>
                      <div className="space-y-3 mt-4">
                        {complianceChecks.map((check) => (
                          <div key={check.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded">
                            <span className="text-sm">{check.title}</span>
                            <Badge
                              variant="outline"
                              className={check.passed ? "border-green-500/30 text-green-400" : "border-red-500/30 text-red-400"}
                            >
                              {check.passed ? "Pass" : "Fail"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="collab" className="p-4 m-0 space-y-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MessageSquare className="h-5 w-5 text-yellow-400" />
                        Collaboration Comments
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Textarea
                          value={commentDraft}
                          onChange={(event) => setCommentDraft(event.target.value)}
                          placeholder="Add a comment for reviewers..."
                          data-testid="comment-input"
                        />
                        <Button onClick={handleAddComment} data-testid="add-comment-btn">
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Add Comment
                        </Button>
                      </div>
                      <div className="space-y-4">
                        {comments.map((thread) => (
                          <div key={thread.id} className="p-3 bg-zinc-900/50 border border-border rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium">{thread.author}</p>
                                <p className="text-xs text-muted-foreground">{thread.role}</p>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {new Date(thread.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-sm mt-2">{thread.message}</p>
                            <div className="mt-3 space-y-2">
                              {thread.replies.map((reply) => (
                                <div key={reply.id} className="ml-4 p-2 bg-black/30 rounded">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <p className="text-xs font-medium">{reply.author}</p>
                                      <p className="text-[11px] text-muted-foreground">{reply.role}</p>
                                    </div>
                                    <span className="text-[11px] text-muted-foreground">
                                      {new Date(reply.timestamp).toLocaleString()}
                                    </span>
                                  </div>
                                  <p className="text-xs mt-1">{reply.message}</p>
                                </div>
                              ))}
                            </div>
                            <div className="mt-3 flex gap-2">
                              <Input
                                value={replyDrafts[thread.id] || ""}
                                onChange={(event) =>
                                  setReplyDrafts({ ...replyDrafts, [thread.id]: event.target.value })
                                }
                                placeholder="Reply..."
                                data-testid={`reply-input-${thread.id}`}
                              />
                              <Button variant="outline" onClick={() => handleAddReply(thread.id)} data-testid={`reply-btn-${thread.id}`}>
                                Reply
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="history" className="p-4 m-0 space-y-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <GitBranch className="h-5 w-5 text-blue-400" />
                        Version History
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {historyEntries.map((entry) => (
                          <div key={entry.id} className="p-3 bg-zinc-800/50 border border-border rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium">v{entry.version}</p>
                                <p className="text-xs text-muted-foreground">{entry.summary}</p>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {new Date(entry.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs font-mono">{entry.author}</span>
                              <Button variant="outline" size="sm" data-testid={`history-view-${entry.id}`}>
                                View Diff
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </ScrollArea>
            </Tabs>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <FileCode className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select a rule to edit</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RuleEditor;
