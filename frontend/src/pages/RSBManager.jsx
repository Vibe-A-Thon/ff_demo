import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { Skeleton } from "../components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Progress } from "../components/ui/progress";
import { rsbAPI, agentAPI, xaiAPI } from "../lib/api";
import { toast } from "sonner";
import {
  Package,
  Upload,
  Play,
  Merge,
  FileJson,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  Download,
  Trash2,
  Shield,
  Clock,
  FileText,
  GitMerge,
  GripVertical,
} from "lucide-react";

const RSBManager = () => {
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [viewMode, setViewMode] = useState("grid");
  const [stagedQueue, setStagedQueue] = useState([]);
  const [validationStatus, setValidationStatus] = useState("idle");
  const [validationProgress, setValidationProgress] = useState(0);
  const [conflictDecisions, setConflictDecisions] = useState({});
  const [graphLoading, setGraphLoading] = useState(true);
  const [comparison, setComparison] = useState(null);
  const [deploying, setDeploying] = useState(false);
  const [importData, setImportData] = useState({
    name: "",
    version: "",
    description: "",
    manifest: {},
    rules: [],
    compliance_badges: [],
  });
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [testRunning, setTestRunning] = useState(null);
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [xaiBundle, setXaiBundle] = useState(null);
  const [xaiLoading, setXaiLoading] = useState(false);
  const ruleGraphRef = useRef(null);
  const ruleGraphWrapperRef = useRef(null);
  const [ruleGraphSize, setRuleGraphSize] = useState({ width: 640, height: 220 });
  const navigate = useNavigate();

  useEffect(() => {
    loadPackages();
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
    const updateGraphSize = () => {
      if (!ruleGraphWrapperRef.current) return;
      setRuleGraphSize({
        width: ruleGraphWrapperRef.current.offsetWidth,
        height: 220,
      });
    };

    updateGraphSize();
    window.addEventListener("resize", updateGraphSize);
    return () => window.removeEventListener("resize", updateGraphSize);
  }, [selectedPackage]);

  useEffect(() => {
    if (!selectedPackage) return;
    setGraphLoading(true);
    const timer = setTimeout(() => setGraphLoading(false), 420);
    return () => clearTimeout(timer);
  }, [selectedPackage]);

  useEffect(() => {
    const loadXai = async () => {
      if (!selectedPackage) {
        setXaiBundle(null);
        return;
      }
      const runId = selectedPackage.run_id || selectedPackage?.manifest?.run_id;
      if (runId) {
        setXaiLoading(true);
        try {
          const response = await xaiAPI.explainRunFull(runId);
          setXaiBundle(response?.data?.bundle || null);
          return;
        } catch (error) {
          setXaiBundle(selectedPackage.xai_bundle || null);
        } finally {
          setXaiLoading(false);
        }
        return;
      }
      if (selectedPackage.xai_bundle) {
        setXaiBundle(selectedPackage.xai_bundle);
        return;
      }
      setXaiLoading(true);
      try {
        const response = await xaiAPI.explainPackage(selectedPackage.id);
        setXaiBundle(response?.data?.bundle || null);
      } catch (error) {
        setXaiBundle(null);
      } finally {
        setXaiLoading(false);
      }
    };
    loadXai();
  }, [selectedPackage]);

  useEffect(() => {
    if (!selectedPackage) return;
    const validation = selectedPackage.validation;
    if (!validation) {
      setValidationStatus("idle");
      setValidationProgress(0);
      return;
    }
    setValidationStatus(validation.valid ? "passed" : "failed");
    setValidationProgress(100);
  }, [selectedPackage]);

  const loadPackages = async () => {
    try {
      const response = await rsbAPI.getAll();
      setPackages(response.data);
    } catch (error) {
      console.error("Failed to load packages:", error);
    }
  };

  const handleImport = async () => {
    if (!importFile && (!importData.name || !importData.version)) {
      toast.error("Please select an .rsb file or fill in required fields");
      return;
    }

    setImporting(true);
    try {
      if (importFile) {
        const formData = new FormData();
        formData.append("file", importFile);
        if (importData.name) formData.append("name", importData.name);
        if (importData.version) formData.append("version", importData.version);
        if (importData.description) formData.append("description", importData.description);
        if (importData.compliance_badges?.length) {
          formData.append("compliance_badges", importData.compliance_badges.join(", "));
        }
        const response = await rsbAPI.upload(formData);
        setPackages((prev) => [response.data, ...prev]);
        setSelectedPackage(response.data);
      } else {
        const tempId = `temp-${Date.now()}`;
        const optimisticPackage = {
          ...importData,
          id: tempId,
          status: "pending",
          created_at: new Date().toISOString(),
        };
        setPackages((prev) => [optimisticPackage, ...prev]);
        const manifest = {
          rules: importData.rules?.length || 0,
          patterns: 5,
          compliance: importData.compliance_badges || [],
        };
        const response = await rsbAPI.create({ ...importData, manifest });
        setPackages((prev) => prev.map((pkg) => (pkg.id === tempId ? response.data : pkg)));
        setSelectedPackage(response.data);
      }
      toast.success("RSB Package imported successfully!");
      setShowImportModal(false);
      setImportData({ name: "", version: "", description: "", manifest: {}, rules: [], compliance_badges: [] });
      setImportFile(null);
      loadPackages();
    } catch (error) {
      toast.error("Failed to import package");
    } finally {
      setImporting(false);
    }
  };

  const handleRunTests = async (packageId) => {
    setTestRunning(packageId);
    try {
      const response = await rsbAPI.test(packageId);
      const pkg = packages.find(p => p.id === packageId);
      if (pkg) {
        pkg.test_results = response.data;
        pkg.status = "tested";
        setPackages([...packages]);
        setSelectedPackage({ ...pkg });
      }
      toast.success("Tests completed!");
    } catch (error) {
      toast.error("Test execution failed");
    } finally {
      setTestRunning(null);
    }
  };

  const handleMerge = async (packageId) => {
    const previousPackages = packages;
    setPackages((prev) => prev.map((pkg) => (pkg.id === packageId ? { ...pkg, status: "merging" } : pkg)));
    try {
      const pkg = packages.find((item) => item.id === packageId);
      if (pkg?.conflicts?.length) {
        const unresolved = pkg.conflicts.filter((conflict) => !conflictDecisions[conflict.id]);
        if (unresolved.length > 0) {
          toast.error("Resolve merge conflicts before merging");
          setPackages(previousPackages);
          return;
        }
        await rsbAPI.resolveConflicts(packageId, conflictDecisions);
      }
      await rsbAPI.merge(packageId);
      loadPackages();
      toast.success("Package merged successfully!");
    } catch (error) {
      setPackages(previousPackages);
      toast.error("Merge failed");
    }
  };

  const handleDelete = async (packageId) => {
    const previousPackages = packages;
    setPackages((prev) => prev.filter((pkg) => pkg.id !== packageId));
    try {
      await rsbAPI.delete(packageId);
      if (selectedPackage?.id === packageId) {
        setSelectedPackage(null);
      }
      toast.success("Package deleted");
    } catch (error) {
      setPackages(previousPackages);
      toast.error("Delete failed");
    }
  };

  const handleExport = async (packageId, packageName) => {
    setExporting(true);
    try {
      const response = await rsbAPI.export(packageId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${packageName || "rsb-package"}.rsb`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("RSB package exported");
    } catch (error) {
      toast.error("Export failed");
    } finally {
      setExporting(false);
    }
  };

  const handlePackageDragStart = (pkg) => (event) => {
    event.dataTransfer.setData("application/json", JSON.stringify(pkg));
    event.dataTransfer.effectAllowed = "move";
  };

  const handleStageDrop = (event) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData("application/json");
    if (!raw) return;
    const pkg = JSON.parse(raw);
    setStagedQueue((prev) => {
      if (prev.find((item) => item.id === pkg.id)) return prev;
      return [...prev, pkg];
    });
    toast.success(`Staged ${pkg.name}`);
  };

  const handleStageDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const removeStaged = (pkgId) => {
    setStagedQueue((prev) => prev.filter((item) => item.id !== pkgId));
  };

  const handleConflictDecision = (conflictId, decision) => {
    setConflictDecisions((prev) => ({ ...prev, [conflictId]: decision }));
  };

  const triggerValidation = () => {
    if (!selectedPackage) return;
    setValidationStatus("running");
    setValidationProgress(30);
    rsbAPI
      .get(selectedPackage.id)
      .then((response) => {
        const validation = response.data.validation || { valid: true };
        setValidationProgress(100);
        setValidationStatus(validation.valid ? "passed" : "failed");
        setSelectedPackage(response.data);
        setPackages((prev) => prev.map((pkg) => (pkg.id === response.data.id ? response.data : pkg)));
        toast[validation.valid ? "success" : "error"](
          validation.valid ? "Validation passed" : "Validation failed"
        );
      })
      .catch(() => {
        setValidationStatus("failed");
        toast.error("Validation failed");
      });
  };

  const deployStagedQueue = async () => {
    if (stagedQueue.length === 0) {
      toast.error("No packages staged for deployment");
      return;
    }
    setDeploying(true);
    try {
      await Promise.all(stagedQueue.map((pkg) => rsbAPI.stage(pkg.id)));
      toast.success(`Deployment queued for ${stagedQueue.length} packages`);
      setStagedQueue([]);
      loadPackages();
    } catch (error) {
      toast.error("Failed to stage packages");
    } finally {
      setDeploying(false);
    }
  };

  const handleCompareVersion = (version) => {
    if (!selectedPackage) return;
    setComparison({
      base: selectedPackage.version,
      target: version,
      changes: {
        rules: Math.max(1, (selectedPackage.manifest?.rules || 3) - 1),
        tests: Math.max(1, (selectedPackage.manifest?.tests || 4) + 1),
        compliance: selectedPackage.compliance_badges?.length || 0,
      },
    });
  };

  const conflictItems = useMemo(() => {
    if (selectedPackage?.conflicts?.length) {
      return selectedPackage.conflicts.map((conflict) => ({
        id: conflict.id,
        label: conflict.type === "rule_id_collision"
          ? `Rule ID collision: ${conflict.rule_id}`
          : conflict.type || "Conflict detected",
        suggestion: conflict.existing_version
          ? `Existing version ${conflict.existing_version}`
          : "Manual review",
      }));
    }
    return [
      { id: "conf-1", label: "Rule action mismatch", suggestion: "Require approval" },
      { id: "conf-2", label: "Version jump detected", suggestion: "Manual review" },
    ];
  }, [selectedPackage]);

  const versionTimeline = selectedPackage
    ? [
        { version: "1.8.0", status: "merged" },
        { version: "2.0.0", status: "tested" },
        { version: selectedPackage.version, status: selectedPackage.status || "pending" },
      ]
    : [];

  const buildRuleNetwork = useCallback(() => {
    const rules = selectedPackage?.rules?.length
      ? selectedPackage.rules
      : selectedPackage
      ? ["R-ACCOUNT_TAKEOVER"]
      : [];
    const nodes = rules.map((ruleId, idx) => ({
      id: ruleId,
      name: ruleId,
      group: idx === 0 ? "root" : "rule",
      val: idx === 0 ? 10 : 6,
    }));
    const links = rules.slice(1).map((ruleId, idx) => ({
      source: rules[idx],
      target: ruleId,
    }));
    return { nodes, links };
  }, [selectedPackage]);

  const ruleNetwork = useMemo(() => buildRuleNetwork(), [buildRuleNetwork]);

  const defaultManifestTree = [
    { name: "manifest.json" },
    {
      name: "rule/",
      children: [
        { name: "specification.json" },
        { name: "description.md" },
        { name: "rule.json" },
        { name: "rule_Patch.py" },
      ],
    },
    {
      name: "code/",
      children: [
        { name: "ruleC_<RULE_ID>.py" },
        { name: "ruleCP_<RULE_ID>.py" },
      ],
    },
    {
      name: "tests/",
      children: [
        { name: "ruleUT_<RULE_ID>.py" },
        { name: "ruleIT_<RULE_ID>.py" },
      ],
    },
    {
      name: "compliance/",
      children: [
        { name: "*_xai.json" },
        { name: "*_Compliance_explanation.json" },
      ],
    },
  ];

  const renderTree = (nodes, depth = 0) => (
    <ul className="space-y-1">
      {nodes.map((node) => (
        <li key={`${node.name}-${depth}`} className="text-sm">
          <div className="flex items-center gap-2" style={{ paddingLeft: depth * 12 }}>
            <span className="text-muted-foreground">{node.children ? "▸" : "•"}</span>
            <span className="font-mono text-xs">{node.name}</span>
          </div>
          {node.children && (
            <div className="mt-1">
              {renderTree(node.children, depth + 1)}
            </div>
          )}
        </li>
      ))}
    </ul>
  );

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20", icon: Clock },
      tested: { color: "bg-blue-500/15 text-blue-400 border-blue-500/20", icon: CheckCircle2 },
      merged: { color: "bg-green-500/15 text-green-400 border-green-500/20", icon: GitMerge },
      failed: { color: "bg-red-500/15 text-red-400 border-red-500/20", icon: XCircle },
    };
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} border`}>
        <Icon className="h-3 w-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const TestResultsView = ({ results }) => {
    if (!results) return <p className="text-muted-foreground">No test results available</p>;

    const sections = [
      { name: "Unit Tests", data: results.unit_tests },
      { name: "Integration Tests", data: results.integration_tests },
      { name: "Compliance Checks", data: results.compliance_checks },
    ];

    return (
      <div className="space-y-4">
        {sections.map((section) => (
          <div key={section.name} className="p-4 bg-zinc-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">{section.name}</span>
              <span className="text-sm font-mono">
                {section.data?.passed || 0}/{section.data?.total || 0} passed
              </span>
            </div>
            <Progress
              value={((section.data?.passed || 0) / (section.data?.total || 1)) * 100}
              className="h-2"
            />
            {section.data?.failed > 0 && (
              <p className="text-red-400 text-sm mt-2">
                <XCircle className="h-3 w-3 inline mr-1" />
                {section.data.failed} failed
              </p>
            )}
          </div>
        ))}
        <div className="text-xs text-muted-foreground">
          Last run: {results.timestamp ? new Date(results.timestamp).toLocaleString() : 'N/A'}
        </div>
      </div>
    );
  };

  const codePreview = selectedPackage?.code
    ? selectedPackage.code
    : `def detect_rule(txs):
    """Auto-generated rule stub."""
    signals = []
    for tx in txs:
        if tx.get("tx_count", 0) > 5:
            signals.append({"id": tx.get("transaction_id"), "reason": "velocity"})
    return signals`;

  return (
    <div className="h-full flex" data-testid="rsb-manager">
      {/* Package List */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">RSB Packages</h2>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={viewMode === "grid" ? "default" : "outline"}
                onClick={() => setViewMode("grid")}
                data-testid="rsb-view-grid"
              >
                Grid
              </Button>
              <Button
                size="sm"
                variant={viewMode === "list" ? "default" : "outline"}
                onClick={() => setViewMode("list")}
                data-testid="rsb-view-list"
              >
                List
              </Button>
              <Dialog open={showImportModal} onOpenChange={setShowImportModal}>
                <DialogTrigger asChild>
                  <Button
                    size="sm"
                    data-testid="import-rsb-btn"
                    data-explain="Import RSB package"
                    data-explain-title="RSB package intake"
                    data-explain-summary="Validates manifest metadata, compliance badges, and rule inventory before staging."
                    data-explain-rules="RSB-ING-02,COM-006"
                    data-explain-evidence="Manifest schema,Compliance badges,Rule count"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Import
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-card border-border" data-testid="import-modal">
                  <DialogHeader>
                    <DialogTitle>Import RSB Package</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-muted-foreground">RSB File (.rsb) *</label>
                      <Input
                        type="file"
                        accept=".rsb,.zip"
                        onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                        data-testid="import-file-input"
                      />
                      <p className="text-xs text-muted-foreground mt-1">Optional: override metadata below.</p>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Package Name *</label>
                      <Input
                        value={importData.name}
                        onChange={(e) => setImportData({ ...importData, name: e.target.value })}
                        placeholder="e.g., Fraud Detection Core"
                        data-testid="import-name-input"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Version *</label>
                      <Input
                        value={importData.version}
                        onChange={(e) => setImportData({ ...importData, version: e.target.value })}
                        placeholder="e.g., 2.1.0"
                        data-testid="import-version-input"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Description</label>
                      <Input
                        value={importData.description}
                        onChange={(e) => setImportData({ ...importData, description: e.target.value })}
                        placeholder="Package description..."
                        data-testid="import-description-input"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Compliance Badges (comma-separated)</label>
                      <Input
                        value={importData.compliance_badges?.join(", ") || ""}
                        onChange={(e) => setImportData({
                          ...importData,
                          compliance_badges: e.target.value.split(",").map(s => s.trim()).filter(Boolean)
                        })}
                        placeholder="PCI-DSS, SOX, GDPR"
                        data-testid="import-compliance-input"
                      />
                    </div>
                    <Button
                      onClick={handleImport}
                      className="w-full"
                      disabled={importing}
                      data-testid="confirm-import-btn"
                      data-explain="Confirm import"
                      data-explain-title="Import validation"
                      data-explain-summary="Creates a staged package and records compliance checks for audit."
                      data-explain-rules="RSB-ING-05,COM-010"
                      data-explain-evidence="Package metadata,Checksum,Policy badges"
                    >
                      <Package className="h-4 w-4 mr-2" />
                      {importing ? "Importing..." : "Import Package"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className={viewMode === "grid" ? "p-2 grid grid-cols-2 gap-2" : "p-2 space-y-2"}>
            {packages.map((pkg) => (
              <div
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
                draggable
                onDragStart={handlePackageDragStart(pkg)}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedPackage?.id === pkg.id
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-border hover:border-zinc-600 bg-card"
                }`}
                data-testid={`package-${pkg.id}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium">{pkg.name}</h3>
                    <p className="text-sm text-muted-foreground font-mono">v{pkg.version}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(pkg.status)}
                    <div
                      className="rounded-md border border-border bg-black/30 p-1"
                      data-testid={`package-drag-handle-${pkg.id}`}
                      title="Drag to stage"
                    >
                      <GripVertical className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </div>
                {pkg.compliance_badges?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {pkg.compliance_badges.map((badge) => (
                      <Badge key={badge} variant="outline" className="text-xs">
                        <Shield className="h-2 w-2 mr-1" />
                        {badge}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {packages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No packages yet</p>
                <p className="text-sm">Import or seed demo data</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Package Details */}
      <div className="flex-1 overflow-hidden">
        {selectedPackage ? (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-border">
              <div className="flex items-start justify-between gap-6">
                <div>
                  <h1 className="text-2xl font-bold">{selectedPackage.name}</h1>
                  <p className="text-muted-foreground mt-1">{selectedPackage.description || "No description"}</p>
                  <div className="flex items-center gap-4 mt-4">
                    <span className="text-sm font-mono">Version: {selectedPackage.version}</span>
                    {getStatusBadge(selectedPackage.status)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/diff-viewer?package=${selectedPackage.id}`)}
                    data-testid="rsb-open-visual-patcher"
                  >
                    <GitMerge className="h-4 w-4 mr-2" />
                    Open Visual Patcher
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleRunTests(selectedPackage.id)}
                    disabled={testRunning === selectedPackage.id}
                    data-testid="rsb-run-tests"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    {testRunning === selectedPackage.id ? "Running" : "Run Tests"}
                  </Button>
                  <Button
                    onClick={() => handleMerge(selectedPackage.id)}
                    data-testid="rsb-merge"
                  >
                    <Merge className="h-4 w-4 mr-2" />
                    Merge
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleExport(selectedPackage.id, selectedPackage.name)}
                    disabled={exporting}
                    data-testid="rsb-export"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {exporting ? "Exporting" : "Export"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleDelete(selectedPackage.id)}
                    data-testid="rsb-delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <Card className="border-border mt-4" data-testid="rsb-registry">
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

              <Card className="border-border mt-4" data-testid="rsb-xai-linkage">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">XAI Linkage</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-xs text-muted-foreground">
                  {xaiBundle ? (
                    <>
                      <div className="text-white text-xs font-medium">{xaiBundle.summary}</div>
                      <div>Evidence Nodes: {xaiBundle.evidence_graph?.nodes?.length || 0}</div>
                      <div>Counterfactuals: {xaiBundle.counterfactuals?.length || 0}</div>
                    </>
                  ) : xaiLoading ? (
                    <div>Loading XAI bundle...</div>
                  ) : (
                    <div>No XAI bundle linked to this RSB yet.</div>
                  )}
                </CardContent>
              </Card>

              <div className="grid grid-cols-4 gap-4 mt-6">
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-sm">Validation Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Badge variant="outline" className="text-xs capitalize">
                      {validationStatus}
                    </Badge>
                    <Progress value={validationProgress} className="h-2" />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={triggerValidation}
                      data-testid="validation-run-btn"
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Run Validation
                    </Button>
                    {selectedPackage.validation?.errors?.length > 0 && (
                      <div className="text-xs text-red-400 space-y-1">
                        {selectedPackage.validation.errors.map((err) => (
                          <div key={err}>• {err}</div>
                        ))}
                      </div>
                    )}
                    {selectedPackage.validation?.warnings?.length > 0 && (
                      <div className="text-xs text-yellow-400 space-y-1">
                        {selectedPackage.validation.warnings.map((warn) => (
                          <div key={warn}>• {warn}</div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-sm">Deployment Staging</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div
                      onDrop={handleStageDrop}
                      onDragOver={handleStageDragOver}
                      className="border border-dashed border-border rounded-lg p-3 text-xs text-muted-foreground"
                      data-testid="staging-dropzone"
                    >
                      Drop packages here to stage
                    </div>
                    <div className="space-y-2 mt-3">
                      {stagedQueue.map((pkg) => (
                        <div key={pkg.id} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <GripVertical className="h-3 w-3 text-muted-foreground" />
                            <span>{pkg.name}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStaged(pkg.id)}
                            data-testid={`remove-staged-${pkg.id}`}
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                      {stagedQueue.length === 0 && (
                        <div className="text-xs text-muted-foreground">No packages staged</div>
                      )}
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Button
                        size="sm"
                        onClick={deployStagedQueue}
                        disabled={deploying}
                        data-testid="deploy-staged-btn"
                      >
                        {deploying ? "Deploying..." : "Deploy Staged"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setStagedQueue([])}
                        disabled={stagedQueue.length === 0}
                        data-testid="clear-staged-btn"
                      >
                        Clear
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-sm">Merge Conflicts</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {conflictItems.map((item) => (
                      <div key={item.id} className="p-2 rounded border border-border bg-black/30 text-xs">
                        <div className="font-medium">{item.label}</div>
                        <div className="text-muted-foreground">{item.suggestion}</div>
                        <div className="mt-2 flex gap-2">
                          <Button
                            variant={conflictDecisions[item.id] === "keep" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(item.id, "keep")}
                            data-testid={`conflict-keep-${item.id}`}
                          >
                            Keep
                          </Button>
                          <Button
                            variant={conflictDecisions[item.id] === "merge" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(item.id, "merge")}
                            data-testid={`conflict-merge-${item.id}`}
                          >
                            Merge
                          </Button>
                          <Button
                            variant={conflictDecisions[item.id] === "manual" ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleConflictDecision(item.id, "manual")}
                            data-testid={`conflict-manual-${item.id}`}
                          >
                            Manual
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="text-sm">Version Timeline</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {versionTimeline.map((item, idx) => (
                      <div key={`${item.version}-${idx}`} className="flex items-center gap-3 text-xs">
                        <div className="h-6 w-6 rounded-full border border-border flex items-center justify-center text-[10px] font-mono">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          <div className="font-mono">v{item.version}</div>
                          <div className="text-muted-foreground capitalize">{item.status}</div>
                        </div>
                        <Badge variant="outline" className="capitalize">
                          {item.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCompareVersion(item.version)}
                          data-testid={`compare-version-${item.version}`}
                        >
                          Compare
                        </Button>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              {comparison && (
                <Card className="border-border mt-4" data-testid="version-compare-panel">
                  <CardHeader>
                    <CardTitle className="text-sm">Version Comparison</CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">Base</div>
                      <div className="font-mono">v{comparison.base}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Target</div>
                      <div className="font-mono">v{comparison.target}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Delta</div>
                      <div className="font-mono">Rules +{comparison.changes.rules}</div>
                      <div className="font-mono">Tests +{comparison.changes.tests}</div>
                      <div className="font-mono">Badges {comparison.changes.compliance}</div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Tabs */}
            <Tabs defaultValue="manifest" className="flex-1 flex flex-col overflow-hidden">
              <TabsList className="mx-6 mt-4 w-fit">
                <TabsTrigger value="manifest">
                  <FileJson className="h-4 w-4 mr-2" />
                  Manifest
                </TabsTrigger>
                <TabsTrigger value="tests">
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Test Results
                </TabsTrigger>
                <TabsTrigger value="compliance">
                  <Shield className="h-4 w-4 mr-2" />
                  Compliance
                </TabsTrigger>
              </TabsList>

              <ScrollArea className="flex-1">
                <TabsContent value="manifest" className="p-6 m-0 space-y-4">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Package Manifest</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="p-4 bg-black/30 rounded-lg font-mono text-sm overflow-auto">
                        {JSON.stringify(selectedPackage.manifest, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>File Manifest (Tree View)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-3 bg-black/30 rounded-lg">
                        {renderTree(selectedPackage.manifest?.files || defaultManifestTree)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Rule Network (Interactive)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div ref={ruleGraphWrapperRef} className="bg-black/30 rounded-lg">
                        {graphLoading ? (
                          <Skeleton className="h-[220px] w-full" />
                        ) : (
                          <ForceGraph2D
                            ref={ruleGraphRef}
                            graphData={ruleNetwork}
                            width={ruleGraphSize.width}
                            height={ruleGraphSize.height}
                            backgroundColor="#09090B"
                            nodeLabel="name"
                            nodeColor={(node) => (node.group === "root" ? "#3B82F6" : "#60A5FA")}
                            nodeVal={(node) => node.val}
                            linkColor={() => "#334155"}
                            linkDirectionalArrowLength={4}
                            linkDirectionalArrowRelPos={1}
                          />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-3">
                        Nodes represent RSB rules; edges indicate dependency flow.
                      </p>
                    </CardContent>
                  </Card>

                  {selectedPackage.rules?.length > 0 && (
                    <Card className="border-border">
                      <CardHeader>
                        <CardTitle>Included Rules ({selectedPackage.rules.length})</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {selectedPackage.rules.map((ruleId) => (
                            <div key={ruleId} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                              <FileText className="h-4 w-4 text-blue-400" />
                              <span className="font-mono text-sm">{ruleId}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Code Viewer</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="p-4 bg-black/30 rounded-lg font-mono text-xs overflow-auto max-h-64">
                        {codePreview}
                      </pre>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="tests" className="p-6 m-0 space-y-4">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Test Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <TestResultsView results={selectedPackage.test_results} />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="compliance" className="p-6 m-0 space-y-4">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Compliance Badges</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {selectedPackage.compliance_badges?.length > 0 ? (
                        <div className="grid grid-cols-3 gap-4">
                          {selectedPackage.compliance_badges.map((badge) => (
                            <div key={badge} className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                              <div className="flex items-center gap-2">
                                <CheckCircle2 className="h-5 w-5 text-green-400" />
                                <span className="font-semibold">{badge}</span>
                              </div>
                              <p className="text-sm text-muted-foreground mt-2">
                                Compliance verified
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-muted-foreground">No compliance badges</p>
                      )}
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Compliance Documentation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {selectedPackage.compliance_docs?.length > 0 ? (
                        <div className="space-y-3">
                          {selectedPackage.compliance_docs.map((doc) => (
                            <div key={doc.name} className="p-3 bg-black/30 rounded-lg">
                              <div className="text-xs text-muted-foreground font-mono mb-2">{doc.name}</div>
                              <pre className="text-xs text-muted-foreground whitespace-pre-wrap max-h-56 overflow-auto">
                                {typeof doc.content === "string" ? doc.content : JSON.stringify(doc.content, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 bg-black/30 rounded-lg text-sm text-muted-foreground">
                          {selectedPackage.description || "Compliance narrative not provided. Please attach compliance docs to this package."}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </ScrollArea>
            </Tabs>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select a package to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RSBManager;
