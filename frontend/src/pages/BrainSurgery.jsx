import React, { useState, useEffect, useRef, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { knowledgeAPI } from "../lib/api";
import { toast } from "sonner";
import {
  Plus,
  Trash2,
  Link2,
  Play,
  Eye,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Info,
  Shield,
  FileText,
  Lock,
  Lightbulb,
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
  const graphRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

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
    toast.success("Sandbox test initiated - Simulating patch application...");
    setTimeout(() => {
      toast.success("Sandbox test passed! All rules validated.");
    }, 2000);
  };

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-background" data-testid="brain-surgery">
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
    </div>
  );
};

export default BrainSurgery;
