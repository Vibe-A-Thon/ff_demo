import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { ScrollArea } from "../components/ui/scroll-area";
import { amcAPI, teamAPI } from "../lib/api";
import { toast } from "sonner";
import { Download, Upload, FileDiff, ShieldCheck, FolderOpen, RefreshCw } from "lucide-react";

const DEFAULT_SCOPE = {
  include_memory_layers: ["semantic", "episodic", "procedural", "distilled"],
  include_logs: "sanitized_only",
  include_models: false,
  include_battle_refs: true,
  time_window_days: 180,
};

const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
};

const AmcManager = () => {
  const [teams, setTeams] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [teamId, setTeamId] = useState("");
  const [envTag, setEnvTag] = useState("sandbox");
  const [scope, setScope] = useState(DEFAULT_SCOPE);
  const [exporting, setExporting] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [diffOldFile, setDiffOldFile] = useState(null);
  const [diffNewFile, setDiffNewFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [previewResult, setPreviewResult] = useState(null);
  const [diffResult, setDiffResult] = useState(null);
  const [importMode, setImportMode] = useState("merge");
  const [activateAfterImport, setActivateAfterImport] = useState(false);
  const [loadingCatalog, setLoadingCatalog] = useState(false);

  useEffect(() => {
    const loadTeams = async () => {
      try {
        const response = await teamAPI.getAll();
        setTeams(response?.data || []);
        if (response?.data?.length) {
          setTeamId(response.data[0].team_id);
        }
      } catch (error) {
        setTeams([]);
      }
    };
    loadTeams();
  }, []);

  const refreshCatalog = async () => {
    setLoadingCatalog(true);
    try {
      const response = await amcAPI.catalog();
      setCatalog(response?.data || []);
    } catch (error) {
      setCatalog([]);
    } finally {
      setLoadingCatalog(false);
    }
  };

  useEffect(() => {
    refreshCatalog();
  }, []);

  const exportScopeDisplay = useMemo(
    () => scope.include_memory_layers.join(", "),
    [scope.include_memory_layers]
  );

  const handleExport = async () => {
    if (!teamId) {
      toast.error("Select a team to export.");
      return;
    }
    setExporting(true);
    try {
      const response = await amcAPI.export({ team_id: teamId, env_tag: envTag, export_scope: scope });
      const filename = response?.headers?.["content-disposition"]?.split("filename=")?.[1]?.replace(/"/g, "") || `${teamId}.amc`;
      downloadBlob(response.data, filename);
      toast.success("AMC export ready.");
      refreshCatalog();
    } catch (error) {
      toast.error("AMC export failed.");
    } finally {
      setExporting(false);
    }
  };

  const handleValidate = async () => {
    if (!uploadFile) {
      toast.error("Upload an AMC file first.");
      return;
    }
    const formData = new FormData();
    formData.append("file", uploadFile);
    try {
      const response = await amcAPI.validate(formData);
      setValidationResult(response?.data || null);
      toast.success("Validation completed.");
    } catch (error) {
      toast.error("Validation failed.");
    }
  };

  const handlePreview = async () => {
    if (!uploadFile) {
      toast.error("Upload an AMC file first.");
      return;
    }
    const formData = new FormData();
    formData.append("file", uploadFile);
    try {
      const response = await amcAPI.preview(formData);
      setPreviewResult(response?.data || null);
      toast.success("Preview ready.");
    } catch (error) {
      toast.error("Preview failed.");
    }
  };

  const handleImport = async () => {
    if (!uploadFile) {
      toast.error("Upload an AMC file first.");
      return;
    }
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("mode", importMode);
    formData.append("activate", activateAfterImport);
    try {
      const response = await amcAPI.import(formData);
      setPreviewResult(response?.data?.preview || null);
      toast.success("AMC imported.");
      refreshCatalog();
    } catch (error) {
      toast.error("AMC import failed.");
    }
  };

  const handleDiff = async () => {
    if (!diffOldFile || !diffNewFile) {
      toast.error("Upload both AMC files for diff.");
      return;
    }
    const formData = new FormData();
    formData.append("old_file", diffOldFile);
    formData.append("new_file", diffNewFile);
    try {
      const response = await amcAPI.diff(formData);
      setDiffResult(response?.data || null);
      toast.success("Diff generated.");
    } catch (error) {
      toast.error("Diff failed.");
    }
  };

  const handleActivate = async (packageId) => {
    const formData = new FormData();
    formData.append("package_id", packageId);
    try {
      await amcAPI.activate(formData);
      toast.success("AMC activated.");
      refreshCatalog();
    } catch (error) {
      toast.error("Activation failed.");
    }
  };

  return (
    <div className="space-y-6" data-testid="amc-manager-root">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AMC Manager</h1>
          <p className="text-sm text-muted-foreground">Export, validate, import, and compare Agent Memory Capsules.</p>
        </div>
        <Button onClick={refreshCatalog} variant="outline" data-testid="amc-manager-refresh">
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      <Tabs defaultValue="export" className="space-y-4">
        <TabsList className="bg-muted" data-testid="amc-manager-tabs">
          <TabsTrigger value="export" data-testid="amc-manager-tab-export">Export</TabsTrigger>
          <TabsTrigger value="import" data-testid="amc-manager-tab-import">Import</TabsTrigger>
          <TabsTrigger value="diff" data-testid="amc-manager-tab-diff">Diff</TabsTrigger>
          <TabsTrigger value="catalog" data-testid="amc-manager-tab-catalog">Catalog</TabsTrigger>
        </TabsList>

        <TabsContent value="export">
          <Card className="bg-card" data-testid="amc-export-card">
            <CardHeader>
              <CardTitle>Export AMC Capsule</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <label className="text-xs text-muted-foreground">Team</label>
                  <Select value={teamId} onValueChange={setTeamId} data-testid="amc-export-team">
                    <SelectTrigger data-testid="amc-export-team-trigger">
                      <SelectValue placeholder="Select team" />
                    </SelectTrigger>
                    <SelectContent>
                      {teams.map((team) => (
                        <SelectItem key={team.team_id} value={team.team_id}>
                          {team.bank_facing_name || team.internal_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Environment Tag</label>
                  <Input value={envTag} onChange={(event) => setEnvTag(event.target.value)} data-testid="amc-export-env" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Time Window (days)</label>
                  <Input
                    type="number"
                    value={scope.time_window_days}
                    onChange={(event) => setScope((prev) => ({ ...prev, time_window_days: Number(event.target.value || 0) }))}
                    data-testid="amc-export-window"
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Badge variant="outline">Memory Layers: {exportScopeDisplay}</Badge>
                <Badge variant="outline">Logs: {scope.include_logs}</Badge>
                <Badge variant="outline">Battle refs: {scope.include_battle_refs ? "Yes" : "No"}</Badge>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => setScope((prev) => ({ ...prev, include_battle_refs: !prev.include_battle_refs }))}
                  variant="outline"
                  data-testid="amc-export-toggle-battles"
                >
                  Toggle Battle Refs
                </Button>
                <Button
                  onClick={() => setScope((prev) => ({ ...prev, include_models: !prev.include_models }))}
                  variant="outline"
                  data-testid="amc-export-toggle-models"
                >
                  Toggle Models
                </Button>
                <Button onClick={handleExport} disabled={exporting} data-testid="amc-export-run">
                  <Download className="mr-2 h-4 w-4" /> {exporting ? "Exporting..." : "Export AMC"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="import">
          <Card className="bg-card" data-testid="amc-import-card">
            <CardHeader>
              <CardTitle>Validate & Import AMC</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="md:col-span-2">
                  <label className="text-xs text-muted-foreground">Upload AMC File</label>
                  <Input
                    type="file"
                    accept=".amc,.zip"
                    onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
                    data-testid="amc-import-file"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Import Mode</label>
                  <Select value={importMode} onValueChange={setImportMode} data-testid="amc-import-mode">
                    <SelectTrigger data-testid="amc-import-mode-trigger">
                      <SelectValue placeholder="Select mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="merge">Merge</SelectItem>
                      <SelectItem value="replace">Replace</SelectItem>
                      <SelectItem value="merge_calibrate">Merge + Calibrate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={handleValidate} variant="outline" data-testid="amc-import-validate">
                  <ShieldCheck className="mr-2 h-4 w-4" /> Validate
                </Button>
                <Button onClick={handlePreview} variant="outline" data-testid="amc-import-preview">
                  <FolderOpen className="mr-2 h-4 w-4" /> Preview
                </Button>
                <Button onClick={handleImport} data-testid="amc-import-run">
                  <Upload className="mr-2 h-4 w-4" /> Import AMC
                </Button>
                <Button
                  onClick={() => setActivateAfterImport((prev) => !prev)}
                  variant={activateAfterImport ? "default" : "outline"}
                  data-testid="amc-import-activate-toggle"
                >
                  {activateAfterImport ? "Activate After Import" : "Activate Later"}
                </Button>
              </div>

              {validationResult && (
                <div className="rounded-md border border-border bg-muted/30 p-4" data-testid="amc-validation-result">
                  <p className="text-sm font-semibold">Validation</p>
                  <p className="text-xs text-muted-foreground">Valid: {validationResult.valid ? "Yes" : "No"}</p>
                  <ScrollArea className="h-32 mt-2">
                    <pre className="text-xs whitespace-pre-wrap text-muted-foreground">
                      {JSON.stringify(validationResult, null, 2)}
                    </pre>
                  </ScrollArea>
                </div>
              )}

              {previewResult && (
                <div className="rounded-md border border-border bg-muted/30 p-4" data-testid="amc-preview-result">
                  <p className="text-sm font-semibold">Preview</p>
                  <ScrollArea className="h-32 mt-2">
                    <pre className="text-xs whitespace-pre-wrap text-muted-foreground">
                      {JSON.stringify(previewResult, null, 2)}
                    </pre>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="diff">
          <Card className="bg-card" data-testid="amc-diff-card">
            <CardHeader>
              <CardTitle>AMC Diff</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-xs text-muted-foreground">Old AMC</label>
                  <Input
                    type="file"
                    accept=".amc,.zip"
                    onChange={(event) => setDiffOldFile(event.target.files?.[0] || null)}
                    data-testid="amc-diff-old"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">New AMC</label>
                  <Input
                    type="file"
                    accept=".amc,.zip"
                    onChange={(event) => setDiffNewFile(event.target.files?.[0] || null)}
                    data-testid="amc-diff-new"
                  />
                </div>
              </div>
              <Button onClick={handleDiff} variant="outline" data-testid="amc-diff-run">
                <FileDiff className="mr-2 h-4 w-4" /> Generate Diff
              </Button>
              {diffResult && (
                <div className="rounded-md border border-border bg-muted/30 p-4" data-testid="amc-diff-result">
                  <ScrollArea className="h-48">
                    <pre className="text-xs whitespace-pre-wrap text-muted-foreground">
                      {JSON.stringify(diffResult, null, 2)}
                    </pre>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="catalog">
          <Card className="bg-card" data-testid="amc-catalog-card">
            <CardHeader>
              <CardTitle>AMC Catalog</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-muted-foreground">Stored AMC exports/imports.</p>
                <Badge variant="outline">{loadingCatalog ? "Loading..." : `${catalog.length} entries`}</Badge>
              </div>
              <div className="space-y-3">
                {catalog.map((entry) => (
                  <div key={entry.id} className="rounded-md border border-border p-4" data-testid={`amc-catalog-${entry.id}`}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-white">{entry.team_name || entry.team_id}</p>
                        <p className="text-xs text-muted-foreground">{entry.team_version} • {entry.env_tag} • {entry.source}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant="outline">{entry.status}</Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleActivate(entry.id)}
                          data-testid={`amc-catalog-activate-${entry.id}`}
                        >
                          Activate
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                {!catalog.length && (
                  <div className="text-sm text-muted-foreground" data-testid="amc-catalog-empty">
                    No AMC entries available.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AmcManager;
