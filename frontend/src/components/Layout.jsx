import React, { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { ScrollArea } from "../components/ui/scroll-area";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../components/ui/dropdown-menu";
import { seedData } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { useAlerts } from "../contexts/AlertContext";
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
} from "lucide-react";

const navItems = [
  { path: "/war-room", label: "War Room", icon: Swords, team: "red" },
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

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { alerts } = useAlerts();

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

  const unreadAlerts = alerts.filter(a => a.type === 'critical').length;

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

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="space-y-1 px-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              const teamClass = teamColors[item.team];

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.path.slice(1)}`}
                  className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all border-l-2 ${
                    isActive
                      ? `bg-zinc-800 ${teamClass.split(" ")[0]} ${teamClass.split(" ")[1]}`
                      : `border-transparent text-muted-foreground hover:text-foreground ${teamClass.split(" ").slice(2).join(" ")}`
                  }`}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Seed Data Button */}
        <div className="border-t border-border p-4">
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
    </div>
  );
};

export default Layout;
