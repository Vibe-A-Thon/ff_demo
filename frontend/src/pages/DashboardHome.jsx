import React, { useMemo, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { useAuth } from "../contexts/AuthContext";
import { agentAPI, ragAPI, settingsAPI } from "../lib/api";
import {
  Activity,
  ShieldAlert,
  CheckCircle2,
  Timer,
  Swords,
  FileSearch,
  GitCompare,
  Settings,
} from "lucide-react";

const quickActions = [
  { id: "start-battle", label: "Start Battle", icon: Swords, intent: "red", path: "/war-room", roles: ["analyst", "engineer", "admin"] },
  { id: "lifecycle-auto", label: "Lifecycle Auto-Run", icon: Activity, intent: "blue", path: "/war-room?lifecycle=auto", roles: ["analyst", "engineer", "admin"] },
  { id: "open-evidence", label: "Open Evidence", icon: FileSearch, intent: "gold", path: "/evidence", roles: ["analyst", "compliance", "admin"] },
  { id: "review-diff", label: "Review Diff", icon: GitCompare, intent: "orange", path: "/diff-viewer", roles: ["engineer", "admin"] },
  { id: "configure", label: "Configure", icon: Settings, intent: "white", path: "/settings", roles: ["admin", "compliance"] },
];

const kpis = [
  { label: "Active Battles", value: 6, change: "+12%", trend: "up", icon: Activity, color: "text-blue-400", path: "/war-room", roles: ["analyst", "engineer", "admin"] },
  { label: "Open Incidents", value: 3, change: "-25%", trend: "down", icon: ShieldAlert, color: "text-red-400", path: "/incidents", roles: ["analyst", "compliance", "admin"] },
  { label: "Approvals Pending", value: 8, change: "+4%", trend: "up", icon: CheckCircle2, color: "text-green-400", path: "/approvals", roles: ["compliance", "engineer", "admin"] },
  { label: "Time-to-Immunity", value: "3h 18m", change: "-18%", trend: "down", icon: Timer, color: "text-purple-400", path: "/metrics", roles: ["analyst", "admin", "compliance"] },
];

const recentActivity = [
  {
    id: "activity-1",
    title: "RSB-492 merged into staging",
    meta: "Green Team • 12 minutes ago",
    status: "merged",
    roles: ["engineer", "admin"],
  },
  {
    id: "activity-2",
    title: "Incident INC-204 escalated to Purple",
    meta: "Blue Team • 45 minutes ago",
    status: "escalated",
    roles: ["analyst", "compliance", "admin"],
  },
  {
    id: "activity-3",
    title: "Evidence pack exported for Case-1188",
    meta: "Gold Team • 2 hours ago",
    status: "exported",
    roles: ["compliance", "admin", "analyst"],
  },
  {
    id: "activity-4",
    title: "RuleSpec v3.2 approved",
    meta: "Orange Team • 4 hours ago",
    status: "approved",
    roles: ["compliance", "engineer", "admin"],
  },
];


const badgeStyles = {
  merged: "bg-green-500/15 text-green-400 border-green-500/20",
  escalated: "bg-red-500/15 text-red-400 border-red-500/20",
  exported: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  approved: "bg-blue-500/15 text-blue-400 border-blue-500/20",
};


const DashboardHome = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [registrySnapshot, setRegistrySnapshot] = useState(null);
  const [ragSnapshot, setRagSnapshot] = useState(null);
  const [ragLoading, setRagLoading] = useState(true);
  const actionStyles = useMemo(
    () => ({
      red: "border-red-500/40 text-red-300 hover:bg-red-500/10",
      blue: "border-blue-500/40 text-blue-300 hover:bg-blue-500/10",
      gold: "border-yellow-500/40 text-yellow-300 hover:bg-yellow-500/10",
      orange: "border-orange-500/40 text-orange-300 hover:bg-orange-500/10",
      white: "border-slate-200/40 text-slate-200 hover:bg-slate-200/10",
    }),
    []
  );

  const filterByRole = (items) => {
    if (!user?.role || user.role === "admin") return items;
    return items.filter((item) => !item.roles || item.roles.includes(user.role));
  };

  useEffect(() => {
    const loadRegistry = async () => {
      try {
        const response = await agentAPI.getRegistry();
        setRegistrySnapshot(response?.data || null);
      } catch (error) {
        setRegistrySnapshot(null);
      }
    };
    loadRegistry();
  }, []);

  useEffect(() => {
    const loadRagSnapshot = async () => {
      setRagLoading(true);
      try {
        const [historyRes, telemetryRes, alertsRes, settingsRes] = await Promise.all([
          ragAPI.evaluationHistory({ limit: 1 }),
          ragAPI.cacheTelemetry({ limit: 50 }),
          ragAPI.evaluationAlerts({ limit: 5 }),
          settingsAPI.get(),
        ]);
        const latest = historyRes?.data?.items?.[0] || null;
        const telemetry = telemetryRes?.data?.summary || null;
        const alerts = alertsRes?.data?.items || [];
        const ragSettings = settingsRes?.data?.rag || {};
        setRagSnapshot({ latest, telemetry, alerts, ragSettings });
      } catch (error) {
        setRagSnapshot(null);
      } finally {
        setRagLoading(false);
      }
    };
    loadRagSnapshot();
  }, []);

  const hitRateStatus = () => {
    const hitRate = ragSnapshot?.telemetry?.hit_rate;
    if (hitRate === undefined || hitRate === null) return "neutral";
    const warn = Number(ragSnapshot?.ragSettings?.hit_rate_warn ?? 0.6);
    const crit = Number(ragSnapshot?.ragSettings?.hit_rate_crit ?? 0.4);
    if (hitRate <= crit) return "critical";
    if (hitRate <= warn) return "warning";
    return "ok";
  };

  const hitRateBadge = () => {
    const status = hitRateStatus();
    if (status === "critical") return "bg-red-500/15 text-red-400 border border-red-500/30";
    if (status === "warning") return "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30";
    return "bg-green-500/15 text-green-400 border border-green-500/30";
  };

  const visibleKpis = filterByRole(kpis);
  const visibleActions = filterByRole(quickActions);
  const visibleActivity = filterByRole(recentActivity);

  return (
    <div className="flex h-full flex-col gap-6">
      <header className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Command Center</p>
            <h1 className="text-2xl font-semibold">Dashboard Home</h1>
          </div>
          <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30" data-testid="dashboard-status">
            Live Ops
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          A consolidated operational view across battles, approvals, and risk posture. Use the quick actions to jump into the most
          critical workflows.
        </p>
      </header>
      <ScrollArea className="flex-1">
        <div className="space-y-6 pr-2">
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {visibleKpis.map((kpi) => (
              <Link
                key={kpi.label}
                to={kpi.path}
                className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                data-testid={`dashboard-kpi-${kpi.label.toLowerCase().replace(/\s/g, '-')}`}
              >
                <Card className="border-border transition-colors hover:border-primary/50 hover:bg-muted/20">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">{kpi.label}</p>
                        <p className={`text-2xl font-semibold mt-2 ${kpi.color}`}>{kpi.value}</p>
                        <p className="text-xs text-muted-foreground mt-1">{kpi.change} vs last week</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/20">
                        <kpi.icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Card className="border-border" data-testid="dashboard-rag-status">
              <CardHeader>
                <CardTitle className="text-lg">RAG Quality Snapshot</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {ragLoading && <p className="text-sm text-muted-foreground">Loading RAG status...</p>}
                {!ragLoading && !ragSnapshot && (
                  <p className="text-sm text-muted-foreground">RAG telemetry not available.</p>
                )}
                {ragSnapshot && (
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Last Eval</p>
                      <p className="text-sm font-mono text-foreground">
                        {ragSnapshot.latest?.created_at || "—"}
                      </p>
                    </div>
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Cache Hit Rate</p>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-mono text-foreground">
                          {ragSnapshot.telemetry ? `${(ragSnapshot.telemetry.hit_rate * 100).toFixed(1)}%` : "—"}
                        </p>
                        {ragSnapshot.telemetry && (
                          <Badge className={hitRateBadge()}> {hitRateStatus().toUpperCase()} </Badge>
                        )}
                      </div>
                    </div>
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Regression Alerts</p>
                      <p className="text-sm font-mono text-foreground">
                        {ragSnapshot.alerts?.length ?? 0}
                      </p>
                    </div>
                  </div>
                )}
                <Button
                  variant="outline"
                  onClick={() => navigate("/rag-evaluation")}
                  data-testid="dashboard-rag-open"
                >
                  Review RAG Evaluation
                </Button>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Card className="border-border" data-testid="dashboard-quick-actions">
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                {visibleActions.map((action) => (
                  <Button
                    key={action.id}
                    variant="outline"
                    className={`justify-start gap-3 border ${actionStyles[action.intent]}`}
                    onClick={() => action.path && navigate(action.path)}
                    data-testid={`dashboard-action-${action.id}`}
                  >
                    <action.icon className="h-4 w-4" />
                    {action.label}
                  </Button>
                ))}
              </CardContent>
            </Card>
            <Card className="border-border" data-testid="dashboard-registry">
              <CardHeader>
                <CardTitle className="text-lg">Registry Snapshot</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className="border-border">
                    {registrySnapshot?.teams?.length || 0} teams
                  </Badge>
                  <Badge variant="outline" className="border-border">
                    {registrySnapshot?.agents?.length || 0} agents
                  </Badge>
                </div>
                <div className="space-y-2">
                  {(registrySnapshot?.delegation_preview || []).slice(0, 3).map((item) => (
                    <div key={item.agent_id} className="rounded-md border border-border bg-zinc-900/40 p-3">
                      <div className="text-sm font-medium text-white">{item.agent_name}</div>
                      <div className="text-xs text-muted-foreground">{item.role}</div>
                    </div>
                  ))}
                  {!registrySnapshot?.delegation_preview?.length && (
                    <div className="text-xs text-muted-foreground">Registry data not available.</div>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate("/agent-management")}
                  data-testid="dashboard-registry-manage"
                >
                  Manage Agents
                </Button>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
            <Card className="border-border" data-testid="dashboard-activity">
              <CardHeader>
                <CardTitle className="text-lg">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[280px]">
                  <div className="divide-y divide-border">
                    {visibleActivity.map((activity) => (
                      <div key={activity.id} className="flex items-center justify-between px-5 py-4">
                        <div>
                          <p className="text-sm font-medium">{activity.title}</p>
                          <p className="text-xs text-muted-foreground">{activity.meta}</p>
                        </div>
                        <Badge className={`border ${badgeStyles[activity.status]}`} data-testid={`dashboard-activity-${activity.id}`}>
                          {activity.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
};

export default DashboardHome;
