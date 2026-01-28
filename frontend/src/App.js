import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";

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

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
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
          <Route path="war-room" element={<WarRoom />} />
          <Route path="brain-surgery" element={<BrainSurgery />} />
          <Route path="metrics" element={<MetricsDashboard />} />
          <Route path="rsb-manager" element={<RSBManager />} />
          <Route path="diff-viewer" element={<DifferenceVisualizer />} />
          <Route path="evidence" element={<EvidenceViewer />} />
          <Route path="rules" element={<RuleEditor />} />
          <Route path="approvals" element={<Approvals />} />
        </Route>

        {/* Catch all - redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function App() {
  return (
    <div className="App dark min-h-screen bg-background">
      <AuthProvider>
        <AlertProvider>
          <AppRoutes />
          <Toaster position="bottom-right" theme="dark" richColors />
        </AlertProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
