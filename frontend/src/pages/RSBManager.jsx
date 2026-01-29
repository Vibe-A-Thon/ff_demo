import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Progress } from "../components/ui/progress";
import { rsbAPI } from "../lib/api";
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
  Trash2,
  Shield,
  Clock,
  FileText,
  GitMerge,
} from "lucide-react";

const RSBManager = () => {
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importData, setImportData] = useState({
    name: "",
    version: "",
    description: "",
    manifest: {},
    rules: [],
    compliance_badges: [],
  });
  const [testRunning, setTestRunning] = useState(null);

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      const response = await rsbAPI.getAll();
      setPackages(response.data);
    } catch (error) {
      console.error("Failed to load packages:", error);
    }
  };

  const handleImport = async () => {
    if (!importData.name || !importData.version) {
      toast.error("Please fill in required fields");
      return;
    }
    try {
      const manifest = {
        rules: importData.rules?.length || 0,
        patterns: 5,
        compliance: importData.compliance_badges || [],
      };
      await rsbAPI.create({ ...importData, manifest });
      toast.success("RSB Package imported successfully!");
      setShowImportModal(false);
      setImportData({ name: "", version: "", description: "", manifest: {}, rules: [], compliance_badges: [] });
      loadPackages();
    } catch (error) {
      toast.error("Failed to import package");
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
    try {
      await rsbAPI.merge(packageId);
      loadPackages();
      toast.success("Package merged successfully!");
    } catch (error) {
      toast.error("Merge failed");
    }
  };

  const handleDelete = async (packageId) => {
    try {
      await rsbAPI.delete(packageId);
      loadPackages();
      if (selectedPackage?.id === packageId) {
        setSelectedPackage(null);
      }
      toast.success("Package deleted");
    } catch (error) {
      toast.error("Delete failed");
    }
  };

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

  return (
    <div className="h-full flex" data-testid="rsb-manager">
      {/* Package List */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">RSB Packages</h2>
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
                    data-testid="confirm-import-btn"
                    data-explain="Confirm import"
                    data-explain-title="Import validation"
                    data-explain-summary="Creates a staged package and records compliance checks for audit."
                    data-explain-rules="RSB-ING-05,COM-010"
                    data-explain-evidence="Package metadata,Checksum,Policy badges"
                  >
                    <Package className="h-4 w-4 mr-2" />
                    Import Package
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {packages.map((pkg) => (
              <div
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
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
                  {getStatusBadge(pkg.status)}
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
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold">{selectedPackage.name}</h1>
                  <p className="text-muted-foreground mt-1">{selectedPackage.description || "No description"}</p>
                  <div className="flex items-center gap-4 mt-4">
                    <span className="text-sm font-mono">Version: {selectedPackage.version}</span>
                    {getStatusBadge(selectedPackage.status)}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleRunTests(selectedPackage.id)}
                    disabled={testRunning === selectedPackage.id}
                    data-testid="run-tests-btn"
                    data-explain="Run RSB tests"
                    data-explain-title="Package test execution"
                    data-explain-summary="Runs unit, integration, and compliance checks to validate package readiness."
                    data-explain-rules="RSB-TEST-01,COM-014"
                    data-explain-evidence="Test results,Compliance status,Coverage"
                  >
                    <Play className={`h-4 w-4 mr-2 ${testRunning === selectedPackage.id ? 'animate-spin' : ''}`} />
                    Run Tests
                  </Button>
                  <Button
                    onClick={() => handleMerge(selectedPackage.id)}
                    disabled={selectedPackage.status !== "tested"}
                    data-testid="merge-btn"
                    data-explain="Merge package"
                    data-explain-title="Merge authorization"
                    data-explain-summary="Moves validated packages into the active ruleset after tests pass."
                    data-explain-rules="RSB-MERGE-02,COM-020"
                    data-explain-evidence="Passed tests,Change approvals,Audit log"
                  >
                    <Merge className="h-4 w-4 mr-2" />
                    Merge
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => handleDelete(selectedPackage.id)}
                    data-testid="delete-package-btn"
                    data-explain="Delete package"
                    data-explain-title="Deletion controls"
                    data-explain-summary="Removes a package and logs the action for compliance review."
                    data-explain-rules="RSB-DEL-01,COM-009"
                    data-explain-evidence="Requester role,Deletion intent,Audit record"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
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
                <TabsContent value="manifest" className="p-6 m-0">
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

                  <Card className="border-border mt-4">
                    <CardHeader>
                      <CardTitle>File Manifest (Tree View)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-3 bg-black/30 rounded-lg">
                        {renderTree(selectedPackage.manifest?.files || defaultManifestTree)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border mt-4">
                    <CardHeader>
                      <CardTitle>Rule Network (Preview)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {(selectedPackage.rules || ["R-ACCOUNT_TAKEOVER"]).map((ruleId) => (
                          <Badge key={ruleId} variant="outline" className="font-mono text-xs">
                            {ruleId}
                          </Badge>
                        ))}
                        <Badge variant="outline" className="text-xs">Risk-Scorer</Badge>
                        <Badge variant="outline" className="text-xs">Policy-Gate</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-3">
                        Nodes represent RSB rules; edges indicate dependency flow.
                      </p>
                    </CardContent>
                  </Card>

                  {selectedPackage.rules?.length > 0 && (
                    <Card className="border-border mt-4">
                      <CardHeader>
                        <CardTitle>Included Rules ({selectedPackage.rules.length})</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {selectedPackage.rules.map((ruleId, idx) => (
                            <div key={ruleId} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                              <FileText className="h-4 w-4 text-blue-400" />
                              <span className="font-mono text-sm">{ruleId}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>


                  <Card className="border-border mt-4">
                    <CardHeader>
                      <CardTitle>Code Viewer</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="p-4 bg-black/30 rounded-lg font-mono text-xs overflow-auto max-h-64">
{`def detect_rule(txs):
                <TabsContent value="tests" className="p-6 m-0">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle>Test Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      </pre>
                    </CardContent>
                  </Card>
                      <TestResultsView results={selectedPackage.test_results} />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="compliance" className="p-6 m-0">
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

                  <Card className="border-border mt-4">
                    <CardHeader>
                      <CardTitle>Compliance Documentation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 bg-black/30 rounded-lg text-sm text-muted-foreground">
                        {selectedPackage.description || "Compliance narrative not provided. Please attach compliance docs to this package."}
                      </div>
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
