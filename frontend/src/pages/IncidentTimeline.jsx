import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { ScrollArea } from "../components/ui/scroll-area";
import { Clock, AlertTriangle, ArrowRight, Plus, ShieldAlert } from "lucide-react";

const incidents = [
  {
    id: "INC-204",
    title: "Account takeover surge",
    severity: "high",
    status: "escalated",
    owner: "Blue Team",
    timestamp: "45m ago",
    notes: "Spike in device mismatch and geo anomalies across 3 regions.",
  },
  {
    id: "INC-199",
    title: "Wire diversion pattern",
    severity: "medium",
    status: "contained",
    owner: "Purple Team",
    timestamp: "2h ago",
    notes: "RuleSpec v3.2 deployed to halt invoice redirection attempts.",
  },
  {
    id: "INC-187",
    title: "ACH mule network",
    severity: "critical",
    status: "open",
    owner: "Black Team",
    timestamp: "6h ago",
    notes: "Simulation indicates 12% evasion rate under new velocity thresholds.",
  },
  {
    id: "INC-175",
    title: "P2P first-payment fraud",
    severity: "low",
    status: "resolved",
    owner: "Gold Team",
    timestamp: "1d ago",
    notes: "Evidence pack finalized and sent to compliance.",
  },
];

const severityStyles = {
  critical: "bg-red-500/15 text-red-400 border-red-500/20",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  low: "bg-green-500/15 text-green-400 border-green-500/20",
};

const statusStyles = {
  open: "bg-red-500/15 text-red-400 border-red-500/20",
  escalated: "bg-purple-500/15 text-purple-400 border-purple-500/20",
  contained: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  resolved: "bg-green-500/15 text-green-400 border-green-500/20",
};

const IncidentTimeline = () => {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const matchesSeverity = severityFilter === "all" || incident.severity === severityFilter;
      const matchesStatus = statusFilter === "all" || incident.status === statusFilter;
      return matchesSeverity && matchesStatus;
    });
  }, [severityFilter, statusFilter]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Operations</p>
            <h1 className="text-2xl font-semibold">Incident Timeline</h1>
          </div>
          <Button className="gap-2" data-testid="incident-create">
            <Plus className="h-4 w-4" />
            New Incident
          </Button>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Track active incidents, escalation paths, and resolution checkpoints. Each event ties back to evidence packs and approvals.
        </p>
      </header>

      <Card className="border-border" data-testid="incident-filters">
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger className="w-full md:w-[200px]" data-testid="incident-filter-severity">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severity</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full md:w-[200px]" data-testid="incident-filter-status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="escalated">Escalated</SelectItem>
              <SelectItem value="contained">Contained</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" data-testid="incident-export">
            Export Timeline
          </Button>
        </CardContent>
      </Card>

      <Card className="border-border" data-testid="incident-timeline">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-red-400" />
            Live Incident Feed
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[480px]">
            <div className="relative divide-y divide-border">
              {filteredIncidents.map((incident, index) => (
                <div key={incident.id} className="px-5 py-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <Badge className={`border ${severityStyles[incident.severity]}`}>{incident.severity}</Badge>
                        <span className="text-sm font-semibold">{incident.id}</span>
                        <Badge className={`border ${statusStyles[incident.status]}`}>{incident.status}</Badge>
                      </div>
                      <p className="text-sm font-medium">{incident.title}</p>
                      <p className="text-xs text-muted-foreground">{incident.notes}</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <Clock className="h-3.5 w-3.5" />
                      {incident.timestamp}
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <AlertTriangle className="h-3.5 w-3.5 text-orange-400" />
                    Owner: {incident.owner}
                    <ArrowRight className="h-3.5 w-3.5" />
                    Evidence Pack linked
                  </div>
                  {index < filteredIncidents.length - 1 && (
                    <div className="mt-4 h-px bg-border" />
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default IncidentTimeline;
