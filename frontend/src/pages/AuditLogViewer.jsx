import React, { useMemo, useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { ScrollArea } from "../components/ui/scroll-area";
import { FileText, Download, Filter, Brain, Database } from "lucide-react";
import { ragAPI, settingsAPI } from "../lib/api";

const auditLogs = [
  {
    id: "LOG-8821",
    actor: "techlead@bank.com",
    action: "Patch Approved",
    resource: "RSB-492",
    timestamp: "2026-01-29 14:12",
    status: "approved",
  },
  {
    id: "LOG-8813",
    actor: "operator@bank.com",
    action: "Battle Paused",
    resource: "Battle-1129",
    timestamp: "2026-01-29 13:58",
    status: "actioned",
  },
  {
    id: "LOG-8802",
    actor: "auditor@bank.com",
    action: "Evidence Exported",
    resource: "Case-1188",
    timestamp: "2026-01-29 12:41",
    status: "exported",
  },
  {
    id: "LOG-8796",
    actor: "manager@bank.com",
    action: "Release Approved",
    resource: "Release-33",
    timestamp: "2026-01-29 11:10",
    status: "approved",
  },
];

const statusStyles = {
  approved: "bg-green-500/15 text-green-400 border-green-500/20",
  actioned: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  exported: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
};

const AuditLogViewer = () => {
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [ragEvalEvents, setRagEvalEvents] = useState([]);
  const [ragCacheTelemetry, setRagCacheTelemetry] = useState(null);
  const [ragSettings, setRagSettings] = useState(null);

  const filteredLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const matchesSearch = `${log.actor} ${log.action} ${log.resource}`.toLowerCase().includes(search.toLowerCase());
      const matchesAction = actionFilter === "all" || log.action === actionFilter;
      const matchesStatus = statusFilter === "all" || log.status === statusFilter;
      return matchesSearch && matchesAction && matchesStatus;
    });
  }, [search, actionFilter, statusFilter]);

  useEffect(() => {
    const loadRagAudit = async () => {
      try {
        const [historyRes, telemetryRes, settingsRes] = await Promise.all([
          ragAPI.evaluationHistory({ limit: 5 }),
          ragAPI.cacheTelemetry({ limit: 20 }),
          settingsAPI.get(),
        ]);
        setRagEvalEvents(historyRes?.data?.items || []);
        setRagCacheTelemetry(telemetryRes?.data?.summary || null);
        setRagSettings(settingsRes?.data?.rag || null);
      } catch (error) {
        setRagEvalEvents([]);
        setRagCacheTelemetry(null);
        setRagSettings(null);
      }
    };
    loadRagAudit();
  }, []);

  return (
    <div className="flex h-full flex-col gap-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Compliance</p>
            <h1 className="text-2xl font-semibold">Audit Log Viewer</h1>
          </div>
          <Button variant="outline" className="gap-2" data-testid="audit-export">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Immutable, chain-of-custody logs for every action across the platform. Filter by actor, action, or compliance outcome.
        </p>
      </header>
      <ScrollArea className="flex-1">
        <div className="space-y-6 pr-2">
          <Card className="border-border" data-testid="audit-filters">
            <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
              <div className="flex-1">
                <Input
                  placeholder="Search by actor, action, or resource"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  data-testid="audit-search"
                />
              </div>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger className="w-full md:w-[220px]" data-testid="audit-filter-action">
                  <SelectValue placeholder="Action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="Patch Approved">Patch Approved</SelectItem>
                  <SelectItem value="Battle Paused">Battle Paused</SelectItem>
                  <SelectItem value="Evidence Exported">Evidence Exported</SelectItem>
                  <SelectItem value="Release Approved">Release Approved</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-[220px]" data-testid="audit-filter-status">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="actioned">Actioned</SelectItem>
                  <SelectItem value="exported">Exported</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" data-testid="audit-filter-advanced">
                <Filter className="mr-2 h-4 w-4" />
                Advanced Filters
              </Button>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Card className="border-border" data-testid="audit-rag-evals">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Brain className="h-4 w-4 text-purple-400" />
                  RAG Evaluation Events
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {!ragEvalEvents.length && (
                  <p className="text-sm text-muted-foreground">No RAG evaluation events logged yet.</p>
                )}
                {ragEvalEvents.map((event, index) => (
                  <div key={`${event.report_id}-${index}`} className="rounded-md border border-border p-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-foreground">{event.report_id}</span>
                      <Badge variant="outline" className="border-border">
                        {event.metrics?.cases || 0} cases
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">{event.created_at}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card className="border-border" data-testid="audit-rag-cache">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-400" />
                  RAG Cache Telemetry
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {ragCacheTelemetry ? (
                  <>
                    <p className="text-muted-foreground">Hit rate: {(ragCacheTelemetry.hit_rate * 100).toFixed(1)}%</p>
                    <p className="text-muted-foreground">Hits: {ragCacheTelemetry.hits} • Misses: {ragCacheTelemetry.misses}</p>
                    <p className="text-muted-foreground">Cache size: {ragCacheTelemetry.cache_stats?.size || 0}</p>
                    {ragSettings && (
                      <Badge className={ragCacheTelemetry.hit_rate <= (ragSettings.hit_rate_crit ?? 0.4)
                        ? "bg-red-500/15 text-red-400 border border-red-500/30"
                        : ragCacheTelemetry.hit_rate <= (ragSettings.hit_rate_warn ?? 0.6)
                          ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                          : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                        {ragCacheTelemetry.hit_rate <= (ragSettings.hit_rate_crit ?? 0.4)
                          ? "CRITICAL"
                          : ragCacheTelemetry.hit_rate <= (ragSettings.hit_rate_warn ?? 0.6)
                            ? "WARN"
                            : "OK"}
                      </Badge>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">No cache telemetry available.</p>
                )}
              </CardContent>
            </Card>
          </div>

          <Card className="border-border" data-testid="audit-table">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-4 w-4 text-yellow-400" />
                Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[420px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Actor</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-mono text-xs">{log.id}</TableCell>
                        <TableCell>{log.actor}</TableCell>
                        <TableCell>{log.action}</TableCell>
                        <TableCell>{log.resource}</TableCell>
                        <TableCell className="text-muted-foreground">{log.timestamp}</TableCell>
                        <TableCell>
                          <Badge className={`border ${statusStyles[log.status]}`} data-testid={`audit-status-${log.id}`}>
                            {log.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
};

export default AuditLogViewer;
