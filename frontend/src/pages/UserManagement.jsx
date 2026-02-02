import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { ScrollArea } from "../components/ui/scroll-area";
import { UserPlus, Shield, KeyRound, Ban } from "lucide-react";

const users = [
  { id: "user-01", name: "Avery Jones", email: "techlead@bank.com", role: "TechLead", status: "active" },
  { id: "user-02", name: "Jordan Lee", email: "operator@bank.com", role: "Fraud Operator", status: "active" },
  { id: "user-03", name: "Robin Patel", email: "auditor@bank.com", role: "Auditor", status: "active" },
  { id: "user-04", name: "Taylor Kim", email: "developer@bank.com", role: "Dev/Test", status: "suspended" },
  { id: "user-05", name: "Morgan Chen", email: "manager@bank.com", role: "TechManager", status: "active" },
];

const statusStyles = {
  active: "bg-green-500/15 text-green-400 border-green-500/20",
  suspended: "bg-red-500/15 text-red-400 border-red-500/20",
};

const UserManagement = () => {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      const matchesSearch = `${user.name} ${user.email}`.toLowerCase().includes(search.toLowerCase());
      const matchesRole = roleFilter === "all" || user.role === roleFilter;
      const matchesStatus = statusFilter === "all" || user.status === statusFilter;
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [search, roleFilter, statusFilter]);

  return (
    <div className="flex h-full flex-col gap-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Governance</p>
            <h1 className="text-2xl font-semibold">User Management</h1>
          </div>
          <Button className="gap-2" data-testid="user-add">
            <UserPlus className="h-4 w-4" />
            Invite User
          </Button>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Manage platform access, assign roles, and enforce separation of duties for every fraud defense workflow.
        </p>
      </header>
      <ScrollArea className="flex-1">
        <div className="space-y-6 pr-2">
          <Card className="border-border" data-testid="user-filters">
            <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center">
              <div className="flex-1">
                <Input
                  placeholder="Search users by name or email"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  data-testid="user-search"
                />
              </div>
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-full md:w-[200px]" data-testid="user-filter-role">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  <SelectItem value="TechLead">TechLead</SelectItem>
                  <SelectItem value="Fraud Operator">Fraud Operator</SelectItem>
                  <SelectItem value="Auditor">Auditor</SelectItem>
                  <SelectItem value="Dev/Test">Dev/Test</SelectItem>
                  <SelectItem value="TechManager">TechManager</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-[200px]" data-testid="user-filter-status">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card className="border-border" data-testid="user-table">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-4 w-4 text-blue-400" />
                Active Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell className="text-muted-foreground">{user.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-border" data-testid={`user-role-${user.id}`}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`border ${statusStyles[user.status]}`} data-testid={`user-status-${user.id}`}>
                          {user.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="outline" size="sm" data-testid={`user-reset-${user.id}`}>
                            <KeyRound className="mr-1 h-3.5 w-3.5" />
                            Reset MFA
                          </Button>
                          <Button variant="outline" size="sm" data-testid={`user-disable-${user.id}`}>
                            <Ban className="mr-1 h-3.5 w-3.5" />
                            {user.status === "active" ? "Suspend" : "Activate"}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
};

export default UserManagement;
