import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { AlertTriangle, Clock, Shield, TrendingDown, DollarSign } from "lucide-react";

const AlertContext = createContext(null);

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error("useAlerts must be used within AlertProvider");
  }
  return context;
};

// Default alert threshold configuration
const DEFAULT_THRESHOLDS = {
  timeToImmunity: {
    critical: 8,
    warning: 5,
    good: 3,
  },
  successRate: {
    critical: 60,
    warning: 75,
  },
  moneyAtRisk: {
    critical: 40000,
    warning: 25000,
  },
};

// Preset configurations for different bank risk profiles
export const BANK_PRESETS = {
  conservative: {
    name: "Conservative Bank",
    description: "Low risk tolerance - tight thresholds",
    thresholds: {
      timeToImmunity: { critical: 5, warning: 3, good: 2 },
      successRate: { critical: 75, warning: 85 },
      moneyAtRisk: { critical: 25000, warning: 15000 },
    },
  },
  moderate: {
    name: "Moderate Bank",
    description: "Balanced risk approach",
    thresholds: {
      timeToImmunity: { critical: 8, warning: 5, good: 3 },
      successRate: { critical: 60, warning: 75 },
      moneyAtRisk: { critical: 40000, warning: 25000 },
    },
  },
  aggressive: {
    name: "High-Volume Bank",
    description: "Higher risk tolerance - looser thresholds",
    thresholds: {
      timeToImmunity: { critical: 12, warning: 8, good: 5 },
      successRate: { critical: 50, warning: 65 },
      moneyAtRisk: { critical: 75000, warning: 50000 },
    },
  },
  fintech: {
    name: "Fintech/Neobank",
    description: "Fast-paced, higher volume tolerance",
    thresholds: {
      timeToImmunity: { critical: 10, warning: 6, good: 4 },
      successRate: { critical: 55, warning: 70 },
      moneyAtRisk: { critical: 60000, warning: 35000 },
    },
  },
};

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);
  const [lastMetrics, setLastMetrics] = useState(null);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [thresholds, setThresholds] = useState(() => {
    // Load from localStorage if available
    const saved = localStorage.getItem("ff_alert_thresholds");
    return saved ? JSON.parse(saved) : DEFAULT_THRESHOLDS;
  });
  const [currentPreset, setCurrentPreset] = useState(() => {
    return localStorage.getItem("ff_alert_preset") || "moderate";
  });

  // Save thresholds to localStorage when they change
  useEffect(() => {
    localStorage.setItem("ff_alert_thresholds", JSON.stringify(thresholds));
  }, [thresholds]);

  useEffect(() => {
    localStorage.setItem("ff_alert_preset", currentPreset);
  }, [currentPreset]);

  // Apply a preset
  const applyPreset = useCallback((presetKey) => {
    const preset = BANK_PRESETS[presetKey];
    if (preset) {
      setThresholds(preset.thresholds);
      setCurrentPreset(presetKey);
      toast.success(`Applied "${preset.name}" alert profile`);
    }
  }, []);

  // Update individual threshold
  const updateThreshold = useCallback((category, level, value) => {
    setThresholds(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [level]: value,
      },
    }));
    setCurrentPreset("custom");
  }, []);

  // Reset to defaults
  const resetThresholds = useCallback(() => {
    setThresholds(DEFAULT_THRESHOLDS);
    setCurrentPreset("moderate");
    toast.info("Reset to default thresholds");
  }, []);

  // Check metrics and generate alerts
  const checkMetrics = useCallback((metrics) => {
    if (!alertsEnabled || !metrics) return;

    const newAlerts = [];
    const now = Date.now();

    // Time to Immunity Check
    if (metrics.time_to_immunity !== undefined) {
      const tti = metrics.time_to_immunity;
      const lastTTI = lastMetrics?.time_to_immunity;

      if (tti > thresholds.timeToImmunity.critical) {
        newAlerts.push({
          id: `tti-critical-${now}`,
          type: "critical",
          category: "time_to_immunity",
          title: "Critical: Time to Immunity Exceeded",
          message: `Time to Immunity is ${tti} minutes - system is taking too long to adapt!`,
          value: tti,
          threshold: thresholds.timeToImmunity.critical,
          timestamp: now,
          read: false,
        });
        
        toast.error(
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold">Time to Immunity Critical!</p>
              <p className="text-sm text-muted-foreground">
                TTI at {tti}m - exceeds {thresholds.timeToImmunity.critical}m threshold
              </p>
            </div>
          </div>,
          { duration: 10000 }
        );
      } else if (tti > thresholds.timeToImmunity.warning) {
        newAlerts.push({
          id: `tti-warning-${now}`,
          type: "warning",
          category: "time_to_immunity",
          title: "Warning: Time to Immunity Elevated",
          message: `Time to Immunity is ${tti} minutes - approaching critical threshold`,
          value: tti,
          threshold: thresholds.timeToImmunity.warning,
          timestamp: now,
          read: false,
        });
        
        toast.warning(
          <div className="flex items-start gap-3">
            <Clock className="h-5 w-5 text-yellow-400 mt-0.5" />
            <div>
              <p className="font-semibold">Time to Immunity Warning</p>
              <p className="text-sm text-muted-foreground">
                TTI at {tti}m - approaching critical level
              </p>
            </div>
          </div>,
          { duration: 5000 }
        );
      }

      // Positive alert when TTI drops significantly
      if (lastTTI && tti < lastTTI && tti <= thresholds.timeToImmunity.good) {
        newAlerts.push({
          id: `tti-good-${now}`,
          type: "success",
          category: "time_to_immunity",
          title: "Time to Immunity Improved",
          message: `TTI decreased to ${tti} minutes - system is learning faster!`,
          value: tti,
          threshold: thresholds.timeToImmunity.good,
          timestamp: now,
          read: false,
        });
        
        toast.success(
          <div className="flex items-start gap-3">
            <TrendingDown className="h-5 w-5 text-green-400 mt-0.5" />
            <div>
              <p className="font-semibold">Time to Immunity Improved!</p>
              <p className="text-sm text-muted-foreground">
                TTI decreased to {tti}m - system is learning faster
              </p>
            </div>
          </div>,
          { duration: 4000 }
        );
      }
    }

    // Success Rate Check
    if (metrics.success_rate !== undefined) {
      const sr = metrics.success_rate;
      
      if (sr < thresholds.successRate.critical) {
        newAlerts.push({
          id: `sr-critical-${now}`,
          type: "critical",
          category: "success_rate",
          title: "Critical: Low Detection Rate",
          message: `Success rate dropped to ${sr}% - attacks may be getting through!`,
          value: sr,
          threshold: thresholds.successRate.critical,
          timestamp: now,
          read: false,
        });
        
        toast.error(
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold">Detection Rate Critical!</p>
              <p className="text-sm text-muted-foreground">
                Success rate at {sr}% - below {thresholds.successRate.critical}% threshold
              </p>
            </div>
          </div>,
          { duration: 10000 }
        );
      } else if (sr < thresholds.successRate.warning) {
        newAlerts.push({
          id: `sr-warning-${now}`,
          type: "warning",
          category: "success_rate",
          title: "Warning: Detection Rate Declining",
          message: `Success rate at ${sr}% - below warning threshold`,
          value: sr,
          threshold: thresholds.successRate.warning,
          timestamp: now,
          read: false,
        });
      }
    }

    // Money at Risk Check
    if (metrics.money_at_risk !== undefined) {
      const mar = metrics.money_at_risk;
      
      if (mar > thresholds.moneyAtRisk.critical) {
        newAlerts.push({
          id: `mar-critical-${now}`,
          type: "critical",
          category: "money_at_risk",
          title: "Critical: High Financial Exposure",
          message: `$${mar.toLocaleString()} at risk - exceeds safety threshold!`,
          value: mar,
          threshold: thresholds.moneyAtRisk.critical,
          timestamp: now,
          read: false,
        });
        
        toast.error(
          <div className="flex items-start gap-3">
            <DollarSign className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold">Financial Exposure Critical!</p>
              <p className="text-sm text-muted-foreground">
                ${mar.toLocaleString()} at risk - above ${thresholds.moneyAtRisk.critical.toLocaleString()} threshold
              </p>
            </div>
          </div>,
          { duration: 10000 }
        );
      } else if (mar > thresholds.moneyAtRisk.warning) {
        newAlerts.push({
          id: `mar-warning-${now}`,
          type: "warning",
          category: "money_at_risk",
          title: "Warning: Elevated Financial Risk",
          message: `$${mar.toLocaleString()} at risk - approaching critical threshold`,
          value: mar,
          threshold: thresholds.moneyAtRisk.warning,
          timestamp: now,
          read: false,
        });
      }
    }

    // Add new alerts to state
    if (newAlerts.length > 0) {
      setAlerts(prev => [...newAlerts, ...prev].slice(0, 100)); // Keep last 100 alerts
    }

    setLastMetrics(metrics);
  }, [alertsEnabled, lastMetrics, thresholds]);

  // Clear all alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Dismiss single alert
  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  // Mark alert as read
  const markAsRead = useCallback((alertId) => {
    setAlerts(prev => prev.map(a => 
      a.id === alertId ? { ...a, read: true } : a
    ));
  }, []);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
  }, []);

  // Get unread count
  const unreadCount = alerts.filter(a => !a.read).length;
  const criticalCount = alerts.filter(a => a.type === "critical" && !a.read).length;

  return (
    <AlertContext.Provider value={{
      alerts,
      checkMetrics,
      clearAlerts,
      dismissAlert,
      markAsRead,
      markAllAsRead,
      alertsEnabled,
      setAlertsEnabled,
      thresholds,
      updateThreshold,
      applyPreset,
      resetThresholds,
      currentPreset,
      unreadCount,
      criticalCount,
      presets: BANK_PRESETS,
    }}>
      {children}
    </AlertContext.Provider>
  );
};

export default AlertProvider;
