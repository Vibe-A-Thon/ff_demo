import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Switch } from "../components/ui/switch";
import { ScrollArea } from "../components/ui/scroll-area";
import { Separator } from "../components/ui/separator";
import { knowledgeAPI } from "../lib/api";
import { toast } from "sonner";
import {
  RefreshCw,
  Database,
  Activity,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Timer,
} from "lucide-react";

const StatusBadge = ({ status }) => {
  const normalized = (status || "unknown").toLowerCase();
  if (normalized === "ok") {
    return <Badge className="bg-green-500/15 text-green-400 border border-green-500/30">Healthy</Badge>;
  }
  if (normalized === "skipped") {
    return <Badge className="bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">Skipped</Badge>;
  }
  if (normalized === "unavailable") {
    return <Badge className="bg-zinc-800 text-zinc-300 border border-zinc-700">Unavailable</Badge>;
  }
  return <Badge className="bg-red-500/15 text-red-400 border border-red-500/30">Error</Badge>;
};

const formatTimestamp = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString();
};

const timeAgo = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const diff = Date.now() - date.getTime();
  if (diff < 0) return "just now";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "<1m ago";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

const Neo4jSyncDashboard = () => {
  const [health, setHealth] = useState(null);
  const [syncHistory, setSyncHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const latestSync = syncHistory?.[0] || null;

  const loadDashboard = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [healthRes, statusRes] = await Promise.all([
        knowledgeAPI.neo4jHealth(),
        knowledgeAPI.graphSyncStatus(),
      ]);
      setHealth(healthRes?.data || null);
      setSyncHistory(statusRes?.data?.items || []);
    } catch (error) {
      setHealth({ status: "error", reason: "failed_to_fetch" });
      setSyncHistory([]);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const interval = window.setInterval(() => loadDashboard(true), 15000);
    return () => window.clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboard(true);
    setRefreshing(false);
  };

  const handleSyncNow = async () => {
    try {
      await knowledgeAPI.syncNeo4j();
      toast.success("Neo4j sync triggered");
      await loadDashboard(true);
    } catch (error) {
      toast.error("Sync trigger failed");
    }
  };

  const statusCards = useMemo(() => {
    return [
      {
        title: "Neo4j Health",
        value: health?.status || "unknown",
        icon: Activity,
        status: health?.status,
        detail: health?.reason || "Connection check",
      },
      {
        title: "Latest Sync",
        value: latestSync?.status || "pending",
        icon: Database,
        status: latestSync?.status,
        detail: latestSync?.reason || `${latestSync?.nodes || 0} nodes`,
      },
      {
        title: "Last Run",
        value: timeAgo(latestSync?.timestamp),
        icon: Timer,
        status: latestSync?.status,
        detail: formatTimestamp(latestSync?.timestamp),
      },
    ];
  }, [health, latestSync]);

  return (
    <div className="space-y-6" data-testid="neo4j-sync-page">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Neo4j Sync Health</h1>
          <p className="text-sm text-muted-foreground">
            Automated graph ingestion health, scheduler telemetry, and sync history.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-md border border-border px-3 py-2">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
              data-testid="neo4j-sync-controls-auto-refresh"
            />
            <span className="text-xs text-muted-foreground">Auto refresh</span>
          </div>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            data-testid="neo4j-sync-controls-refresh"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            onClick={handleSyncNow}
            data-testid="neo4j-sync-controls-sync-now"
          >
            <ShieldCheck className="mr-2 h-4 w-4" />
            Sync Now
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {statusCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title} className="border-border" data-testid={`neo4j-sync-card-${card.title.toLowerCase().replace(/\s/g, "-")}`}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center justify-between">
                  <span>{card.title}</span>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold font-mono text-foreground">
                    {card.value}
                  </span>
                  <StatusBadge status={card.status} />
                </div>
                <p className="text-xs text-muted-foreground">{card.detail}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card className="border-border" data-testid="neo4j-sync-history">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Sync History</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[360px]">
              <div className="divide-y divide-border">
                {loading && (
                  <div className="p-4 text-sm text-muted-foreground">Loading sync telemetry...</div>
                )}
                {!loading && syncHistory.length === 0 && (
                  <div className="p-4 text-sm text-muted-foreground">No sync records yet.</div>
                )}
                {syncHistory.map((entry, index) => (
                  <div
                    key={`${entry.timestamp || "row"}-${index}`}
                    className="p-4 flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between"
                  >
                    <div className="flex items-center gap-3">
                      {entry.status === "ok" ? (
                        <CheckCircle2 className="h-5 w-5 text-green-400" />
                      ) : entry.status === "skipped" || entry.status === "unavailable" ? (
                        <AlertTriangle className="h-5 w-5 text-yellow-400" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-red-400" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-foreground">{entry.status || "unknown"}</span>
                          <StatusBadge status={entry.status} />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {entry.reason || "Sync completed"}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground font-mono">
                      <span>Nodes: {entry.nodes ?? 0}</span>
                      <span>Edges: {entry.relationships ?? 0}</span>
                      <span>{formatTimestamp(entry.timestamp)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="neo4j-sync-scheduler">
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Scheduler Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-border bg-background/60 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">Latest run</p>
                  <p className="text-lg font-semibold font-mono text-foreground">
                    {timeAgo(latestSync?.timestamp)}
                  </p>
                </div>
                <Timer className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>

            <div className="rounded-md border border-border bg-background/60 p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Health signal</span>
                <StatusBadge status={health?.status} />
              </div>
              <Separator className="bg-border" />
              <div className="space-y-2 text-xs text-muted-foreground">
                <p>Reason: {health?.reason || "—"}</p>
                <p>Last sync: {formatTimestamp(latestSync?.timestamp)}</p>
                <p>Nodes synced: {latestSync?.nodes ?? 0}</p>
                <p>Relationships: {latestSync?.relationships ?? 0}</p>
              </div>
            </div>

            <div className="rounded-md border border-border bg-background/60 p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Database className="h-4 w-4" />
                <span>Operational Notes</span>
              </div>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Background loop runs from backend startup if enabled.</li>
                <li>• Manual sync records are logged with status + counts.</li>
                <li>• Health probes verify Neo4j connectivity.</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Neo4jSyncDashboard;
