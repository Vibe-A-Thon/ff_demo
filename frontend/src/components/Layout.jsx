import React, { useEffect, useMemo, useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { ScrollArea } from "../components/ui/scroll-area";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { battleAPI, evidenceAPI, ruleAPI, seedData, teamAPI, agentAPI } from "../lib/api";
import { useAuth, ROLE_DEFINITIONS } from "../contexts/AuthContext";
import { useAlerts } from "../contexts/AlertContext";
import { AlertHistoryPanel, ThresholdConfigPanel } from "./AlertPanels";
import CollaborationIndicator from "./CollaborationIndicator";
import KeyboardShortcutsOverlay from "./KeyboardShortcutsOverlay";
import HelpCenter from "./HelpCenter";
import OnboardingWizard from "./OnboardingWizard";
import FloatingHelp from "./FloatingHelp";
import ExplainabilityPanel from "./ExplainabilityPanel";
import { toast } from "sonner";
import {
  Swords,
  Brain,
  BarChart3,
  Package,
  GitCompare,
  FileSearch,
  FileText,
  FileCode,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Activity,
  Database,
  User,
  Users,
  ClipboardList,
  LogOut,
  Bell,
  Settings,
  PlayCircle,
  Crown,
  Shield,
  Wrench,
  Scale,
  Sparkles,
  RefreshCw,
  Info,
  Search,
  Plus,
  Crosshair,
} from "lucide-react";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: Activity, team: "blue" },
  { path: "/war-room", label: "War Room", icon: Swords, team: "red" },
  { path: "/war-practice", label: "War Practice", icon: Crosshair, team: "red" },
  { path: "/incidents", label: "Incident Timeline", icon: Bell, team: "red" },
  { path: "/battle-replay", label: "Battle Replay", icon: PlayCircle, team: "blue" },
  { path: "/brain-surgery", label: "Brain Surgery", icon: Brain, team: "purple" },
  { path: "/metrics", label: "Metrics", icon: BarChart3, team: "blue" },
  { path: "/taxonomy", label: "Fraud Taxonomy", icon: Database, team: "gold" },
  { path: "/rsb-manager", label: "RSB Manager", icon: Package, team: "green" },
  { path: "/diff-viewer", label: "Diff Viewer", icon: GitCompare, team: "orange" },
  { path: "/rules", label: "Rule Editor", icon: FileCode, team: "blue" },
  { path: "/approvals", label: "Approvals", icon: ShieldCheck, team: "green" },
  { path: "/evidence", label: "Evidence Packs", icon: FileSearch, team: "gold" },
  { path: "/teams", label: "Team Directory", icon: Users, team: "purple" },
  { path: "/agents", label: "Agent Management", icon: User, team: "purple" },
  { path: "/agent-queue", label: "Agent Task Queue", icon: ClipboardList, team: "purple" },
  { path: "/audit-logs", label: "Audit Logs", icon: FileText, team: "white" },
  { path: "/rag-console", label: "RAG Console", icon: Brain, team: "gold" },
  { path: "/settings", label: "Settings", icon: Settings, team: "white" },
  { path: "/users", label: "User Management", icon: Users, team: "white" },
];

const teamColors = {
  red: "border-red-500 text-red-400 hover:bg-red-500/10",
  blue: "border-blue-500 text-blue-400 hover:bg-blue-500/10",
  purple: "border-purple-500 text-purple-400 hover:bg-purple-500/10",
  green: "border-green-500 text-green-400 hover:bg-green-500/10",
  gold: "border-yellow-500 text-yellow-400 hover:bg-yellow-500/10",
  orange: "border-orange-500 text-orange-400 hover:bg-orange-500/10",
  white: "border-slate-200 text-slate-200 hover:bg-slate-200/10",
};

// Role-based access configuration
const ROLE_PERMISSIONS = {
  admin: ["*"],
  analyst: ["dashboard", "war-room", "war-practice", "brain-surgery", "metrics", "evidence", "battle-replay", "incidents", "taxonomy", "teams"],
  engineer: ["dashboard", "war-room", "war-practice", "brain-surgery", "metrics", "rsb-manager", "diff-viewer", "rules", "battle-replay", "agents", "taxonomy", "teams"],
  compliance: ["dashboard", "metrics", "evidence", "approvals", "battle-replay", "audit-logs", "teams"],
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


const Layout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [alertPanelOpen, setAlertPanelOpen] = useState(false);
  const [thresholdPanelOpen, setThresholdPanelOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [explainOpen, setExplainOpen] = useState(true);
  const [explainPayload, setExplainPayload] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [recentItems, setRecentItems] = useState([]);
  const [searchIndex, setSearchIndex] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isDemoUser, switchRole, roleDefinitions } = useAuth();
  const { unreadCount, criticalCount, currentPreset } = useAlerts();

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      if (event.key === "?" || (event.shiftKey && event.key === "/")) {
        event.preventDefault();
        setShortcutsOpen(true);
      }
      if (event.key.toLowerCase() === "h") {
        setHelpOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const handleContextExplain = (event) => {
      const target = event.target?.closest?.("[data-explain]");
      if (!target) return;

      event.preventDefault();
      const payload = {
        title: target.getAttribute("data-explain-title") || target.getAttribute("data-explain") || "Explain This",
        summary: target.getAttribute("data-explain-summary") || "Context-aware explanation generated for this action.",
        confidence: Number(target.getAttribute("data-explain-confidence")) || 0.84,
        triggeredRules: (target.getAttribute("data-explain-rules") || "R-ATO-001").split(","),
        evidence: (target.getAttribute("data-explain-evidence") || "Risk score elevated,Device mismatch").split(","),
        similarCases: (target.getAttribute("data-explain-similar") || "Case-1128,Case-1136").split(","),
      };
      setExplainPayload(payload);
      setExplainOpen(true);
    };

    document.addEventListener("contextmenu", handleContextExplain);
    return () => document.removeEventListener("contextmenu", handleContextExplain);
  }, []);

  useEffect(() => {
    const loadSearchIndex = async () => {
      setSearchLoading(true);
      try {
        const [battleRes, ruleRes, evidenceRes, teamRes, agentRes] = await Promise.all([
          battleAPI.getAll(),
          ruleAPI.getAll(),
          evidenceAPI.getAll(),
          teamAPI.getAll(),
          agentAPI.getAll(),
        ]);
        const battles = (battleRes?.data || []).map((battle) => ({
          id: `battle-${battle.id}`,
          label: battle.scenario_name || "Battle",
          subtitle: `Battle • ${battle.status || "unknown"}`,
          path: "/war-room",
          type: "battle",
        }));
        const teams = (teamRes?.data || []).map((team) => ({
          id: `team-${team.team_id}`,
          label: team.bank_facing_name || team.internal_name || "Team",
          subtitle: `Team • ${team.team_id}`,
          path: "/teams",
          type: "team",
        }));
        const agents = (agentRes?.data || []).map((agent) => ({
          id: `agent-${agent.agent_id}`,
          label: agent.agent_name || "Agent",
          subtitle: `Agent • ${agent.team_id || "team"}`,
          path: "/agents",
          type: "agent",
        }));
        const rules = (ruleRes?.data || []).map((rule) => ({
          id: `rule-${rule.id}`,
          label: rule.name || "Rule",
          subtitle: `Rule • ${rule.rule_type || "policy"}`,
          path: "/rules",
          type: "rule",
        }));
        const evidence = (evidenceRes?.data || []).map((pack) => ({
          id: `evidence-${pack.id}`,
          label: pack.name || `Evidence ${pack.id}`,
          subtitle: "Evidence Pack",
          path: "/evidence",
          type: "evidence",
        }));
        setSearchIndex([...battles, ...rules, ...evidence, ...teams, ...agents]);
      } catch (error) {
        setSearchIndex([]);
      } finally {
        setSearchLoading(false);
      }
    };

    loadSearchIndex();
  }, []);

  useEffect(() => {
    const currentItem = navItems.find((item) => item.path === location.pathname);
    if (!currentItem) return;
    setRecentItems((prev) => {
      const filtered = prev.filter((item) => item.path !== currentItem.path);
      return [currentItem, ...filtered].slice(0, 4);
    });
  }, [location.pathname]);

  const breadcrumbSegments = location.pathname.split("/").filter(Boolean);
  const breadcrumbItems = breadcrumbSegments.map((segment, index) => {
    const path = `/${breadcrumbSegments.slice(0, index + 1).join("/")}`;
    const navItem = navItems.find((item) => item.path === path);
    return {
      label: navItem?.label || segment.replace(/-/g, " "),
      path,
    };
  });

  const isPathAccessible = (path) => {
    if (!user || !path) return false;
    const routeKey = path.startsWith("/") ? path.slice(1) : path;
    return hasAccess(user.role, routeKey);
  };

  const visibleNavItems = user ? navItems.filter((item) => isPathAccessible(item.path)) : [];
  const searchPool = user
    ? [...visibleNavItems, ...searchIndex.filter((item) => !item.path || isPathAccessible(item.path))]
    : [];
  const searchResults = searchQuery
    ? searchPool.filter((item) => {
        const target = `${item.label} ${item.subtitle || ""}`.toLowerCase();
        return target.includes(searchQuery.toLowerCase());
      })
    : recentItems;

  const getSearchIcon = (item) => {
    if (item.icon) return item.icon;
    if (item.type === "battle") return Swords;
    if (item.type === "rule") return FileCode;
    if (item.type === "evidence") return FileSearch;
    return Sparkles;
  };

  const handleSearchSelect = (path) => {
    navigate(path);
    setSearchQuery("");
    setSearchOpen(false);
  };

  const handleSearchBlur = () => {
    window.setTimeout(() => setSearchOpen(false), 150);
  };

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

  const routeExplainability = {
    "/war-room": {
      title: "War Room Explainability",
      summary: "Live decisioning, reasoning streams, and battle outcomes explained in context.",
      confidence: 0.89,
      triggeredRules: ["R-ATO-001", "R-VELOCITY-004"],
      evidence: ["Anomalous device", "Burst transfers", "Behavior deviation"],
      similarCases: ["Case-1128", "Case-2214"],
      contradictions: [
        {
          id: "war-room-contradiction",
          title: "Policy override",
          detail: "Manual override conflicts with automated block recommendation.",
          severity: "high",
        },
      ],
      learningContext: {
        summary: "Battle telemetry feeds Purple Team for rule hardening.",
        impact: "Expected to improve detection latency by 8% in next cycle.",
        nextActions: ["Escalate to strategy backlog", "Capture additional evidence traces"],
      },
      audienceViews: {
        regulator: "All decisions logged with evidence chain and SoD gates.",
        customer: "We protected your account by stopping unusual activity.",
        investigator: "Triggered velocity and device mismatch rules with confidence 0.89.",
      },
    },
    "/rules": {
      title: "Rule Editor Explainability",
      summary: "Rule changes are validated against compliance and test evidence.",
      confidence: 0.83,
      triggeredRules: ["COM-010", "TEST-004"],
      evidence: ["RuleSpec form", "Test results", "Policy checks"],
      similarCases: ["Rule-208", "Rule-219"],
      contradictions: [],
      learningContext: {
        summary: "Edits update the learning baseline and improve future detection coverage.",
        impact: "Projected false-positive reduction of 4%.",
        nextActions: ["Run edge-case suite", "Monitor post-deploy drift"],
      },
      audienceViews: {
        regulator: "Change control logged with approvals and audits.",
        customer: "Updated rules protect customers with minimal friction.",
        investigator: "RuleSpec updates tracked with version history and evidence.",
      },
    },
  };

  const explainContext = routeExplainability[location.pathname] || {
    title: "Global Explainability",
    summary: "Context-aware explanations for decisions, evidence, and audit trails.",
    confidence: 0.82,
    triggeredRules: ["R-DEFAULT-001"],
    evidence: ["Operational telemetry", "Audit trail", "Policy checks"],
    similarCases: ["Case-1002", "Case-1019"],
    contradictions: [],
    learningContext: {
      summary: "Signals from this screen feed future model and rule improvements.",
      impact: "Improves decision consistency across teams.",
      nextActions: ["Capture additional outcomes", "Review contradictory signals"],
    },
    audienceViews: {
      regulator: "Evidence chain preserved with immutable logs.",
      customer: "Decisions explained with clear, human language.",
      investigator: "Evidence and rules are traceable for post-incident review.",
    },
  };

  const commentorContext = useMemo(() => {
    const base = explainPayload || explainContext;
    const highlights = [
      ...(base.triggeredRules || []),
      ...(base.evidence || []),
    ].filter(Boolean);
    return {
      screen: base.title || "Global Explainability",
      role: user?.role || "analyst",
      summary: base.summary,
      highlights,
    };
  }, [explainPayload, explainContext, user?.role]);

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
            {visibleNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                const teamClass = teamColors[item.team];
                const routeKey = item.path.slice(1);
                const navLinkContent = (
                  <>
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!collapsed && <span className="flex-1">{item.label}</span>}
                  </>
                );

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
      <main className="flex-1 overflow-hidden flex flex-col" data-testid="main-content">
        <div className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-card/80 px-6 py-3 backdrop-blur">
          <div className="flex flex-col gap-1">
            <CollaborationIndicator />
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <NavLink to="/war-room" className="hover:text-foreground">Home</NavLink>
              {breadcrumbItems.map((item, idx) => (
                <React.Fragment key={item.path}>
                  <ChevronRight className="h-3 w-3" />
                  {idx === breadcrumbItems.length - 1 ? (
                    <span className="text-foreground font-medium capitalize">{item.label}</span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleSearchSelect(item.path)}
                      className="hover:text-foreground capitalize"
                    >
                      {item.label}
                    </button>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="relative w-[320px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              onFocus={() => setSearchOpen(true)}
              onBlur={handleSearchBlur}
              placeholder="Global search (battles, rules, evidence)"
              className="pl-9"
              data-testid="global-search"
            />
            {searchOpen && (searchQuery || recentItems.length > 0 || searchLoading) && (
              <div className="absolute left-0 right-0 mt-2 rounded-lg border border-border bg-card shadow-xl">
                <div className="px-3 py-2 text-[11px] uppercase text-muted-foreground">
                  {searchQuery ? "Results" : "Recent"}
                </div>
                <div className="max-h-48 overflow-auto">
                  {searchLoading ? (
                    <div className="px-3 py-3 text-sm text-muted-foreground">Indexing data...</div>
                  ) : searchResults.length > 0 ? (
                    searchResults.map((item) => (
                      <button
                        key={item.id || item.path}
                        type="button"
                        onMouseDown={() => handleSearchSelect(item.path)}
                        className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-zinc-800"
                      >
                        {(() => {
                          const Icon = getSearchIcon(item);
                          return <Icon className="h-4 w-4 text-blue-400" />;
                        })()}
                        <div className="text-left">
                          <div>{item.label}</div>
                          {item.subtitle && (
                            <div className="text-xs text-muted-foreground">{item.subtitle}</div>
                          )}
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="px-3 py-3 text-sm text-muted-foreground">No matches found.</div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShortcutsOpen(true)}
              data-testid="open-shortcuts-btn"
            >
              <Info className="h-4 w-4 mr-2" />
              Shortcuts
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setExplainPayload(null);
                setExplainOpen((prev) => !prev);
              }}
              data-testid="open-explain-btn"
            >
              <Shield className="h-4 w-4 mr-2" />
              {explainOpen ? "Hide Explain" : "Show Explain"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setHelpOpen(true)}
              data-testid="open-help-btn"
            >
              <Settings className="h-4 w-4 mr-2" />
              Help
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <Outlet />
        </div>

        <div className="fixed bottom-6 right-6 z-30">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button className="rounded-full h-12 w-12 p-0 neon-border" data-testid="fab-menu">
                <Plus className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Quick Actions</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleSearchSelect("/war-room")}>New Battle</DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleSearchSelect("/rules")}>Create Rule</DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleSearchSelect("/approvals")}>Request Approval</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </main>

      {/* Global Explainability Panel */}
      <aside className={`border-l border-border bg-card w-[360px] ${explainOpen ? "flex" : "hidden"}`} data-testid="explainability-sidenav">
        <ExplainabilityPanel
          open={explainOpen}
          onOpenChange={setExplainOpen}
          payload={explainPayload || explainContext}
          commentorContext={commentorContext}
        />
      </aside>

      {/* Alert History Panel */}
      <AlertHistoryPanel open={alertPanelOpen} onOpenChange={setAlertPanelOpen} />

      {/* Threshold Configuration Panel */}
      <ThresholdConfigPanel open={thresholdPanelOpen} onOpenChange={setThresholdPanelOpen} />

      <KeyboardShortcutsOverlay open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
      <HelpCenter open={helpOpen} onOpenChange={setHelpOpen} />
      <OnboardingWizard />
      <FloatingHelp onOpen={() => setHelpOpen(true)} />
      {/* Explainability panel rendered in right sidenav */}
    </div>
  );
};

export default Layout;
