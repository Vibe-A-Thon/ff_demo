/**
 * GovernanceControl - HitL/HotL Toggle Component
 * 
 * A "DEFCON-style" global control that toggles between:
 * - HitL (Human-in-the-Loop): All actions require approval
 * - HotL (Human-on-the-Loop): Actions auto-proceed with notifications
 */

import React, { useState, useEffect, createContext, useContext } from "react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "./ui/dialog";
import { toast } from "sonner";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Lock,
  Unlock,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
} from "lucide-react";

// Context for governance state
const GovernanceContext = createContext(null);

export const useGovernance = () => {
  const context = useContext(GovernanceContext);
  if (!context) {
    throw new Error("useGovernance must be used within a GovernanceProvider");
  }
  return context;
};

// Governance modes
export const GovernanceMode = {
  HITL: "hitl", // Human-in-the-Loop
  HOTL: "hotl", // Human-on-the-Loop
};

// DEFCON levels (for visual drama)
const DEFCON_LEVELS = {
  1: { name: "MAXIMUM CONTROL", color: "#EF4444", description: "All actions require human approval" },
  2: { name: "HIGH CONTROL", color: "#F97316", description: "Critical actions require approval" },
  3: { name: "MODERATE", color: "#EAB308", description: "High-risk actions require approval" },
  4: { name: "LOW CONTROL", color: "#22C55E", description: "Most actions auto-approved" },
  5: { name: "AUTONOMOUS", color: "#3B82F6", description: "Full automation enabled" },
};

// Provider component
export const GovernanceProvider = ({ children }) => {
  const [mode, setMode] = useState(GovernanceMode.HITL);
  const [defconLevel, setDefconLevel] = useState(2);
  const [pendingActions, setPendingActions] = useState([]);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);

  // Request action approval
  const requestApproval = async (action) => {
    if (mode === GovernanceMode.HOTL || defconLevel >= 4) {
      // Auto-approve with notification
      toast.success(`Auto-approved by Policy ${100 + defconLevel}`, {
        description: `Action: ${action.name}`,
        icon: <Zap className="h-4 w-4 text-blue-400" />,
      });
      return { approved: true, auto: true, policy: `Policy-${100 + defconLevel}` };
    }

    // HitL mode - require approval
    return new Promise((resolve) => {
      setCurrentAction({
        ...action,
        resolve,
        timestamp: new Date().toISOString(),
      });
      setApprovalDialogOpen(true);
    });
  };

  // Handle approval decision
  const handleApprovalDecision = (approved, reason = "") => {
    if (currentAction?.resolve) {
      currentAction.resolve({
        approved,
        auto: false,
        reason,
        approver: "current_user",
        timestamp: new Date().toISOString(),
      });
    }
    setApprovalDialogOpen(false);
    setCurrentAction(null);

    if (approved) {
      toast.success("Action Approved", {
        description: currentAction?.name,
        icon: <CheckCircle2 className="h-4 w-4 text-green-400" />,
      });
    } else {
      toast.error("Action Denied", {
        description: reason || "Awaiting further review",
        icon: <XCircle className="h-4 w-4 text-red-400" />,
      });
    }
  };

  // Toggle mode
  const toggleMode = () => {
    const newMode = mode === GovernanceMode.HITL ? GovernanceMode.HOTL : GovernanceMode.HITL;
    setMode(newMode);
    toast.info(`Switched to ${newMode.toUpperCase()} Mode`, {
      description: newMode === GovernanceMode.HITL
        ? "All actions now require human approval"
        : "Actions will auto-proceed with notifications",
      icon: newMode === GovernanceMode.HITL
        ? <Lock className="h-4 w-4" />
        : <Unlock className="h-4 w-4" />,
    });
  };

  const value = {
    mode,
    setMode,
    defconLevel,
    setDefconLevel,
    requestApproval,
    toggleMode,
    isHitL: mode === GovernanceMode.HITL,
    isHotL: mode === GovernanceMode.HOTL,
    pendingActions,
  };

  return (
    <GovernanceContext.Provider value={value}>
      {children}
      
      {/* Approval Dialog */}
      <Dialog open={approvalDialogOpen} onOpenChange={setApprovalDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-400">
              <ShieldAlert className="h-5 w-5" />
              Approval Required
            </DialogTitle>
            <DialogDescription>
              This action requires human authorization in HitL mode.
            </DialogDescription>
          </DialogHeader>
          
          {currentAction && (
            <div className="space-y-4 py-4">
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
                <h4 className="font-semibold text-amber-400">{currentAction.name}</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {currentAction.description}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Type:</span>
                  <Badge variant="outline" className="ml-2">{currentAction.type}</Badge>
                </div>
                <div>
                  <span className="text-muted-foreground">Risk:</span>
                  <Badge 
                    variant="outline" 
                    className={`ml-2 ${
                      currentAction.risk === "high" ? "text-red-400 border-red-400/30" :
                      currentAction.risk === "medium" ? "text-amber-400 border-amber-400/30" :
                      "text-green-400 border-green-400/30"
                    }`}
                  >
                    {currentAction.risk || "low"}
                  </Badge>
                </div>
              </div>
              
              {currentAction.details && (
                <div className="rounded-lg bg-black/20 p-3 font-mono text-xs">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(currentAction.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => handleApprovalDecision(false, "Denied by user")}
              className="flex-1"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Deny
            </Button>
            <Button
              onClick={() => handleApprovalDecision(true)}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </GovernanceContext.Provider>
  );
};

// Compact toggle component for header/sidebar
export const GovernanceToggle = ({ className = "" }) => {
  const { mode, toggleMode, defconLevel, setDefconLevel, isHitL } = useGovernance();
  const currentDefcon = DEFCON_LEVELS[defconLevel];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* DEFCON indicator */}
      <div 
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border"
        style={{ 
          borderColor: `${currentDefcon.color}40`,
          backgroundColor: `${currentDefcon.color}10`,
        }}
      >
        <div 
          className="h-2 w-2 rounded-full animate-pulse"
          style={{ backgroundColor: currentDefcon.color }}
        />
        <span 
          className="text-xs font-bold tracking-wider"
          style={{ color: currentDefcon.color }}
        >
          DEFCON {defconLevel}
        </span>
      </div>
      
      {/* HitL/HotL Switch */}
      <div className="flex items-center gap-2">
        <span className={`text-xs font-medium ${isHitL ? "text-amber-400" : "text-muted-foreground"}`}>
          HitL
        </span>
        <Switch
          checked={!isHitL}
          onCheckedChange={toggleMode}
          className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-amber-600"
        />
        <span className={`text-xs font-medium ${!isHitL ? "text-blue-400" : "text-muted-foreground"}`}>
          HotL
        </span>
      </div>
      
      {/* Mode indicator */}
      <Badge 
        variant="outline" 
        className={isHitL ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : "bg-blue-500/10 text-blue-400 border-blue-500/30"}
      >
        {isHitL ? (
          <>
            <Lock className="h-3 w-3 mr-1" />
            Manual
          </>
        ) : (
          <>
            <Zap className="h-3 w-3 mr-1" />
            Auto
          </>
        )}
      </Badge>
    </div>
  );
};

// Full control panel for settings page
export const GovernanceControlPanel = () => {
  const { mode, defconLevel, setDefconLevel, isHitL, toggleMode } = useGovernance();
  const currentDefcon = DEFCON_LEVELS[defconLevel];

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardContent className="pt-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div 
                className="p-3 rounded-xl"
                style={{ backgroundColor: `${currentDefcon.color}20` }}
              >
                <Shield className="h-6 w-6" style={{ color: currentDefcon.color }} />
              </div>
              <div>
                <h3 className="font-semibold">Governance Control</h3>
                <p className="text-sm text-muted-foreground">
                  Configure human oversight levels
                </p>
              </div>
            </div>
            <GovernanceToggle />
          </div>
          
          {/* DEFCON Level Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Control Level</span>
              <span 
                className="text-sm font-bold"
                style={{ color: currentDefcon.color }}
              >
                {currentDefcon.name}
              </span>
            </div>
            
            <div className="flex gap-2">
              {Object.entries(DEFCON_LEVELS).map(([level, config]) => (
                <button
                  key={level}
                  onClick={() => setDefconLevel(parseInt(level))}
                  className={`
                    flex-1 p-3 rounded-lg border transition-all
                    ${parseInt(level) === defconLevel ? "ring-2 ring-offset-2 ring-offset-background" : ""}
                  `}
                  style={{
                    borderColor: parseInt(level) === defconLevel ? config.color : "transparent",
                    backgroundColor: `${config.color}20`,
                  }}
                >
                  <div 
                    className="text-lg font-bold"
                    style={{ color: config.color }}
                  >
                    {level}
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-1">
                    DEFCON
                  </div>
                </button>
              ))}
            </div>
            
            <p className="text-xs text-muted-foreground text-center">
              {currentDefcon.description}
            </p>
          </div>
          
          {/* Mode Details */}
          <div className="grid grid-cols-2 gap-4">
            <div 
              className={`p-4 rounded-lg border ${isHitL ? "ring-2 ring-amber-500" : ""}`}
              style={{ borderColor: isHitL ? "#F59E0B" : "transparent", backgroundColor: "#F59E0B10" }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Lock className="h-4 w-4 text-amber-400" />
                <span className="font-semibold text-amber-400">HitL Mode</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Human-in-the-Loop: Actions pause for approval
              </p>
            </div>
            
            <div 
              className={`p-4 rounded-lg border ${!isHitL ? "ring-2 ring-blue-500" : ""}`}
              style={{ borderColor: !isHitL ? "#3B82F6" : "transparent", backgroundColor: "#3B82F610" }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-blue-400" />
                <span className="font-semibold text-blue-400">HotL Mode</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Human-on-the-Loop: Auto-proceed with notifications
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GovernanceControlPanel;
