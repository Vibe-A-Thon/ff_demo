import React, { useState, useCallback} from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
import { amcAPI } from "../lib/api";
import { toast } from "sonner";
import {
  Upload,
  FileArchive,
  Shield,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  FileText,
  FileJson,
  FolderOpen,
  Folder,
  Users,
  Brain,
  Activity,
  Eye,
  Download,
} from "lucide-react";

/**
 * AMC Explorer - File viewer for .amc packages
 * 
 * Features:
 * - Drag & drop AMC file upload
 * - Directory tree visualization
 * - JSON/Markdown content rendering
 * - Team Evolution Summary card
 * - Safety Scan Badge
 */
const AMCExplorer = () => {
  const [amcFile, setAmcFile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedPaths, setExpandedPaths] = useState(new Set(["agents", "team"]));
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Handle file drop
  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith(".amc") || file.name.endsWith(".zip")) {
        await processAmcFile(file);
      } else {
        toast.error("Please drop an .amc file");
      }
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      await processAmcFile(file);
    }
  };

  const processAmcFile = async (file) => {
    setLoading(true);
    setAmcFile(file);
    setValidation(null);
    setPreview(null);
    setSelectedFile(null);
    setFileContent(null);

    try {
      // Validate the AMC
      const formData = new FormData();
      formData.append("file", file);
      
      const validationResult = await amcAPI.validate(formData);
      setValidation(validationResult.data);

      // Get preview
      const formData2 = new FormData();
      formData2.append("file", file);
      const previewResult = await amcAPI.preview(formData2);
      setPreview(previewResult.data);

      toast.success("AMC file loaded successfully");
    } catch (err) {
      toast.error("Failed to load AMC file: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const togglePath = (path) => {
    const newExpanded = new Set(expandedPaths);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedPaths(newExpanded);
  };

  const selectFile = (path, content) => {
    setSelectedFile(path);
    setFileContent(content);
  };

  // Build file tree from preview data
  const buildFileTree = () => {
    if (!preview?.import?.manifest) return null;
    
    const manifest = preview.import.manifest;
    const agents = manifest.agents || [];
    
    return {
      name: "root",
      children: [
        {
          name: "manifest.json",
          type: "file",
          content: manifest,
          icon: FileJson,
        },
        {
          name: "team",
          type: "folder",
          children: [
            {
              name: "team_profile.json",
              type: "file",
              content: {
                team_id: manifest.team_id,
                team_name: manifest.team_name,
                version: manifest.team_version,
              },
              icon: FileJson,
            },
          ],
        },
        {
          name: "agents",
          type: "folder",
          children: agents.map((agent) => ({
            name: agent.agent_id,
            type: "folder",
            children: [
              {
                name: "agent_profile.json",
                type: "file",
                content: agent,
                icon: FileJson,
              },
              {
                name: "memory",
                type: "folder",
                children: [
                  { name: "semantic_memory.jsonl", type: "file", icon: FileText },
                  { name: "episodic_memory.jsonl", type: "file", icon: FileText },
                  { name: "procedural_memory.json", type: "file", icon: FileJson },
                  { name: "distilled_lessons.md", type: "file", icon: FileText },
                ],
              },
            ],
          })),
        },
        {
          name: "contracts",
          type: "folder",
          children: [
            { name: "tool_registry.yaml", type: "file", icon: FileText },
            { name: "prompt_manifest.yaml", type: "file", icon: FileText },
          ],
        },
        {
          name: "pack_hashes.json",
          type: "file",
          icon: FileJson,
        },
      ],
    };
  };

  const renderTreeNode = (node, path = "", depth = 0) => {
    const currentPath = path ? `${path}/${node.name}` : node.name;
    const isExpanded = expandedPaths.has(currentPath);
    const isSelected = selectedFile === currentPath;
    const Icon = node.icon || (node.type === "folder" ? (isExpanded ? FolderOpen : Folder) : FileText);

    if (node.type === "folder" && node.children) {
      return (
        <div key={currentPath}>
          <div
            className={`flex items-center gap-1 py-1 px-2 rounded cursor-pointer hover:bg-accent/50 ${
              isSelected ? "bg-accent" : ""
            }`}
            style={{ paddingLeft: `${depth * 16 + 8}px` }}
            onClick={() => togglePath(currentPath)}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <Icon className="h-4 w-4 text-blue-400" />
            <span className="text-sm">{node.name}</span>
          </div>
          {isExpanded && (
            <div>
              {node.children.map((child) => renderTreeNode(child, currentPath, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        key={currentPath}
        className={`flex items-center gap-1 py-1 px-2 rounded cursor-pointer hover:bg-accent/50 ${
          isSelected ? "bg-accent" : ""
        }`}
        style={{ paddingLeft: `${depth * 16 + 24}px` }}
        onClick={() => selectFile(currentPath, node.content)}
      >
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">{node.name}</span>
      </div>
    );
  };

  const fileTree = buildFileTree();

  // Team Evolution Summary
  const getEvolutionSummary = () => {
    if (!preview?.import?.manifest) return null;
    
    const manifest = preview.import.manifest;
    const importData = preview.import;
    
    return {
      teamName: manifest.team_name || "Unknown Team",
      version: manifest.team_version || "1.0.0",
      agentCount: importData.agent_count || manifest.agents?.length || 0,
      battlesParticipated: importData.total_semantic || 0,
      winRate: 0.78, // Demo value
      evolutionLevel: 12, // Demo value
      topPatterns: [
        "Mule network detection",
        "ATO prevention",
        "Velocity abuse blocking",
      ],
      lastDistilled: manifest.created_at,
    };
  };

  const evolutionSummary = getEvolutionSummary();

  return (
    <div className="space-y-6 p-6" data-testid="amc-explorer">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AMC Explorer</h1>
          <p className="text-muted-foreground">
            Explore Agent Memory Capsule packages
          </p>
        </div>
        <div className="flex gap-2">
          <input
            type="file"
            id="amc-file-input"
            accept=".amc,.zip"
            onChange={handleFileSelect}
            className="hidden"
          />
          <Button
            onClick={() => document.getElementById("amc-file-input")?.click()}
            disabled={loading}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload AMC
          </Button>
        </div>
      </div>

      {/* Drop Zone */}
      {!amcFile && (
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            isDragging
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50"
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          data-testid="amc-drop-zone"
        >
          <FileArchive className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">
            Drag & Drop an AMC File
          </h3>
          <p className="text-muted-foreground mb-4">
            or click "Upload AMC" to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supports .amc and .zip files
          </p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-64" />
        </div>
      )}

      {/* AMC Content */}
      {amcFile && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - File Tree */}
          <Card className="lg:col-span-1 border-border">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileArchive className="h-4 w-4" />
                {amcFile.name}
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-[500px] overflow-y-auto">
              {fileTree && fileTree.children?.map((node) => renderTreeNode(node))}
            </CardContent>
          </Card>

          {/* Middle Panel - Content Viewer */}
          <Card className="lg:col-span-1 border-border">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Eye className="h-4 w-4" />
                {selectedFile || "Select a file to view"}
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-[500px] overflow-y-auto">
              {fileContent ? (
                <pre className="text-xs bg-black/30 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                  {typeof fileContent === "object"
                    ? JSON.stringify(fileContent, null, 2)
                    : fileContent}
                </pre>
              ) : (
                <div className="text-center text-muted-foreground py-12">
                  Click a file in the tree to view its contents
                </div>
              )}
            </CardContent>
          </Card>

          {/* Right Panel - Summary & Badges */}
          <div className="lg:col-span-1 space-y-4">
            {/* Safety Scan Badge */}
            <Card className="border-border">
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Safety Scan
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {validation && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Structure</span>
                      <Badge
                        className={
                          validation.structure ? "status-success" : "status-error"
                        }
                      >
                        {validation.structure ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircle className="h-3 w-3 mr-1" />
                        )}
                        {validation.structure ? "Valid" : "Invalid"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Schemas</span>
                      <Badge
                        className={
                          validation.schemas ? "status-success" : "status-error"
                        }
                      >
                        {validation.schemas ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircle className="h-3 w-3 mr-1" />
                        )}
                        {validation.schemas ? "Valid" : "Invalid"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Integrity</span>
                      <Badge
                        className={
                          validation.integrity ? "status-success" : "status-error"
                        }
                      >
                        {validation.integrity ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircle className="h-3 w-3 mr-1" />
                        )}
                        {validation.integrity ? "Verified" : "Failed"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Safety (No PII)</span>
                      <Badge
                        className={
                          validation.policy ? "status-success" : "status-warning"
                        }
                      >
                        {validation.policy ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <AlertTriangle className="h-3 w-3 mr-1" />
                        )}
                        {validation.policy ? "Clean" : "Review"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Compatibility</span>
                      <Badge
                        className={
                          validation.compatibility
                            ? "status-success"
                            : "status-warning"
                        }
                      >
                        {validation.compatibility ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <AlertTriangle className="h-3 w-3 mr-1" />
                        )}
                        {validation.compatibility ? "Compatible" : "Check"}
                      </Badge>
                    </div>
                    
                    {/* Overall Badge */}
                    <div className="pt-3 border-t border-border">
                      <div className="flex items-center justify-center">
                        {validation.valid ? (
                          <Badge className="status-success text-lg px-4 py-2">
                            <Shield className="h-5 w-5 mr-2" />
                            AMC Verified Safe
                          </Badge>
                        ) : (
                          <Badge className="status-error text-lg px-4 py-2">
                            <XCircle className="h-5 w-5 mr-2" />
                            Validation Failed
                          </Badge>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Team Evolution Summary */}
            {evolutionSummary && (
              <Card className="border-border bg-gradient-to-br from-blue-900/10 to-purple-900/10">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-400" />
                    Team Evolution Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <h3 className="text-xl font-bold">
                      {evolutionSummary.teamName}
                    </h3>
                    <Badge variant="outline">v{evolutionSummary.version}</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-3 rounded bg-black/20">
                      <Users className="h-5 w-5 mx-auto text-blue-400 mb-1" />
                      <div className="text-2xl font-bold">
                        {evolutionSummary.agentCount}
                      </div>
                      <div className="text-xs text-muted-foreground">Agents</div>
                    </div>
                    <div className="text-center p-3 rounded bg-black/20">
                      <Activity className="h-5 w-5 mx-auto text-green-400 mb-1" />
                      <div className="text-2xl font-bold">
                        {(evolutionSummary.winRate * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Win Rate</div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Evolution Level</span>
                      <span>{evolutionSummary.evolutionLevel}/20</span>
                    </div>
                    <Progress
                      value={(evolutionSummary.evolutionLevel / 20) * 100}
                      className="h-2"
                    />
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground mb-2">
                      Top Learned Patterns
                    </p>
                    <div className="space-y-1">
                      {evolutionSummary.topPatterns.map((pattern, i) => (
                        <div
                          key={i}
                          className="text-xs bg-black/20 px-2 py-1 rounded"
                        >
                          {pattern}
                        </div>
                      ))}
                    </div>
                  </div>

                  {evolutionSummary.lastDistilled && (
                    <div className="text-xs text-muted-foreground text-center">
                      Last distilled:{" "}
                      {new Date(evolutionSummary.lastDistilled).toLocaleString()}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" disabled={!validation?.valid}>
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AMCExplorer;
