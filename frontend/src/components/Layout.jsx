import React, { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { ScrollArea } from "../components/ui/scroll-area";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip";
import { seedData } from "../lib/api";
import { useAuth, ROLE_DEFINITIONS } from "../contexts/AuthContext";
import { useAlerts } from "../contexts/AlertContext";
import { AlertHistoryPanel, ThresholdConfigPanel } from "./AlertPanels";
import { toast } from "sonner";
import {
  Swords,
  Brain,
  BarChart3,
  Package,
  GitCompare,
  FileSearch,
  FileCode,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Activity,
  Database,
  User,
  LogOut,
  Bell,
  Settings,
  PlayCircle,
  Lock,
  Crown,
  Shield,
  Wrench,
  Scale,
  Sparkles,
  RefreshCw,
  Info,
} from "lucide-react";

const navItems = [
  { path: "/war-room", label: "War Room", icon: Swords, team: "red" },
  { path: "/battle-replay", label: "Battle Replay", icon: PlayCircle, team: "blue" },
  { path: "/brain-surgery", label: "Brain Surgery", icon: Brain, team: "purple" },
  { path: "/metrics", label: "Metrics", icon: BarChart3, team: "blue" },
  { path: "/rsb-manager", label: "RSB Manager", icon: Package, team: "green" },
  { path: "/diff-viewer", label: "Diff Viewer", icon: GitCompare, team: "orange" },
  { path: "/evidence", label: "Evidence Packs", icon: FileSearch, team: "gold" },
  { path: "/rules", label: "Rule Editor", icon: FileCode, team: "blue" },
  { path: "/approvals", label: "Approvals", icon: ShieldCheck, team: "green" },
];

const teamColors = {
  red: "border-red-500 text-red-400 hover:bg-red-500/10",
  blue: "border-blue-500 text-blue-400 hover:bg-blue-500/10",
  purple: "border-purple-500 text-purple-400 hover:bg-purple-500/10",
  green: "border-green-500 text-green-400 hover:bg-green-500/10",
  gold: "border-yellow-500 text-yellow-400 hover:bg-yellow-500/10",
  orange: "border-orange-500 text-orange-400 hover:bg-orange-500/10",
};

// Role-based access configuration
const ROLE_PERMISSIONS = {
  admin: ["*"],
  analyst: ["war-room", "brain-surgery", "metrics", "evidence", "battle-replay"],
  engineer: ["war-room", "brain-surgery", "metrics", "rsb-manager", "diff-viewer", "rules", "battle-replay"],
  compliance: ["metrics", "evidence", "approvals", "battle-replay"],
};

const ROLE_ICONS = {
  admin: Crown,
  analyst: Shield,
  engineer: Wrench,
  compliance: Scale,
};

const hasAccess = (userRole, routePath) => {
  const permissions = ROLE_PERMISSIONS[userRole] || [];
  if (permissions.includes("*")) return true;
  return permissions.includes(routePath);
};

// Get roles that have access to a specific route
const getRolesWithAccess = (routePath) => {
  const rolesWithAccess = [];
  Object.entries(ROLE_PERMISSIONS).forEach(([role, permissions]) => {
    if (permissions.includes("*") || permissions.includes(routePath)) {
      rolesWithAccess.push(role);
    }
  });
  return rolesWithAccess;
};

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [alertPanelOpen, setAlertPanelOpen] = useState(false);
  const [thresholdPanelOpen, setThresholdPanelOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isDemoUser, switchRole, roleDefinitions } = useAuth();
  const { unreadCount, criticalCount, currentPreset } = useAlerts();

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      await seedData();
      toast.success("Demo data seeded successfully!");
    } catch (error) {
      toast.error("Failed to seed data");
    } finally {
      setSeeding(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
    toast.success("Logged out successfully");
  };

  const handleRoleSwitch = (newRole) => {
    switchRole(newRole);
    toast.success(
      <div className="flex items-center gap-2">
        <RefreshCw className="h-4 w-4" />
        <span>Switched to <strong>{roleDefinitions[newRole]?.label}</strong> role</span>
      </div>
    );
  };

  const RoleIcon = user?.role ? ROLE_ICONS[user.role] : User;

  return (
    <div className="flex h-screen bg-background" data-testid="layout-container">
      {/* Sidebar */}
      <aside
        className={`${
          collapsed ? "w-16" : "w-64"
        } flex flex-col border-r border-border bg-card transition-all duration-300`}
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-blue-500" />
              <span className="text-lg font-bold tracking-tight">Fraud Forge</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8"
            data-testid="sidebar-toggle"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        {/* User Info */}
        {!collapsed && user && (
          <div className="p-4 border-b border-border">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start gap-3 h-auto py-2" data-testid="user-menu-btn">
                  <div className={`w-8 h-8 rounded-full ${roleDefinitions[user.role]?.bgColor || 'bg-blue-500/20'} flex items-center justify-center`}>
                    <RoleIcon className={`h-4 w-4 ${roleDefinitions[user.role]?.color || 'text-blue-400'}`} />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{user.name}</p>
                      {isDemoUser && (
                        <Badge className="bg-purple-500/20 text-purple-400 text-[10px] px-1.5 py-0">
                          <Sparkles className="h-2.5 w-2.5 mr-0.5" />
                          DEMO
                        </Badge>
                      )}
                    </div>
                    <p className={`text-xs ${roleDefinitions[user.role]?.color || 'text-muted-foreground'}`}>
                      {roleDefinitions[user.role]?.label || user.role}
                    </p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-64">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="h-4 w-4 mr-2" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setThresholdPanelOpen(true)}>
                  <Settings className="h-4 w-4 mr-2" />
                  Alert Settings
                  <Badge variant="outline" className="ml-auto text-xs capitalize">{currentPreset}</Badge>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setAlertPanelOpen(true)}>
                  <Bell className="h-4 w-4 mr-2" />
                  Notifications
                  {unreadCount > 0 && (
                    <Badge className={`ml-auto ${criticalCount > 0 ? 'bg-red-500' : 'bg-blue-500'} text-white`}>
                      {unreadCount}
                    </Badge>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-400" data-testid="logout-btn">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Demo User Role Switcher */}
            {isDemoUser && (
              <div className="mt-3 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                  <span className="text-xs font-medium text-purple-400">Demo Role Switcher</span>
                </div>
                <Select value={user.role} onValueChange={handleRoleSwitch}>
                  <SelectTrigger className="h-9" data-testid="demo-role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(roleDefinitions).map(([roleKey, roleDef]) => {
                      const Icon = ROLE_ICONS[roleKey];
                      return (
                        <SelectItem key={roleKey} value={roleKey}>
                          <div className="flex items-center gap-2">
                            <Icon className={`h-4 w-4 ${roleDef.color}`} />
                            <div>
                              <span className="font-medium">{roleDef.label}</span>
                              <p className="text-xs text-muted-foreground">{roleDef.description}</p>
                            </div>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="space-y-1 px-2">
            <TooltipProvider delayDuration={200}>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                const teamClass = teamColors[item.team];
                const routeKey = item.path.slice(1);
                const canAccess = user ? hasAccess(user.role, routeKey) : false;
                const rolesWithAccess = getRolesWithAccess(routeKey);

                const navLinkContent = (
                  <>
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!collapsed && (
                      <>
                        <span className="flex-1">{item.label}</span>
                        {!canAccess && <Lock className="h-3 w-3 text-muted-foreground" />}
                      </>
                    )}
                  </>
                );

                // Show tooltip only for locked items when sidebar is expanded
                if (!canAccess && !collapsed) {
                  return (
                    <Tooltip key={item.path}>
                      <TooltipTrigger asChild>
                        <NavLink
                          to={item.path}
                          data-testid={`nav-${routeKey}`}
                          className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all border-l-2 ${
                            isActive
                              ? `bg-zinc-800 ${teamClass.split(" ")[0]} ${teamClass.split(" ")[1]}`
                              : `border-transparent text-muted-foreground/50 ${teamClass.split(" ").slice(2).join(" ")}`
                          } opacity-50 cursor-pointer`}
                        >
                          {navLinkContent}
                        </NavLink>
                      </TooltipTrigger>
                      <TooltipContent 
                        side="right" 
                        sideOffset={8}
                        className="max-w-[280px] p-3 z-50" 
                        data-testid={`tooltip-${routeKey}`}
                      >
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Lock className="h-4 w-4 text-yellow-400" />
                            <span className="font-semibold text-yellow-400">Access Restricted</span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Your current role (<span className="font-medium">{ROLE_DEFINITIONS[user?.role]?.label || user?.role}</span>) doesn't have access to <span className="font-medium">{item.label}</span>.
                          </p>
                          <div className="pt-2 border-t border-border">
                            <p className="text-xs text-muted-foreground mb-2">Roles with access:</p>
                            <div className="flex flex-wrap gap-1.5">
                              {rolesWithAccess.map(role => {
                                const RoleIcon = ROLE_ICONS[role];
                                const roleDef = ROLE_DEFINITIONS[role];
                                return (
                                  <div 
                                    key={role} 
                                    className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs border ${roleDef?.bgColor || 'bg-zinc-800'} border-current/20`}
                                  >
                                    <RoleIcon className={`h-3 w-3 ${roleDef?.color || 'text-muted-foreground'}`} />
                                    <span className={roleDef?.color || 'text-muted-foreground'}>{roleDef?.label || role}</span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                          {isDemoUser && (
                            <div className="pt-2 border-t border-border">
                              <p className="text-xs text-purple-400 flex items-center gap-1">
                                <Sparkles className="h-3 w-3" />
                                Use the Demo Role Switcher to change roles
                              </p>
                            </div>
                          )}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                // Regular nav link for accessible items
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    data-testid={`nav-${routeKey}`}
                    className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all border-l-2 ${
                      isActive
                        ? `bg-zinc-800 ${teamClass.split(" ")[0]} ${teamClass.split(" ")[1]}`
                        : `border-transparent text-muted-foreground hover:text-foreground ${teamClass.split(" ").slice(2).join(" ")}`
                    }`}
                  >
                    {navLinkContent}
                  </NavLink>
                );
              })}
            </TooltipProvider>
          </nav>
        </ScrollArea>

        {/* Alert Status & Seed Button */}
        <div className="border-t border-border p-4 space-y-3">
          {/* Alert Status */}
          {!collapsed && (
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-between"
              onClick={() => setAlertPanelOpen(true)}
              data-testid="open-alerts-btn"
            >
              <span className="flex items-center gap-2">
                <Bell className={`h-4 w-4 ${criticalCount > 0 ? 'text-red-400' : ''}`} />
                Alerts
              </span>
              {unreadCount > 0 && (
                <Badge className={`${criticalCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-blue-500'} text-white`}>
                  {unreadCount}
                </Badge>
              )}
            </Button>
          )}

          {/* Seed Data Button */}
          <Button
            variant="outline"
            size={collapsed ? "icon" : "sm"}
            onClick={handleSeedData}
            disabled={seeding}
            className="w-full"
            data-testid="seed-data-btn"
          >
            <Database className={`h-4 w-4 ${collapsed ? "" : "mr-2"}`} />
            {!collapsed && (seeding ? "Seeding..." : "Seed Demo Data")}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden" data-testid="main-content">
        <Outlet />
      </main>

      {/* Alert History Panel */}
      <AlertHistoryPanel open={alertPanelOpen} onOpenChange={setAlertPanelOpen} />

      {/* Threshold Configuration Panel */}
      <ThresholdConfigPanel open={thresholdPanelOpen} onOpenChange={setThresholdPanelOpen} />
    </div>
  );
};

export default Layout;
