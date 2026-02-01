import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { ShieldCheck, KeyRound, Save, RefreshCw } from "lucide-react";
import { settingsAPI } from "../lib/api";
import { toast } from "sonner";

const apiKeys = [
  { id: "key-01", name: "OpenAI (Primary)", lastRotated: "2026-01-10", status: "active" },
  { id: "key-02", name: "RAG Vector Store", lastRotated: "2025-12-30", status: "active" },
  { id: "key-03", name: "Monitoring Webhook", lastRotated: "2025-12-05", status: "needs-rotation" },
];

const keyStatusStyles = {
  active: "bg-green-500/15 text-green-400 border-green-500/20",
  "needs-rotation": "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
};

const SettingsConfiguration = () => {
  const [hitlEnabled, setHitlEnabled] = useState(true);
  const [autoReplay, setAutoReplay] = useState(true);
  const [incidentPaging, setIncidentPaging] = useState(false);
  const [bankName, setBankName] = useState("Fraud Forge Bank");
  const [region, setRegion] = useState("US-East");
  const [faithfulnessDrop, setFaithfulnessDrop] = useState("0.05");
  const [relevancyDrop, setRelevancyDrop] = useState("0.05");
  const [faithfulnessWarn, setFaithfulnessWarn] = useState("0.75");
  const [relevancyWarn, setRelevancyWarn] = useState("0.75");
  const [hitRateWarn, setHitRateWarn] = useState("0.6");
  const [hitRateCrit, setHitRateCrit] = useState("0.4");
  const [cacheDir, setCacheDir] = useState("");
  const [cacheTtl, setCacheTtl] = useState("600");
  const [cacheMaxItems, setCacheMaxItems] = useState("200");
  const [settingsLoading, setSettingsLoading] = useState(true);

  const loadSettings = async () => {
    setSettingsLoading(true);
    try {
      const response = await settingsAPI.get();
      const rag = response?.data?.rag || {};
      setFaithfulnessDrop(String(rag.faithfulness_drop ?? "0.05"));
      setRelevancyDrop(String(rag.relevancy_drop ?? "0.05"));
      setFaithfulnessWarn(String(rag.faithfulness_warn ?? "0.75"));
      setRelevancyWarn(String(rag.relevancy_warn ?? "0.75"));
      setHitRateWarn(String(rag.hit_rate_warn ?? "0.6"));
      setHitRateCrit(String(rag.hit_rate_crit ?? "0.4"));
      setCacheDir(String(rag.cache_dir ?? ""));
      setCacheTtl(String(rag.cache_ttl_seconds ?? "600"));
      setCacheMaxItems(String(rag.cache_max_items ?? "200"));
    } catch (error) {
      toast.error("Failed to load settings.");
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const payload = {
        rag: {
          faithfulness_drop: Number(faithfulnessDrop),
          relevancy_drop: Number(relevancyDrop),
          faithfulness_warn: Number(faithfulnessWarn),
          relevancy_warn: Number(relevancyWarn),
          hit_rate_warn: Number(hitRateWarn),
          hit_rate_crit: Number(hitRateCrit),
          cache_dir: cacheDir,
          cache_ttl_seconds: Number(cacheTtl),
          cache_max_items: Number(cacheMaxItems),
        },
      };
      await settingsAPI.update(payload);
      toast.success("Settings updated.");
    } catch (error) {
      toast.error("Failed to update settings.");
    }
  };

  const handleReset = async () => {
    await loadSettings();
  };

  React.useEffect(() => {
    loadSettings();
  }, []);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Platform</p>
            <h1 className="text-2xl font-semibold">Settings & Configuration</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" data-testid="settings-reset" onClick={handleReset}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <Button data-testid="settings-save" onClick={handleSave} disabled={settingsLoading}>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Configure governance modes, integrations, and operational guardrails. Changes are logged and require approval where
          applicable.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card className="border-border" data-testid="settings-bank">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-blue-400" />
              Bank Instance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="bank-name">Bank Name</Label>
              <Input
                id="bank-name"
                value={bankName}
                onChange={(event) => setBankName(event.target.value)}
                data-testid="settings-bank-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bank-region">Primary Region</Label>
              <Input
                id="bank-region"
                value={region}
                onChange={(event) => setRegion(event.target.value)}
                data-testid="settings-bank-region"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">HITL Mode</p>
                  <p className="text-xs text-muted-foreground">Require human approval at every gate</p>
                </div>
                <Switch checked={hitlEnabled} onCheckedChange={setHitlEnabled} data-testid="settings-hitl-toggle" />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">Auto Replay</p>
                  <p className="text-xs text-muted-foreground">Trigger nightly replay suites</p>
                </div>
                <Switch checked={autoReplay} onCheckedChange={setAutoReplay} data-testid="settings-replay-toggle" />
              </div>
              <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">Incident Paging</p>
                  <p className="text-xs text-muted-foreground">Page on-call for critical incidents</p>
                </div>
                <Switch checked={incidentPaging} onCheckedChange={setIncidentPaging} data-testid="settings-paging-toggle" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="settings-keys">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-yellow-400" />
              API Key Vault
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Key</TableHead>
                  <TableHead>Last Rotated</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell className="text-muted-foreground">{key.lastRotated}</TableCell>
                    <TableCell>
                      <Badge className={`border ${keyStatusStyles[key.status]}`} data-testid={`settings-key-${key.id}`}>
                        {key.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="outline" size="sm" data-testid={`settings-rotate-${key.id}`}>
                        Rotate
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border" data-testid="settings-rag">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-purple-400" />
            RAG Evaluation & Cache Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="rag-faith-drop">Faithfulness Drop Threshold</Label>
            <Input
              id="rag-faith-drop"
              value={faithfulnessDrop}
              onChange={(event) => setFaithfulnessDrop(event.target.value)}
              data-testid="settings-rag-faith-drop"
            />
            <p className="text-xs text-muted-foreground">Used for regression alerts.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-rel-drop">Relevancy Drop Threshold</Label>
            <Input
              id="rag-rel-drop"
              value={relevancyDrop}
              onChange={(event) => setRelevancyDrop(event.target.value)}
              data-testid="settings-rag-rel-drop"
            />
            <p className="text-xs text-muted-foreground">Used for regression alerts.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-faith-warn">Faithfulness Warning Floor</Label>
            <Input
              id="rag-faith-warn"
              value={faithfulnessWarn}
              onChange={(event) => setFaithfulnessWarn(event.target.value)}
              data-testid="settings-rag-faith-warn"
            />
            <p className="text-xs text-muted-foreground">Warn when faithfulness drops below this.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-rel-warn">Relevancy Warning Floor</Label>
            <Input
              id="rag-rel-warn"
              value={relevancyWarn}
              onChange={(event) => setRelevancyWarn(event.target.value)}
              data-testid="settings-rag-rel-warn"
            />
            <p className="text-xs text-muted-foreground">Warn when relevancy drops below this.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-hit-warn">Cache Hit Rate Warn</Label>
            <Input
              id="rag-hit-warn"
              value={hitRateWarn}
              onChange={(event) => setHitRateWarn(event.target.value)}
              data-testid="settings-rag-hit-warn"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-hit-crit">Cache Hit Rate Critical</Label>
            <Input
              id="rag-hit-crit"
              value={hitRateCrit}
              onChange={(event) => setHitRateCrit(event.target.value)}
              data-testid="settings-rag-hit-crit"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-cache-dir">Shared Model Cache</Label>
            <Input
              id="rag-cache-dir"
              value={cacheDir}
              onChange={(event) => setCacheDir(event.target.value)}
              data-testid="settings-rag-cache-dir"
            />
            <p className="text-xs text-muted-foreground">Points to shared storage path.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-cache-ttl">CAG Cache TTL (seconds)</Label>
            <Input
              id="rag-cache-ttl"
              value={cacheTtl}
              onChange={(event) => setCacheTtl(event.target.value)}
              data-testid="settings-rag-cache-ttl"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rag-cache-max">CAG Cache Max Items</Label>
            <Input
              id="rag-cache-max"
              value={cacheMaxItems}
              onChange={(event) => setCacheMaxItems(event.target.value)}
              data-testid="settings-rag-cache-max"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border" data-testid="settings-integrations">
        <CardHeader>
          <CardTitle className="text-lg">Integrations</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-md border border-border p-4 space-y-2">
            <p className="text-sm font-medium">Streaming Gateway</p>
            <p className="text-xs text-muted-foreground">ws://stream.ff.local</p>
            <Button variant="outline" size="sm" data-testid="settings-streaming-config">
              Configure
            </Button>
          </div>
          <div className="rounded-md border border-border p-4 space-y-2">
            <p className="text-sm font-medium">Evidence Storage</p>
            <p className="text-xs text-muted-foreground">S3 • encrypted</p>
            <Button variant="outline" size="sm" data-testid="settings-storage-config">
              Configure
            </Button>
          </div>
          <div className="rounded-md border border-border p-4 space-y-2">
            <p className="text-sm font-medium">Notification Hub</p>
            <p className="text-xs text-muted-foreground">PagerDuty • 2 policies</p>
            <Button variant="outline" size="sm" data-testid="settings-notifications-config">
              Configure
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsConfiguration;
