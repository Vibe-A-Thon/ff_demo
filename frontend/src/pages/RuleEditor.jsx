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
} from "lucide-react";

const RuleEditor = () => {
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testRunning, setTestRunning] = useState(false);
  
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
    try {
      const response = await ruleAPI.create(formData);
      setRules([...rules, response.data]);
      setSelectedRule(response.data);
      setShowCreateModal(false);
      resetForm();
      toast.success("Rule created!");
    } catch (error) {
      toast.error("Failed to create rule");
    }
  };

  const handleUpdateRule = async () => {
    if (!selectedRule) return;
    try {
      await ruleAPI.update(selectedRule.id, formData);
      loadRules();
      setIsEditing(false);
      toast.success("Rule updated!");
    } catch (error) {
      toast.error("Failed to update rule");
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await ruleAPI.delete(ruleId);
      setRules(rules.filter(r => r.id !== ruleId));
      if (selectedRule?.id === ruleId) {
        setSelectedRule(rules[0] || null);
      }
      toast.success("Rule deleted");
    } catch (error) {
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
                  JSON View
                </TabsTrigger>
                <TabsTrigger value="tests">
                  <Zap className="h-4 w-4 mr-2" />
                  Test Results
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

                <TabsContent value="code" className="p-4 m-0">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>JSON Definition</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="p-4 bg-black/30 rounded-lg font-mono text-sm overflow-auto max-h-[60vh]">
                        {JSON.stringify(formData, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="tests" className="p-4 m-0">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Test Results</CardTitle>
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
                      ) : (
                        <div className="text-center text-muted-foreground py-8">
                          <Zap className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p>No test results yet</p>
                          <Button variant="outline" className="mt-4" onClick={handleRunTest}>
                            <Play className="h-4 w-4 mr-2" />
                            Run Tests
                          </Button>
                        </div>
                      )}
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
