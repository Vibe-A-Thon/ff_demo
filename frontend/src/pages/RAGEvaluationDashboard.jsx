import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { ragAPI, settingsAPI } from "../lib/api";
import { toast } from "sonner";
import { Sparkles, RefreshCw, Database, AlertTriangle } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const RAGEvaluationDashboard = () => {
  const [evalHistory, setEvalHistory] = useState([]);
  const [evalAlerts, setEvalAlerts] = useState([]);
  const [cacheTelemetry, setCacheTelemetry] = useState(null);
  const [cacheEvents, setCacheEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState("20");
  const [refreshing, setRefreshing] = useState(false);
  const [ragSettings, setRagSettings] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [historyRes, alertsRes, telemetryRes, settingsRes] = await Promise.all([
        ragAPI.evaluationHistory({ limit: Number(limit) }),
        ragAPI.evaluationAlerts({ limit: 10 }),
        ragAPI.cacheTelemetry({ limit: 120 }),
        settingsAPI.get(),
      ]);
      setEvalHistory(historyRes?.data?.items || []);
      setEvalAlerts(alertsRes?.data?.items || []);
      setCacheTelemetry(telemetryRes?.data?.summary || null);
      setCacheEvents(telemetryRes?.data?.items || []);
      setRagSettings(settingsRes?.data?.rag || null);
    } catch (error) {
      setEvalHistory([]);
      setEvalAlerts([]);
      setCacheTelemetry(null);
      setCacheEvents([]);
      setRagSettings(null);
      toast.error("Failed to load RAG evaluation telemetry.");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleGoldEval = async () => {
    try {
      await ragAPI.evaluateGold();
      toast.success("Gold evaluation completed.");
      await loadData();
    } catch (error) {
      toast.error("Gold evaluation failed.");
    }
  };

  const evalSeries = useMemo(() => {
    return [...evalHistory]
      .reverse()
      .map((item, index) => ({
        name: `Eval ${index + 1}`,
        faithfulness: item?.metrics?.avg_faithfulness || 0,
        relevancy: item?.metrics?.avg_answer_relevancy || 0,
        precision: item?.metrics?.avg_precision_at_k || 0,
        recall: item?.metrics?.avg_recall_at_k || 0,
      }));
  }, [evalHistory]);

  const latestReport = evalHistory[0];
  const warnFaith = Number(ragSettings?.faithfulness_warn ?? 0.75);
  const warnRel = Number(ragSettings?.relevancy_warn ?? 0.75);

  return (
    <div className="space-y-6" data-testid="rag-evaluation-page">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm text-muted-foreground">RAG Quality Ops</p>
          <h1 className="text-2xl font-semibold">RAG Evaluation</h1>
          <p className="text-sm text-muted-foreground max-w-2xl">
            Long-term evaluation trends, regression alerts, and cache telemetry for the multi‑RAG pipeline.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select value={limit} onValueChange={setLimit}>
            <SelectTrigger className="w-[140px]" data-testid="rag-eval-limit">
              <SelectValue placeholder="Reports" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">Last 10</SelectItem>
              <SelectItem value="20">Last 20</SelectItem>
              <SelectItem value="50">Last 50</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing} data-testid="rag-eval-refresh">
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button onClick={handleGoldEval} data-testid="rag-eval-run-gold">
            <Sparkles className="mr-2 h-4 w-4" />
            Run Gold Eval
          </Button>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="border-border" data-testid="rag-eval-latest">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Latest Report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-2xl font-semibold font-mono text-foreground">
              {latestReport ? latestReport.report_id?.slice(0, 8) : "—"}
            </div>
            <p className="text-xs text-muted-foreground">{latestReport?.created_at || "No reports"}</p>
          </CardContent>
        </Card>
        <Card className="border-border" data-testid="rag-eval-faithfulness">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Faithfulness</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold font-mono text-foreground">
              {latestReport?.metrics?.avg_faithfulness?.toFixed?.(3) ?? "—"}
            </div>
            {latestReport && (
              <Badge className={(latestReport?.metrics?.avg_faithfulness || 0) < warnFaith
                ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                {(latestReport?.metrics?.avg_faithfulness || 0) < warnFaith ? "WARN" : "OK"}
              </Badge>
            )}
          </CardContent>
        </Card>
        <Card className="border-border" data-testid="rag-eval-relevancy">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Answer Relevancy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold font-mono text-foreground">
              {latestReport?.metrics?.avg_answer_relevancy?.toFixed?.(3) ?? "—"}
            </div>
            {latestReport && (
              <Badge className={(latestReport?.metrics?.avg_answer_relevancy || 0) < warnRel
                ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                {(latestReport?.metrics?.avg_answer_relevancy || 0) < warnRel ? "WARN" : "OK"}
              </Badge>
            )}
          </CardContent>
        </Card>
        <Card className="border-border" data-testid="rag-eval-alerts">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Regression Alerts</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div className="text-2xl font-semibold font-mono text-foreground">
              {evalAlerts.length}
            </div>
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card className="border-border" data-testid="rag-eval-trends">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              Evaluation Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading && <p className="text-sm text-muted-foreground">Loading evaluation data...</p>}
            {!loading && evalSeries.length === 0 && (
              <p className="text-sm text-muted-foreground">No evaluation history recorded yet.</p>
            )}
            {evalSeries.length > 0 && (
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={evalSeries} margin={{ left: 0, right: 16, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={10} />
                    <YAxis stroke="#71717A" fontSize={10} domain={[0, 1]} />
                    <Tooltip contentStyle={{ background: "#18181B", border: "1px solid #27272A" }} />
                    <Line type="monotone" dataKey="faithfulness" stroke="#22c55e" strokeWidth={2} />
                    <Line type="monotone" dataKey="relevancy" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="precision" stroke="#a855f7" strokeWidth={2} />
                    <Line type="monotone" dataKey="recall" stroke="#f59e0b" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="rag-eval-alert-feed">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
              Alert Feed
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!evalAlerts.length && <p className="text-sm text-muted-foreground">No regression alerts.</p>}
            {evalAlerts.map((alert, index) => (
              <div key={`${alert.report_id}-${index}`} className="rounded-md border border-border p-3 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Regression detected</span>
                  <span>{alert.created_at}</span>
                </div>
                <div>Δ Faithfulness: {alert.drop_faithfulness?.toFixed?.(3) ?? alert.drop_faithfulness}</div>
                <div>Δ Relevancy: {alert.drop_relevancy?.toFixed?.(3) ?? alert.drop_relevancy}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-border" data-testid="rag-cache-summary">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-400" />
              Cache Telemetry Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {cacheTelemetry ? (
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-md border border-border p-3">
                  <p className="text-xs text-muted-foreground">Hit rate</p>
                  <p className="text-lg font-mono text-foreground">
                    {(cacheTelemetry.hit_rate * 100).toFixed(1)}%
                  </p>
                  {ragSettings && (
                    <Badge className={cacheTelemetry.hit_rate <= (ragSettings.hit_rate_crit ?? 0.4)
                      ? "bg-red-500/15 text-red-400 border border-red-500/30"
                      : cacheTelemetry.hit_rate <= (ragSettings.hit_rate_warn ?? 0.6)
                        ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                        : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                      {cacheTelemetry.hit_rate <= (ragSettings.hit_rate_crit ?? 0.4)
                        ? "CRITICAL"
                        : cacheTelemetry.hit_rate <= (ragSettings.hit_rate_warn ?? 0.6)
                          ? "WARN"
                          : "OK"}
                    </Badge>
                  )}
                </div>
                <div className="rounded-md border border-border p-3">
                  <p className="text-xs text-muted-foreground">Hits / Misses</p>
                  <p className="text-lg font-mono text-foreground">
                    {cacheTelemetry.hits} / {cacheTelemetry.misses}
                  </p>
                </div>
                <div className="rounded-md border border-border p-3">
                  <p className="text-xs text-muted-foreground">Cache Size</p>
                  <p className="text-lg font-mono text-foreground">
                    {cacheTelemetry.cache_stats?.size || 0}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No cache telemetry available yet.</p>
            )}
            <div className="rounded-md border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
              <p>Last event: {cacheTelemetry?.last_event?.event || "—"}</p>
              <p>Layer: {cacheTelemetry?.last_event?.layer || "—"}</p>
              <p>At: {cacheTelemetry?.last_event?.created_at || "—"}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="rag-cache-events">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-400" />
              Cache Events
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[260px]">
              <div className="divide-y divide-border">
                {cacheEvents.map((event, index) => (
                  <div key={`${event.key_hash}-${index}`} className="p-3 text-xs">
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span>{event.event}</span>
                      <span>{event.layer}</span>
                    </div>
                    <div className="text-muted-foreground">{event.created_at}</div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border" data-testid="rag-eval-history">
        <CardHeader>
          <CardTitle className="text-lg">Evaluation History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[320px]">
            <div className="divide-y divide-border">
              {loading && (
                <div className="p-4 text-sm text-muted-foreground">Loading evaluation history...</div>
              )}
              {!loading && !evalHistory.length && (
                <div className="p-4 text-sm text-muted-foreground">No evaluation reports yet.</div>
              )}
              {evalHistory.map((report, index) => (
                <div key={`${report.report_id}-${index}`} className="p-4 text-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">{report.report_id}</p>
                      <p className="text-xs text-muted-foreground">{report.created_at}</p>
                    </div>
                    <Badge variant="outline" className="border-border text-xs">
                      {report.metrics?.cases || 0} cases
                    </Badge>
                  </div>
                  <div className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
                    <span>Faithfulness: {report.metrics?.avg_faithfulness?.toFixed?.(3) ?? "—"}</span>
                    <span>Relevancy: {report.metrics?.avg_answer_relevancy?.toFixed?.(3) ?? "—"}</span>
                    <span>Precision@k: {report.metrics?.avg_precision_at_k?.toFixed?.(3) ?? "—"}</span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default RAGEvaluationDashboard;
