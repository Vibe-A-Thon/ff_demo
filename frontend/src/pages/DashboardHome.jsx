import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
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
  { id: "start-battle", label: "Start Battle", icon: Swords, intent: "red" },
  { id: "open-evidence", label: "Open Evidence", icon: FileSearch, intent: "gold" },
  { id: "review-diff", label: "Review Diff", icon: GitCompare, intent: "orange" },
  { id: "configure", label: "Configure", icon: Settings, intent: "white" },
];

const kpis = [
  { label: "Active Battles", value: 6, change: "+12%", trend: "up", icon: Activity, color: "text-blue-400" },
  { label: "Open Incidents", value: 3, change: "-25%", trend: "down", icon: ShieldAlert, color: "text-red-400" },
  { label: "Approvals Pending", value: 8, change: "+4%", trend: "up", icon: CheckCircle2, color: "text-green-400" },
  { label: "Time-to-Immunity", value: "3h 18m", change: "-18%", trend: "down", icon: Timer, color: "text-purple-400" },
];

const recentActivity = [
  {
    id: "activity-1",
    title: "RSB-492 merged into staging",
    meta: "Green Team • 12 minutes ago",
    status: "merged",
  },
  {
    id: "activity-2",
    title: "Incident INC-204 escalated to Purple",
    meta: "Blue Team • 45 minutes ago",
    status: "escalated",
  },
  {
    id: "activity-3",
    title: "Evidence pack exported for Case-1188",
    meta: "Gold Team • 2 hours ago",
    status: "exported",
  },
  {
    id: "activity-4",
    title: "RuleSpec v3.2 approved",
    meta: "Orange Team • 4 hours ago",
    status: "approved",
  },
];

const systemHealth = [
  { label: "Streaming latency", value: "68ms", status: "healthy" },
  { label: "Graph render SLA", value: "412ms", status: "healthy" },
  { label: "Replay coverage", value: "92%", status: "healthy" },
  { label: "Chaos resilience", value: "83%", status: "warning" },
];

const badgeStyles = {
  merged: "bg-green-500/15 text-green-400 border-green-500/20",
  escalated: "bg-red-500/15 text-red-400 border-red-500/20",
  exported: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  approved: "bg-blue-500/15 text-blue-400 border-blue-500/20",
};

const healthStyles = {
  healthy: "bg-green-500/15 text-green-400 border-green-500/20",
  warning: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
};

const DashboardHome = () => {
  const actionStyles = useMemo(
    () => ({
      red: "border-red-500/40 text-red-300 hover:bg-red-500/10",
      gold: "border-yellow-500/40 text-yellow-300 hover:bg-yellow-500/10",
      orange: "border-orange-500/40 text-orange-300 hover:bg-orange-500/10",
      white: "border-slate-200/40 text-slate-200 hover:bg-slate-200/10",
    }),
    []
  );

  return (
    <div className="space-y-6">
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

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="border-border" data-testid={`dashboard-kpi-${kpi.label.toLowerCase().replace(/\s/g, '-')}`}>
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
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card className="border-border" data-testid="dashboard-quick-actions">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {quickActions.map((action) => (
              <Button
                key={action.id}
                variant="outline"
                className={`justify-start gap-3 border ${actionStyles[action.intent]}`}
                data-testid={`dashboard-action-${action.id}`}
              >
                <action.icon className="h-4 w-4" />
                {action.label}
              </Button>
            ))}
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="dashboard-health">
          <CardHeader>
            <CardTitle className="text-lg">System Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {systemHealth.map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="text-xs text-muted-foreground">Operational SLA</p>
                </div>
                <Badge className={`border ${healthStyles[item.status]}`} data-testid={`dashboard-health-${item.label.toLowerCase().replace(/\s/g, '-')}`}>
                  {item.value}
                </Badge>
              </div>
            ))}
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
                {recentActivity.map((activity) => (
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

        <Card className="border-border" data-testid="dashboard-priority">
          <CardHeader>
            <CardTitle className="text-lg">Priority Focus</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Next approval gate</p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm">Release approval • RSB-492</p>
                  <p className="text-xs text-muted-foreground">TechManager required • 1h SLA</p>
                </div>
                <Badge className="bg-orange-500/15 text-orange-300 border border-orange-500/30">Gate 3</Badge>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Incident under watch</p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm">INC-204 • Account takeover surge</p>
                  <p className="text-xs text-muted-foreground">Escalated to Purple • 45m ago</p>
                </div>
                <Badge className="bg-red-500/15 text-red-300 border border-red-500/30">High</Badge>
              </div>
            </div>
            <Button variant="outline" className="w-full" data-testid="dashboard-view-queue">
              View Approval Queue
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
};

export default DashboardHome;
