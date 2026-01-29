import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { ScrollArea } from "../components/ui/scroll-area";
import { FileText, Download, Filter } from "lucide-react";

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

  const filteredLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const matchesSearch = `${log.actor} ${log.action} ${log.resource}`.toLowerCase().includes(search.toLowerCase());
      const matchesAction = actionFilter === "all" || log.action === actionFilter;
      const matchesStatus = statusFilter === "all" || log.status === statusFilter;
      return matchesSearch && matchesAction && matchesStatus;
    });
  }, [search, actionFilter, statusFilter]);

  return (
    <div className="space-y-6">
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
  );
};

export default AuditLogViewer;
