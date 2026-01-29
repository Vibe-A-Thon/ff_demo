import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { ShieldCheck, KeyRound, Save, RefreshCw } from "lucide-react";

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

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Platform</p>
            <h1 className="text-2xl font-semibold">Settings & Configuration</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" data-testid="settings-reset">
              <RefreshCw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <Button data-testid="settings-save">
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
