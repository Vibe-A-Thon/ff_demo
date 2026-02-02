/**
 * BrainMergePanel - 3-Pane Knowledge Merge Visualization
 * 
 * Provides a visual interface for merging imported packages (PEP, APMC, RSB, BRC)
 * into the current knowledge base.
 * 
 * Layout:
 * - Left Pane: Current Brain (Blue nodes)
 * - Middle Pane: Incoming Package (Green nodes)
 * - Right Pane: Merged Result Preview
 * 
 * Supports both Merge (additive) and Patch (replace) operations.
 */

import React, { useState, useRef, useCallback, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { ScrollArea } from "./ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog";
import { toast } from "sonner";
import {
  Upload,
  Download,
  GitMerge,
  GitPullRequest,
  Brain,
  Package,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Play,
  RotateCcw,
  Eye,
  FileJson,
  Sparkles,
} from "lucide-react";

// Node color scheme
const NODE_COLORS = {
  current: "#3B82F6",    // Blue - Current knowledge
  incoming: "#22C55E",   // Green - Incoming patch
  conflict: "#EF4444",   // Red - Conflicts
  merged: "#A855F7",     // Purple - Merged result
  unchanged: "#6B7280",  // Gray - Unchanged
};

// Package types
const PACKAGE_TYPES = {
  pep: { name: "PEP", color: "#F59E0B", icon: Package, description: "Portable Evolution Pack" },
  apmc: { name: "APMC", color: "#8B5CF6", icon: Brain, description: "Agent Pattern Memory Capsule" },
  rsb: { name: "RSB", color: "#10B981", icon: FileJson, description: "Rule Suite Box" },
  brc: { name: "BRC", color: "#EC4899", icon: Sparkles, description: "Brain Capsule" },
};

// Merge operation types
const MERGE_OPERATIONS = {
  MERGE: "merge",   // Additive - combine both
  PATCH: "patch",   // Replace - incoming overwrites
};

// Single graph pane component
const GraphPane = ({ title, data, color, icon: Icon, onNodeClick, isInteractive = false }) => {
  const graphRef = useRef();

  const handleNodeClick = useCallback((node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  }, [onNodeClick]);

  return (
    <Card className="h-full bg-card/50 border-border/50">
      <CardHeader className="py-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          {Icon && <Icon className="h-4 w-4" style={{ color }} />}
          <span>{title}</span>
          <Badge variant="outline" className="ml-auto text-xs">
            {data.nodes.length} nodes
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 h-[calc(100%-60px)]">
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          nodeColor={(node) => node.color || color}
          nodeLabel={(node) => `${node.name || node.id}\n${node.type || "unknown"}`}
          linkColor={() => "#ffffff20"}
          linkWidth={1}
          nodeRelSize={6}
          backgroundColor="transparent"
          onNodeClick={handleNodeClick}
          enableNodeDrag={isInteractive}
          enableZoomInteraction={true}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name || node.id;
            const fontSize = 10 / globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;
            
            // Draw node
            ctx.beginPath();
            ctx.arc(node.x || 0, node.y || 0, node.size || 5, 0, 2 * Math.PI);
            ctx.fillStyle = node.color || color;
            ctx.fill();
            
            // Draw border for selected/conflict nodes
            if (node.isConflict) {
              ctx.strokeStyle = NODE_COLORS.conflict;
              ctx.lineWidth = 2 / globalScale;
              ctx.stroke();
            }
            
            // Draw label
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.fillStyle = "#ffffff80";
            ctx.fillText(label, node.x || 0, (node.y || 0) + (node.size || 5) + 2);
          }}
        />
      </CardContent>
    </Card>
  );
};

// Main BrainMergePanel component
const BrainMergePanel = ({ 
  onMergeComplete,
  currentBrain = { nodes: [], links: [] },
}) => {
  const [packageFile, setPackageFile] = useState(null);
  const [packageType, setPackageType] = useState(null);
  const [packageData, setPackageData] = useState(null);
  const [incomingGraph, setIncomingGraph] = useState({ nodes: [], links: [] });
  const [mergedGraph, setMergedGraph] = useState({ nodes: [], links: [] });
  const [conflicts, setConflicts] = useState([]);
  const [mergeOperation, setMergeOperation] = useState(MERGE_OPERATIONS.MERGE);
  const [merging, setMerging] = useState(false);
  const [mergeProgress, setMergeProgress] = useState(0);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  
  const fileInputRef = useRef();

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Detect package type from extension
    const ext = file.name.split('.').pop().toLowerCase();
    if (!PACKAGE_TYPES[ext]) {
      toast.error("Unsupported file type", {
        description: "Please upload a .pep, .apmc, .rsb, or .brc file",
      });
      return;
    }

    setPackageFile(file);
    setPackageType(ext);

    // Parse the package (simulated for demo)
    try {
      const content = await parsePackageFile(file, ext);
      setPackageData(content);
      
      // Convert to graph format
      const graph = convertToGraph(content, ext);
      setIncomingGraph(graph);
      
      // Detect conflicts
      const detectedConflicts = detectConflicts(currentBrain, graph);
      setConflicts(detectedConflicts);
      
      // Generate initial merge preview
      generateMergePreview(currentBrain, graph, detectedConflicts, MERGE_OPERATIONS.MERGE);
      
      toast.success(`Package loaded: ${file.name}`, {
        description: `${graph.nodes.length} nodes, ${detectedConflicts.length} conflicts detected`,
      });
    } catch (error) {
      toast.error("Failed to parse package", { description: error.message });
    }
  };

  // Parse package file
  const parsePackageFile = async (file, type) => {
    // In production, this would use JSZip to extract and parse
    // For demo, return mock data
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          manifest: {
            package_id: "pkg-" + Date.now(),
            package_type: type,
            name: file.name.replace(`.${type}`, ""),
          },
          contents: generateMockContents(type),
        });
      }, 500);
    });
  };

  // Generate mock contents based on package type
  const generateMockContents = (type) => {
    const mockItems = {
      pep: [
        { id: "mem-001", name: "ATO Pattern V2", type: "memory", collection: "patterns" },
        { id: "mem-002", name: "Velocity Rule Update", type: "memory", collection: "rules" },
        { id: "evo-001", name: "Learning Event 12", type: "evolution" },
      ],
      apmc: [
        { id: "apm-001", name: "Fraud Vector 47", type: "pattern" },
        { id: "apm-002", name: "Defense Signature 12", type: "pattern" },
      ],
      rsb: [
        { id: "rul-001", name: "VEL-099", type: "rule", code: "class VelocityCheck:..." },
        { id: "rul-002", name: "ATO-108", type: "rule", code: "def detect_ato(tx):..." },
        { id: "rul-003", name: "GEO-045", type: "rule", code: "class GeoFence:..." },
      ],
      brc: [
        { id: "nod-001", name: "Root Brain Node", type: "core" },
        { id: "nod-002", name: "Pattern Engine", type: "module" },
        { id: "nod-003", name: "Rule Executor", type: "module" },
      ],
    };
    return mockItems[type] || [];
  };

  // Convert package contents to graph format
  const convertToGraph = (content, type) => {
    const nodes = content.contents.map((item, idx) => ({
      id: item.id,
      name: item.name,
      type: item.type,
      color: NODE_COLORS.incoming,
      size: item.type === "core" ? 12 : 8,
      data: item,
    }));

    // Create some links between nodes
    const links = [];
    for (let i = 1; i < nodes.length; i++) {
      links.push({
        source: nodes[0].id,
        target: nodes[i].id,
      });
    }

    return { nodes, links };
  };

  // Detect conflicts between current and incoming graphs
  const detectConflicts = (current, incoming) => {
    const conflicts = [];
    const currentIds = new Set(current.nodes.map(n => n.id));
    
    incoming.nodes.forEach(node => {
      // Check for ID collision
      if (currentIds.has(node.id)) {
        conflicts.push({
          id: `conf-${node.id}`,
          type: "id_collision",
          nodeId: node.id,
          nodeName: node.name,
          resolution: null,
        });
      }
      
      // Check for name similarity (simulated)
      const similarNode = current.nodes.find(n => 
        n.name?.toLowerCase() === node.name?.toLowerCase()
      );
      if (similarNode && similarNode.id !== node.id) {
        conflicts.push({
          id: `conf-name-${node.id}`,
          type: "name_similarity",
          nodeId: node.id,
          nodeName: node.name,
          existingNodeId: similarNode.id,
          resolution: null,
        });
      }
    });

    return conflicts;
  };

  // Generate merge preview
  const generateMergePreview = (current, incoming, conflicts, operation) => {
    let merged = { nodes: [], links: [] };

    if (operation === MERGE_OPERATIONS.MERGE) {
      // Additive merge - include all nodes
      const existingIds = new Set(current.nodes.map(n => n.id));
      
      // Add current nodes (blue)
      merged.nodes = current.nodes.map(n => ({
        ...n,
        color: NODE_COLORS.current,
      }));
      
      // Add incoming nodes that don't conflict (green)
      incoming.nodes.forEach(n => {
        const hasConflict = conflicts.some(c => c.nodeId === n.id);
        if (!existingIds.has(n.id) && !hasConflict) {
          merged.nodes.push({
            ...n,
            color: NODE_COLORS.incoming,
          });
        } else if (hasConflict) {
          merged.nodes.push({
            ...n,
            color: NODE_COLORS.conflict,
            isConflict: true,
          });
        }
      });
      
      // Combine links
      merged.links = [...current.links, ...incoming.links];
      
    } else {
      // Patch - incoming replaces conflicting nodes
      const incomingIds = new Set(incoming.nodes.map(n => n.id));
      
      // Add current nodes not in incoming (blue)
      merged.nodes = current.nodes
        .filter(n => !incomingIds.has(n.id))
        .map(n => ({
          ...n,
          color: NODE_COLORS.current,
        }));
      
      // Add all incoming nodes (green/purple for replaced)
      incoming.nodes.forEach(n => {
        merged.nodes.push({
          ...n,
          color: conflicts.some(c => c.nodeId === n.id) ? NODE_COLORS.merged : NODE_COLORS.incoming,
        });
      });
      
      merged.links = [...current.links.filter(l => 
        !incomingIds.has(l.source) && !incomingIds.has(l.target)
      ), ...incoming.links];
    }

    setMergedGraph(merged);
  };

  // Handle operation change
  const handleOperationChange = (operation) => {
    setMergeOperation(operation);
    generateMergePreview(currentBrain, incomingGraph, conflicts, operation);
  };

  // Execute the merge
  const executeMerge = async () => {
    setMerging(true);
    setMergeProgress(0);

    try {
      // Simulate merge process with progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(r => setTimeout(r, 200));
        setMergeProgress(i);
      }

      toast.success("Knowledge merge complete!", {
        description: `${mergedGraph.nodes.length} nodes in final brain`,
      });

      if (onMergeComplete) {
        onMergeComplete(mergedGraph, packageData);
      }

      // Reset state
      setPackageFile(null);
      setPackageData(null);
      setIncomingGraph({ nodes: [], links: [] });
      setMergedGraph({ nodes: [], links: [] });
      setConflicts([]);
      setConfirmDialogOpen(false);
      
    } catch (error) {
      toast.error("Merge failed", { description: error.message });
    } finally {
      setMerging(false);
      setMergeProgress(0);
    }
  };

  // Resolve a conflict
  const resolveConflict = (conflictId, resolution) => {
    setConflicts(prev => prev.map(c => 
      c.id === conflictId ? { ...c, resolution } : c
    ));
    
    // Regenerate preview
    const updatedConflicts = conflicts.map(c => 
      c.id === conflictId ? { ...c, resolution } : c
    );
    generateMergePreview(currentBrain, incomingGraph, updatedConflicts, mergeOperation);
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/20">
            <GitMerge className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h2 className="font-semibold">Knowledge Merge</h2>
            <p className="text-xs text-muted-foreground">
              Import and merge brain packages
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Package type selector */}
          {packageFile && packageType && (
            <Badge 
              variant="outline"
              style={{ 
                borderColor: PACKAGE_TYPES[packageType].color,
                color: PACKAGE_TYPES[packageType].color,
              }}
            >
              {PACKAGE_TYPES[packageType].name}
            </Badge>
          )}
          
          {/* Import button */}
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-4 w-4 mr-2" />
            Import Package
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pep,.apmc,.rsb,.brc"
            className="hidden"
            onChange={handleFileUpload}
          />
          
          {/* Operation toggle */}
          {packageData && (
            <>
              <div className="flex rounded-lg border border-border overflow-hidden">
                <Button
                  variant={mergeOperation === MERGE_OPERATIONS.MERGE ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleOperationChange(MERGE_OPERATIONS.MERGE)}
                  className="rounded-none"
                >
                  <GitMerge className="h-4 w-4 mr-1" />
                  Merge
                </Button>
                <Button
                  variant={mergeOperation === MERGE_OPERATIONS.PATCH ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleOperationChange(MERGE_OPERATIONS.PATCH)}
                  className="rounded-none"
                >
                  <GitPullRequest className="h-4 w-4 mr-1" />
                  Patch
                </Button>
              </div>
              
              <Button
                onClick={() => setConfirmDialogOpen(true)}
                disabled={merging}
                className="bg-purple-600 hover:bg-purple-700"
              >
                <Play className="h-4 w-4 mr-2" />
                Execute {mergeOperation === MERGE_OPERATIONS.MERGE ? "Merge" : "Patch"}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* 3-Pane View */}
      <div className="flex-1 grid grid-cols-3 gap-4">
        {/* Left: Current Brain */}
        <GraphPane
          title="Current Brain"
          data={currentBrain}
          color={NODE_COLORS.current}
          icon={Brain}
        />

        {/* Middle: Incoming Package */}
        <GraphPane
          title={packageData ? `Incoming: ${packageData.manifest?.name}` : "Incoming Package"}
          data={incomingGraph}
          color={NODE_COLORS.incoming}
          icon={Package}
        />

        {/* Right: Merged Result */}
        <GraphPane
          title="Merged Result"
          data={mergedGraph}
          color={NODE_COLORS.merged}
          icon={GitMerge}
        />
      </div>

      {/* Conflicts Panel */}
      {conflicts.length > 0 && (
        <Card className="bg-red-500/10 border-red-500/20">
          <CardHeader className="py-3">
            <CardTitle className="flex items-center gap-2 text-sm text-red-400">
              <AlertTriangle className="h-4 w-4" />
              {conflicts.length} Conflict{conflicts.length > 1 ? "s" : ""} Detected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="max-h-32">
              <div className="space-y-2">
                {conflicts.map((conflict) => (
                  <div 
                    key={conflict.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-black/20"
                  >
                    <div>
                      <p className="text-sm font-medium">{conflict.nodeName}</p>
                      <p className="text-xs text-muted-foreground capitalize">
                        {conflict.type.replace("_", " ")}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant={conflict.resolution === "keep" ? "default" : "outline"}
                        onClick={() => resolveConflict(conflict.id, "keep")}
                      >
                        Keep Current
                      </Button>
                      <Button
                        size="sm"
                        variant={conflict.resolution === "replace" ? "default" : "outline"}
                        onClick={() => resolveConflict(conflict.id, "replace")}
                      >
                        Use Incoming
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS.current }} />
          <span>Current</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS.incoming }} />
          <span>Incoming</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS.merged }} />
          <span>Merged</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: NODE_COLORS.conflict }} />
          <span>Conflict</span>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitMerge className="h-5 w-5 text-purple-400" />
              Confirm {mergeOperation === MERGE_OPERATIONS.MERGE ? "Merge" : "Patch"}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {merging ? (
              <div className="space-y-3">
                <p className="text-sm text-center text-muted-foreground">
                  Merging knowledge...
                </p>
                <Progress value={mergeProgress} className="h-2" />
                <p className="text-xs text-center text-muted-foreground">
                  {mergeProgress}%
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                    <p className="text-2xl font-bold text-blue-400">
                      {currentBrain.nodes.length}
                    </p>
                    <p className="text-xs text-muted-foreground">Current</p>
                  </div>
                  <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <p className="text-2xl font-bold text-green-400">
                      {incomingGraph.nodes.length}
                    </p>
                    <p className="text-xs text-muted-foreground">Incoming</p>
                  </div>
                  <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <p className="text-2xl font-bold text-purple-400">
                      {mergedGraph.nodes.length}
                    </p>
                    <p className="text-xs text-muted-foreground">Result</p>
                  </div>
                </div>
                
                {conflicts.length > 0 && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <p className="text-sm text-amber-400 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      {conflicts.filter(c => !c.resolution).length} unresolved conflicts
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setConfirmDialogOpen(false)}
              disabled={merging}
            >
              Cancel
            </Button>
            <Button 
              onClick={executeMerge}
              disabled={merging}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {merging ? "Merging..." : `Confirm ${mergeOperation === MERGE_OPERATIONS.MERGE ? "Merge" : "Patch"}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BrainMergePanel;
export { NODE_COLORS, PACKAGE_TYPES, MERGE_OPERATIONS };
