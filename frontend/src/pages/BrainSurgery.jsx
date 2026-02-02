import React, { useState, useEffect, useRef, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Switch } from "../components/ui/switch";
import { Progress } from "../components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { knowledgeAPI } from "../lib/api";
import BrainMergePanel from "../components/BrainMergePanel";
import { toast } from "sonner";
import {
  Plus,
  Trash2,
  Link2,
  Play,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Shield,
  FileText,
  Lock,
  Lightbulb,
  AlertTriangle,
  GitMerge,
  Upload,
  Brain,
} from "lucide-react";

const nodeColors = {
  root: "#3B82F6",
  rule: "#3B82F6",
  pattern: "#A855F7",
  compliance: "#10B981",
  evidence: "#EAB308",
};

const BrainSurgery = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [graphLoading, setGraphLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [newNodeType, setNewNodeType] = useState("rule");
  const [newNodeName, setNewNodeName] = useState("");
  const [connectMode, setConnectMode] = useState(false);
  const [connectSource, setConnectSource] = useState(null);
  const [patchAssignments, setPatchAssignments] = useState({});
  const [sandboxStatus, setSandboxStatus] = useState("idle");
  const [sandboxLogs, setSandboxLogs] = useState([]);
  const [sandboxCases, setSandboxCases] = useState([
    { id: "case-01", name: "Velocity Regression", status: "queued" },
    { id: "case-02", name: "ATO Edge Cases", status: "queued" },
    { id: "case-03", name: "Geo Fence Drift", status: "queued" },
  ]);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [conflicts, setConflicts] = useState([
    {
      id: "conf-01",
      title: "Rule action changed",
      detail: "Existing: review → Patch: block",
      resolution: "keep-existing",
    },
    {
      id: "conf-02",
      title: "Threshold drift",
      detail: "Confidence 0.71 → 0.82",
      resolution: "accept-patch",
    },
  ]);
  const [hotSwapEnabled, setHotSwapEnabled] = useState(true);
  const [perfImpact, setPerfImpact] = useState(18);
  const [perfLatency, setPerfLatency] = useState(6);
  const [perfCpu, setPerfCpu] = useState(4);
  const graphRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [activeTab, setActiveTab] = useState("graph");

  const patches = [
    { id: "patch-ato-01", name: "ATO Patch v1.2", risk: "low", coverage: "+12%" },
    { id: "patch-vel-07", name: "Velocity Tune", risk: "medium", coverage: "+6%" },
    { id: "patch-geo-03", name: "Geo Fence", risk: "high", coverage: "+3%" },
  ];

  const patchDrilldowns = [
    {
      id: "drill-01",
      nodeId: "rule-velocity-01",
      patch: "Velocity Tune",
      status: "conflict",
      detail: "Threshold divergence detected",
    },
    {
      id: "drill-02",
      nodeId: "rule-ato-02",
      patch: "ATO Patch v1.2",
      status: "ready",
      detail: "Passes sandbox validation",
    },
  ];

  const agents = [
    { id: "agent-blue-01", name: "Blue Orchestrator" },
    { id: "agent-purple-02", name: "Purple Strategist" },
    { id: "agent-green-03", name: "Green Builder" },
  ];

  useEffect(() => {
    loadNodes();
    
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight - 120, // Account for toolbar
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  const loadNodes = async () => {
    setGraphLoading(true);
    try {
      const response = await knowledgeAPI.getNodes();
      const nodes = response.data;

      // Transform to graph format
      const graphNodes = nodes.map((n) => ({
        id: n.id,
        name: n.name,
        type: n.node_type,
        data: n.data,
        color: nodeColors[n.node_type] || "#71717A",
        size: n.node_type === "root" ? 20 : n.node_type === "evidence" ? 8 : 12,
      }));

      const graphLinks = [];
      nodes.forEach((n) => {
        (n.connections || []).forEach((targetId) => {
          graphLinks.push({
            source: n.id,
            target: targetId,
            color: "#F87171",
          });
        });
      });

      setGraphData({ nodes: graphNodes, links: graphLinks });
    } catch (error) {
      console.error("Failed to load nodes:", error);
    } finally {
      setGraphLoading(false);
    }
  };

  const handleNodeClick = useCallback((node) => {
    if (connectMode && connectSource) {
      // Connect nodes
      handleConnectNodes(connectSource.id, node.id);
      setConnectMode(false);
      setConnectSource(null);
    } else if (connectMode) {
      setConnectSource(node);
      toast.info("Now click on the target node to connect");
    } else {
      setSelectedNode(node);
    }
  }, [connectMode, connectSource]);

  const handleConnectNodes = async (sourceId, targetId) => {
    if (sourceId === targetId) {
      toast.error("Cannot connect node to itself");
      return;
    }
    try {
      await knowledgeAPI.connectNodes(sourceId, targetId);
      toast.success("Nodes connected!");
      loadNodes();
    } catch (error) {
      toast.error("Failed to connect nodes");
    }
  };

  const handleCreateNode = async () => {
    if (!newNodeName.trim()) {
      toast.error("Please enter a node name");
      return;
    }
    try {
      await knowledgeAPI.createNode({
        node_type: newNodeType,
        name: newNodeName,
        data: {},
        connections: [],
      });
      toast.success("Node created!");
      setNewNodeName("");
      loadNodes();
    } catch (error) {
      toast.error("Failed to create node");
    }
  };

  const handleDeleteNode = async (nodeId) => {
    try {
      await knowledgeAPI.deleteNode(nodeId);
      toast.success("Node deleted!");
      setSelectedNode(null);
      loadNodes();
    } catch (error) {
      toast.error("Failed to delete node");
    }
  };

  const handleZoom = (direction) => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(direction === "in" ? currentZoom * 1.3 : currentZoom / 1.3, 400);
    }
  };

  const handleCenterGraph = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
  };

  const runSandboxTest = () => {
    setSandboxStatus("running");
    setSandboxLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Sandbox booted. Running validation suite...`,
    ]);
    setSandboxCases((prev) => prev.map((item) => ({ ...item, status: "running" })));
    toast.success("Sandbox test initiated - Simulating patch application...");

    setTimeout(() => {
      setSandboxCases((prev) =>
        prev.map((item, index) => ({
          ...item,
          status: index === 2 ? "warning" : "passed",
        }))
      );
      setSandboxStatus("passed");
      setSandboxLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] All unit and integration tests completed.`,
      ]);
      toast.success("Sandbox test passed! All rules validated.");
    }, 1800);
  };

  const handlePatchDragStart = (patch) => (event) => {
    event.dataTransfer.setData("application/json", JSON.stringify(patch));
    event.dataTransfer.effectAllowed = "move";
  };

  const handleAgentDrop = (agentId) => (event) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData("application/json");
    if (!raw) return;
    const patch = JSON.parse(raw);
    setPatchAssignments((prev) => ({ ...prev, [agentId]: patch }));
    toast.success(`Assigned ${patch.name} to ${agents.find(a => a.id === agentId)?.name}`);
  };

  const handleAgentDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const handleMergeDeploy = () => {
    if (sandboxStatus !== "passed") {
      toast.error("Run sandbox validation before deploy.");
      return;
    }
    toast.success("Merge and Deploy started. Watching rollout...");
  };

  const handleResolveConflict = (conflictId, resolution) => {
    setConflicts((prev) =>
      prev.map((conflict) =>
        conflict.id === conflictId ? { ...conflict, resolution } : conflict
      )
    );
  };

  const handlePerfImpactChange = (value) => {
    const next = Number(value);
    setPerfImpact(next);
    setPerfLatency(Math.max(2, Math.round(next / 3)));
    setPerfCpu(Math.max(1, Math.round(next / 4)));
  };

  const getSafetyBadge = (risk) => {
    if (risk === "low") return { label: "SAFE TO MERGE", className: "status-success" };
    if (risk === "medium") return { label: "REQUIRES REVIEW", className: "status-warning" };
    return { label: "HIGH RISK PATCH", className: "status-error" };
  };

  const getSandboxBadge = (status) => {
    if (status === "passed") return { label: "PASSED", className: "status-success" };
    if (status === "warning") return { label: "WARN", className: "status-warning" };
    if (status === "running") return { label: "RUNNING", className: "status-warning" };
    return {
      label: "QUEUED",
      className: "bg-zinc-800 text-zinc-400 border border-zinc-700",
    };
  };

  const conflictNodeIds = new Set(
    graphData.nodes.filter((node) => node.type === "rule").slice(0, 2).map((node) => node.id)
  );

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-background" data-testid="brain-surgery">
      {/* Tab Header */}
      <div className="border-b border-border bg-card/50 px-4 py-2">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-transparent h-auto p-0 gap-4">
            <TabsTrigger 
              value="graph" 
              className="data-[state=active]:border-b-2 data-[state=active]:border-blue-500 rounded-none bg-transparent px-4 py-2"
            >
              <Brain className="h-4 w-4 mr-2" />
              Knowledge Graph
            </TabsTrigger>
            <TabsTrigger 
              value="import" 
              className="data-[state=active]:border-b-2 data-[state=active]:border-purple-500 rounded-none bg-transparent px-4 py-2"
            >
              <GitMerge className="h-4 w-4 mr-2" />
              Import &amp; Merge
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Knowledge Graph Tab */}
      {activeTab === "graph" && (
        <>
          {/* Floating Toolbar */}
      <div className="absolute top-20 left-72 right-4 z-10 flex items-center justify-between glass rounded-lg px-4 py-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Select value={newNodeType} onValueChange={setNewNodeType}>
              <SelectTrigger className="w-32" data-testid="node-type-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rule">Rule</SelectItem>
                <SelectItem value="pattern">Pattern</SelectItem>
                <SelectItem value="compliance">Compliance</SelectItem>
                <SelectItem value="evidence">Evidence</SelectItem>
              </SelectContent>
            </Select>
            <Input
              value={newNodeName}
              onChange={(e) => setNewNodeName(e.target.value)}
              placeholder="Node name..."
              className="w-48"
              data-testid="node-name-input"
            />
            <Button onClick={handleCreateNode} data-testid="create-node-btn">
              <Plus className="h-4 w-4 mr-2" />
              Add Node
            </Button>
          </div>

          <div className="h-6 w-px bg-border" />

          <Button
            variant={connectMode ? "destructive" : "outline"}
            onClick={() => {
              setConnectMode(!connectMode);
              setConnectSource(null);
            }}
            data-testid="connect-mode-btn"
          >
            <Link2 className="h-4 w-4 mr-2" />
            {connectMode ? "Cancel Connect" : "Connect Nodes"}
          </Button>

          <Button variant="outline" onClick={runSandboxTest} data-testid="sandbox-test-btn">
            <Play className="h-4 w-4 mr-2" />
            Sandbox Test
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => handleZoom("in")} data-testid="zoom-in-btn">
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => handleZoom("out")} data-testid="zoom-out-btn">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleCenterGraph} data-testid="center-graph-btn">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="flex-1 relative">
        {graphLoading && (
          <div className="absolute inset-0 z-10 bg-background/60 backdrop-blur-sm flex items-center justify-center">
            <div className="w-2/3 space-y-3">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-64" />
              <Skeleton className="h-6 w-1/3" />
            </div>
          </div>
        )}
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#09090B"
          nodeLabel={(node) => node.name}
          nodeColor={(node) => node.color}
          nodeVal={(node) => node.size}
          linkColor={(link) => link.color || "#F87171"}
          linkWidth={2}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px JetBrains Mono`;
            ctx.fillStyle = node.color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI);
            ctx.fill();

            // Draw label below node
            ctx.fillStyle = "#A1A1AA";
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.fillText(label, node.x, node.y + node.size + 4);

            // Draw ROOT badge for root nodes
            if (node.type === "root") {
              ctx.fillStyle = "#FAFAFA";
              ctx.fillRect(node.x - 20, node.y - 8, 40, 16);
              ctx.fillStyle = "#09090B";
              ctx.font = `bold ${10 / globalScale}px Manrope`;
              ctx.fillText("ROOT", node.x, node.y - 4);
            }

            if (conflictNodeIds.has(node.id)) {
              ctx.fillStyle = "#EF4444";
              ctx.beginPath();
              ctx.arc(node.x + node.size - 4, node.y - node.size + 4, 5, 0, 2 * Math.PI);
              ctx.fill();
            }
          }}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
        />

        {/* Legend */}
        <div className="absolute bottom-4 left-4 glass rounded-lg p-4">
          <h4 className="text-sm font-semibold mb-3">Node Types</h4>
          <div className="space-y-2">
            {Object.entries(nodeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs capitalize">{type}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 pt-2 text-xs text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              Conflict flagged
            </div>
          </div>
        </div>

        {/* Connect Mode Indicator */}
        {connectMode && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 glass rounded-lg px-4 py-2">
            <span className="text-sm text-yellow-400">
              {connectSource ? `Selected: ${connectSource.name}. Click target node.` : "Click source node to start connection"}
            </span>
          </div>
        )}
      </div>

      {/* Node Inspector Sheet */}
      <Sheet open={!!selectedNode} onOpenChange={(open) => !open && setSelectedNode(null)}>
        <SheetContent className="bg-card border-border" data-testid="node-inspector">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              {selectedNode?.type === "rule" && <Shield className="h-5 w-5 text-blue-400" />}
              {selectedNode?.type === "pattern" && <Lightbulb className="h-5 w-5 text-purple-400" />}
              {selectedNode?.type === "compliance" && <Lock className="h-5 w-5 text-green-400" />}
              {selectedNode?.type === "evidence" && <FileText className="h-5 w-5 text-yellow-400" />}
              {selectedNode?.name}
            </SheetTitle>
          </SheetHeader>

          <div className="mt-6 space-y-6">
            <div>
              <label className="text-sm text-muted-foreground">Type</label>
              <Badge className="mt-1 capitalize" style={{ backgroundColor: selectedNode?.color + "33", color: selectedNode?.color }}>
                {selectedNode?.type}
              </Badge>
            </div>

            <div>
              <label className="text-sm text-muted-foreground">ID</label>
              <p className="font-mono text-sm mt-1">{selectedNode?.id}</p>
            </div>

            {selectedNode?.type === "rule" && (
              <div>
                <label className="text-sm text-muted-foreground">Patch Drilldowns</label>
                <div className="mt-2 space-y-2">
                  {patchDrilldowns.map((item) => (
                    <div key={item.id} className="rounded-md border border-border bg-black/30 p-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium">{item.patch}</span>
                        <Badge variant="outline" className={`text-[10px] ${item.status === "conflict" ? "border-red-500/40 text-red-300" : "border-green-500/40 text-green-300"}`}>
                          {item.status}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{item.detail}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedNode?.type === "rule" && conflicts.length > 0 && (
              <div>
                <label className="text-sm text-muted-foreground">Live Conflict Preview</label>
                <div className="mt-2 space-y-2">
                  {conflicts.map((conflict) => (
                    <div key={conflict.id} className="rounded-md border border-border bg-black/30 p-2">
                      <div className="flex items-center gap-2 text-xs font-medium">
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                        {conflict.title}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">{conflict.detail}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedNode?.data && Object.keys(selectedNode.data).length > 0 && (
              <div>
                <label className="text-sm text-muted-foreground">Data</label>
                <pre className="mt-1 p-3 bg-black/30 rounded text-xs font-mono overflow-auto">
                  {JSON.stringify(selectedNode.data, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex gap-2 pt-4 border-t border-border">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setConnectMode(true);
                  setConnectSource(selectedNode);
                  setSelectedNode(null);
                  toast.info("Click on target node to connect");
                }}
              >
                <Link2 className="h-4 w-4 mr-2" />
                Connect
              </Button>
              <Button
                variant="destructive"
                onClick={() => selectedNode && handleDeleteNode(selectedNode.id)}
                data-testid="delete-node-btn"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* Brain Surgery Control Deck */}
      <div className="border-t border-border bg-zinc-900/70 px-6 py-4">
        <div className="grid grid-cols-4 gap-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-sm">Patch Library</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {patches.map((patch) => (
                <div
                  key={patch.id}
                  draggable
                  onDragStart={handlePatchDragStart(patch)}
                  className="p-3 rounded-lg border border-border bg-black/30 cursor-move hover:border-zinc-600"
                  data-testid={`patch-${patch.id}`}
                >
                  <div className="text-sm font-medium">{patch.name}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs capitalize">
                      {patch.risk} risk
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      Coverage {patch.coverage}
                    </Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-sm">Agent Mapping</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onDrop={handleAgentDrop(agent.id)}
                  onDragOver={handleAgentDragOver}
                  className="p-3 rounded-lg border border-dashed border-border bg-black/20"
                  data-testid={`agent-drop-${agent.id}`}
                >
                  <div className="text-xs text-muted-foreground">{agent.name}</div>
                  <div className="text-sm font-medium mt-1">
                    {patchAssignments[agent.id]?.name || "Drop patch here"}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-sm">Sandbox & Safety</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Sandbox Status</span>
                <Badge variant="outline" className="text-xs capitalize">
                  {sandboxStatus}
                </Badge>
              </div>
              <Button variant="outline" onClick={runSandboxTest} data-testid="sandbox-run-btn">
                <Play className="h-4 w-4 mr-2" />
                Run Sandbox
              </Button>
              <div className="space-y-2">
                {patches.map((patch) => {
                  const badge = getSafetyBadge(patch.risk);
                  return (
                    <div key={patch.id} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{patch.name}</span>
                      <Badge className={badge.className}>{badge.label}</Badge>
                    </div>
                  );
                })}
              </div>
              <div className="space-y-2" data-testid="sandbox-cases">
                {sandboxCases.map((testCase) => {
                  const badge = getSandboxBadge(testCase.status);
                  return (
                    <div key={testCase.id} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{testCase.name}</span>
                      <Badge className={badge.className}>{badge.label}</Badge>
                    </div>
                  );
                })}
              </div>
              <div className="rounded-md border border-border bg-black/30 p-2 text-xs font-mono h-24 overflow-auto" data-testid="sandbox-log">
                {sandboxLogs.length === 0 ? (
                  <div className="text-muted-foreground">Sandbox logs will appear here.</div>
                ) : (
                  sandboxLogs.map((log, index) => (
                    <div key={`${log}-${index}`} className="text-muted-foreground">
                      {log}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-sm">Deployment Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Hot-Swap</span>
                <Switch checked={hotSwapEnabled} onCheckedChange={setHotSwapEnabled} data-testid="hotswap-toggle" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Rollback Window</span>
                <Badge variant="outline" className="text-xs">15 min</Badge>
              </div>
              <div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Performance Impact</span>
                  <span>{perfImpact}%</span>
                </div>
                <Progress value={perfImpact} className="h-2" />
                <Input
                  type="range"
                  min="5"
                  max="45"
                  step="1"
                  value={perfImpact}
                  onChange={(e) => handlePerfImpactChange(e.target.value)}
                  className="mt-2"
                  data-testid="perf-impact-slider"
                />
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Latency Δ</span>
                    <span>+{perfLatency}ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>CPU Δ</span>
                    <span>+{perfCpu}%</span>
                  </div>
                </div>
              </div>
              <Button onClick={handleMergeDeploy} data-testid="merge-deploy-btn">
                <Shield className="h-4 w-4 mr-2" />
                Merge & Deploy
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="outline" onClick={() => setConflictOpen(true)} data-testid="conflict-resolve-btn">
                  <FileText className="h-4 w-4 mr-2" />
                  Resolve Conflicts
                </Button>
                <Button variant="ghost" size="icon" data-testid="rollback-btn">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={conflictOpen} onOpenChange={setConflictOpen}>
        <DialogContent className="bg-card border-border" data-testid="conflict-dialog">
          <DialogHeader>
            <DialogTitle>Merge Conflict Resolution</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {conflicts.map((conflict) => (
              <div key={conflict.id} className="rounded-lg border border-border bg-black/30 p-3">
                <div className="text-sm font-medium">{conflict.title}</div>
                <div className="text-xs text-muted-foreground mt-1">{conflict.detail}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant={conflict.resolution === "keep-existing" ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleResolveConflict(conflict.id, "keep-existing")}
                    data-testid={`conflict-keep-${conflict.id}`}
                  >
                    Keep Existing
                  </Button>
                  <Button
                    variant={conflict.resolution === "accept-patch" ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleResolveConflict(conflict.id, "accept-patch")}
                    data-testid={`conflict-accept-${conflict.id}`}
                  >
                    Accept Patch
                  </Button>
                  <Button
                    variant={conflict.resolution === "custom" ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleResolveConflict(conflict.id, "custom")}
                    data-testid={`conflict-custom-${conflict.id}`}
                  >
                    Custom Merge
                  </Button>
                </div>
              </div>
            ))}
            <Button onClick={() => setConflictOpen(false)} data-testid="conflict-save-btn">
              Apply Resolutions
            </Button>
          </div>
        </DialogContent>
      </Dialog>
        </>
      )}

      {/* Import & Merge Tab */}
      {activeTab === "import" && (
        <div className="flex-1 p-4 overflow-auto">
          <BrainMergePanel 
            currentBrain={graphData}
            onMergeComplete={(mergedGraph, packageData) => {
              // Update the graph data with merged result
              setGraphData(mergedGraph);
              loadNodes(); // Refresh from backend
              setActiveTab("graph"); // Switch back to graph view
            }}
          />
        </div>
      )}
    </div>
  );
};

export default BrainSurgery;
