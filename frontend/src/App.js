import React, { useEffect, useState } from "react";
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

// Pages
import Login from "./pages/Login";
import WarRoom from "./pages/WarRoom";
import BrainSurgery from "./pages/BrainSurgery";
import MetricsDashboard from "./pages/MetricsDashboard";
import RSBManager from "./pages/RSBManager";
import DifferenceVisualizer from "./pages/DifferenceVisualizer";
import EvidenceViewer from "./pages/EvidenceViewer";
import RuleEditor from "./pages/RuleEditor";
import Approvals from "./pages/Approvals";
import BattleReplay from "./pages/BattleReplay";

// Role-based access configuration
const ROLE_PERMISSIONS = {
  admin: ["*"], // Access to everything
  analyst: ["war-room", "brain-surgery", "metrics", "evidence", "battle-replay"],
  engineer: ["war-room", "brain-surgery", "metrics", "rsb-manager", "diff-viewer", "rules", "battle-replay"],
  compliance: ["metrics", "evidence", "approvals", "battle-replay"],
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
    return <Navigate to="/war-room" replace />;
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

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
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
          <Route index element={<Navigate to="/war-room" replace />} />
          <Route path="war-room" element={<RoleGate route="war-room"><WarRoom /></RoleGate>} />
          <Route path="brain-surgery" element={<RoleGate route="brain-surgery"><BrainSurgery /></RoleGate>} />
          <Route path="metrics" element={<RoleGate route="metrics"><MetricsDashboard /></RoleGate>} />
          <Route path="rsb-manager" element={<RoleGate route="rsb-manager"><RSBManager /></RoleGate>} />
          <Route path="diff-viewer" element={<RoleGate route="diff-viewer"><DifferenceVisualizer /></RoleGate>} />
          <Route path="evidence" element={<RoleGate route="evidence"><EvidenceViewer /></RoleGate>} />
          <Route path="rules" element={<RoleGate route="rules"><RuleEditor /></RoleGate>} />
          <Route path="approvals" element={<RoleGate route="approvals"><Approvals /></RoleGate>} />
          <Route path="battle-replay" element={<RoleGate route="battle-replay"><BattleReplay /></RoleGate>} />
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
