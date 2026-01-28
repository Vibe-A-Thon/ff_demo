import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";

// Layout
import Layout from "./components/Layout";

// Pages
import WarRoom from "./pages/WarRoom";
import BrainSurgery from "./pages/BrainSurgery";
import MetricsDashboard from "./pages/MetricsDashboard";
import RSBManager from "./pages/RSBManager";
import DifferenceVisualizer from "./pages/DifferenceVisualizer";
import EvidenceViewer from "./pages/EvidenceViewer";
import RuleEditor from "./pages/RuleEditor";
import Approvals from "./pages/Approvals";

function App() {
  return (
    <div className="App dark min-h-screen bg-background">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
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
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}

export default App;
