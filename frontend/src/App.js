import React, { useEffect, useState, Suspense, lazy } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import ErrorBoundary from "./components/ErrorBoundary";
import SplashScreen from "./components/SplashScreen";

// Contexts
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AlertProvider } from "./contexts/AlertContext";

// Layout
import Layout from "./components/Layout";

// Pages (lazy-loaded for smaller initial bundle)
const Login = lazy(() => import("./pages/Login"));
const WarRoom = lazy(() => import("./pages/WarRoom"));
const BrainSurgery = lazy(() => import("./pages/BrainSurgery"));
const MetricsDashboard = lazy(() => import("./pages/MetricsDashboard"));
const RSBManager = lazy(() => import("./pages/RSBManager"));
const DifferenceVisualizer = lazy(() => import("./pages/DifferenceVisualizer"));
const EvidenceViewer = lazy(() => import("./pages/EvidenceViewer"));
const RuleEditor = lazy(() => import("./pages/RuleEditor"));
const Approvals = lazy(() => import("./pages/Approvals"));
const BattleReplay = lazy(() => import("./pages/BattleReplay"));
const WarPractice = lazy(() => import("./pages/WarPractice"));
const DashboardHome = lazy(() => import("./pages/DashboardHome"));
const AgentManagement = lazy(() => import("./pages/AgentManagement"));
const AgentTaskQueue = lazy(() => import("./pages/AgentTaskQueue"));
const TeamDirectory = lazy(() => import("./pages/TeamDirectory"));
const FraudTaxonomyBrowser = lazy(() => import("./pages/FraudTaxonomyBrowser"));
const IncidentTimeline = lazy(() => import("./pages/IncidentTimeline"));
const AuditLogViewer = lazy(() => import("./pages/AuditLogViewer"));
const SettingsConfiguration = lazy(() => import("./pages/SettingsConfiguration"));
const UserManagement = lazy(() => import("./pages/UserManagement"));
const RAGConsole = lazy(() => import("./pages/RAGConsole"));
const Neo4jSyncDashboard = lazy(() => import("./pages/Neo4jSyncDashboard"));
const RAGEvaluationDashboard = lazy(() => import("./pages/RAGEvaluationDashboard"));
const LLMProviderSetup = lazy(() => import("./pages/LLMProviderSetup"));
const AmcManager = lazy(() => import("./pages/AmcManager"));
const PEPManager = lazy(() => import("./pages/PEPManager"));
const AMCExplorer = lazy(() => import("./components/AMCExplorer"));

// Role-based access configuration
const ROLE_PERMISSIONS = {
  admin: ["*"], // Access to everything
  analyst: ["dashboard", "war-room", "war-practice", "brain-surgery", "metrics", "evidence", "battle-replay", "incidents", "taxonomy", "teams", "rag-console", "rag-evaluation", "agent-queue", "neo4j-sync", "llm-setup", "amc-manager"],
  engineer: ["dashboard", "war-room", "war-practice", "brain-surgery", "metrics", "rsb-manager", "diff-viewer", "rules", "battle-replay", "agents", "taxonomy", "teams", "rag-console", "rag-evaluation", "agent-queue", "neo4j-sync", "llm-setup", "amc-manager"],
  compliance: ["dashboard", "metrics", "evidence", "approvals", "battle-replay", "audit-logs", "teams", "rag-console", "rag-evaluation", "agent-queue", "neo4j-sync", "llm-setup", "amc-manager"],
};

// Check if user has access to a route
const hasAccess = (userRole, routePath) => {
  const permissions = ROLE_PERMISSIONS[userRole] || [];
  if (permissions.includes("*")) return true;
  return permissions.includes(routePath);
};

// Protected Route Component with Role Check
const ProtectedRoute = ({ children, requiredRoute = null }) => {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check role-based access if route specified
  if (requiredRoute && user && !hasAccess(user.role, requiredRoute)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Access Denied</h2>
          <p className="text-muted-foreground mb-4">
            Your role ({user.role}) doesn't have permission to access this page.
          </p>
          <a href="/war-room" className="text-blue-400 hover:underline">
            Return to War Room
          </a>
        </div>
      </div>
    );
  }
  
  return children;
};

// Public Route (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Role-gated page wrapper
const RoleGate = ({ children, route }) => {
  const { user } = useAuth();
  
  if (!user || !hasAccess(user.role, route)) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-yellow-400 mb-2">Restricted Access</h2>
          <p className="text-sm text-muted-foreground">
            This feature requires {route.replace(/-/g, ' ')} permissions.
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Contact your administrator to request access.
          </p>
        </div>
      </div>
    );
  }
  
  return children;
};

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-background">
    <div className="text-center">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-muted-foreground">Loading...</p>
    </div>
  </div>
);

const SuspenseRoute = ({ children }) => (
  <Suspense fallback={<PageLoader />}>{children}</Suspense>
);

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <SuspenseRoute>
                <Login />
              </SuspenseRoute>
            </PublicRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<RoleGate route="dashboard"><SuspenseRoute><DashboardHome /></SuspenseRoute></RoleGate>} />
          <Route path="war-room" element={<RoleGate route="war-room"><SuspenseRoute><WarRoom /></SuspenseRoute></RoleGate>} />
          <Route path="war-practice" element={<RoleGate route="war-practice"><SuspenseRoute><WarPractice /></SuspenseRoute></RoleGate>} />
          <Route path="brain-surgery" element={<RoleGate route="brain-surgery"><SuspenseRoute><BrainSurgery /></SuspenseRoute></RoleGate>} />
          <Route path="metrics" element={<RoleGate route="metrics"><SuspenseRoute><MetricsDashboard /></SuspenseRoute></RoleGate>} />
          <Route path="rsb-manager" element={<RoleGate route="rsb-manager"><SuspenseRoute><RSBManager /></SuspenseRoute></RoleGate>} />
          <Route path="diff-viewer" element={<RoleGate route="diff-viewer"><SuspenseRoute><DifferenceVisualizer /></SuspenseRoute></RoleGate>} />
          <Route path="evidence" element={<RoleGate route="evidence"><SuspenseRoute><EvidenceViewer /></SuspenseRoute></RoleGate>} />
          <Route path="rules" element={<RoleGate route="rules"><SuspenseRoute><RuleEditor /></SuspenseRoute></RoleGate>} />
          <Route path="approvals" element={<RoleGate route="approvals"><SuspenseRoute><Approvals /></SuspenseRoute></RoleGate>} />
          <Route path="battle-replay" element={<RoleGate route="battle-replay"><SuspenseRoute><BattleReplay /></SuspenseRoute></RoleGate>} />
          <Route path="teams" element={<RoleGate route="teams"><SuspenseRoute><TeamDirectory /></SuspenseRoute></RoleGate>} />
          <Route path="agents" element={<RoleGate route="agents"><SuspenseRoute><AgentManagement /></SuspenseRoute></RoleGate>} />
          <Route path="agent-queue" element={<RoleGate route="agent-queue"><SuspenseRoute><AgentTaskQueue /></SuspenseRoute></RoleGate>} />
          <Route path="taxonomy" element={<RoleGate route="taxonomy"><SuspenseRoute><FraudTaxonomyBrowser /></SuspenseRoute></RoleGate>} />
          <Route path="incidents" element={<RoleGate route="incidents"><SuspenseRoute><IncidentTimeline /></SuspenseRoute></RoleGate>} />
          <Route path="audit-logs" element={<RoleGate route="audit-logs"><SuspenseRoute><AuditLogViewer /></SuspenseRoute></RoleGate>} />
          <Route path="rag-console" element={<RoleGate route="rag-console"><SuspenseRoute><RAGConsole /></SuspenseRoute></RoleGate>} />
          <Route path="rag-evaluation" element={<RoleGate route="rag-evaluation"><SuspenseRoute><RAGEvaluationDashboard /></SuspenseRoute></RoleGate>} />
          <Route path="neo4j-sync" element={<RoleGate route="neo4j-sync"><SuspenseRoute><Neo4jSyncDashboard /></SuspenseRoute></RoleGate>} />
          <Route path="llm-setup" element={<RoleGate route="llm-setup"><SuspenseRoute><LLMProviderSetup /></SuspenseRoute></RoleGate>} />
          <Route path="amc-manager" element={<RoleGate route="amc-manager"><SuspenseRoute><AmcManager /></SuspenseRoute></RoleGate>} />
          <Route path="pep-manager" element={<RoleGate route="rsb-manager"><SuspenseRoute><PEPManager /></SuspenseRoute></RoleGate>} />
          <Route path="amc-explorer" element={<RoleGate route="amc-manager"><SuspenseRoute><AMCExplorer /></SuspenseRoute></RoleGate>} />
          <Route path="settings" element={<RoleGate route="settings"><SuspenseRoute><SettingsConfiguration /></SuspenseRoute></RoleGate>} />
          <Route path="users" element={<RoleGate route="users"><SuspenseRoute><UserManagement /></SuspenseRoute></RoleGate>} />
        </Route>

        {/* Catch all - redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function App() {
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    document.documentElement.classList.add("dark");
    const timer = setTimeout(() => setShowSplash(false), 1400);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="App dark min-h-screen bg-background">
      {showSplash && <SplashScreen />}
      <AuthProvider>
        <AlertProvider>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
          <Toaster position="bottom-right" theme="dark" richColors />
        </AlertProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
