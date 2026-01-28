import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { AlertTriangle, Clock, Shield, TrendingDown } from "lucide-react";

const AlertContext = createContext(null);

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error("useAlerts must be used within AlertProvider");
  }
  return context;
};

// Alert threshold configuration
const ALERT_THRESHOLDS = {
  timeToImmunity: {
    critical: 8, // Minutes - Alert when > 8 minutes
    warning: 5,  // Minutes - Warning when > 5 minutes
    good: 3,     // Minutes - Good when <= 3 minutes
  },
  successRate: {
    critical: 60, // % - Alert when < 60%
    warning: 75,  // % - Warning when < 75%
  },
  moneyAtRisk: {
    critical: 40000, // $ - Alert when > $40k
    warning: 25000,  // $ - Warning when > $25k
  },
};

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);
  const [lastMetrics, setLastMetrics] = useState(null);
  const [alertsEnabled, setAlertsEnabled] = useState(true);

  // Check metrics and generate alerts
  const checkMetrics = useCallback((metrics) => {
    if (!alertsEnabled || !metrics) return;

    const newAlerts = [];
    const now = Date.now();

    // Time to Immunity Check
    if (metrics.time_to_immunity !== undefined) {
      const tti = metrics.time_to_immunity;
      const lastTTI = lastMetrics?.time_to_immunity;

      if (tti > ALERT_THRESHOLDS.timeToImmunity.critical) {
        // Critical alert for high TTI
        newAlerts.push({
          id: `tti-critical-${now}`,
          type: "critical",
          category: "time_to_immunity",
          title: "Critical: Time to Immunity Exceeded",
          message: `Time to Immunity is ${tti} minutes - system is taking too long to adapt!`,
          value: tti,
          threshold: ALERT_THRESHOLDS.timeToImmunity.critical,
          timestamp: now,
        });
        
        toast.error(
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold">Time to Immunity Critical!</p>
              <p className="text-sm text-muted-foreground">
                TTI at {tti}m - exceeds {ALERT_THRESHOLDS.timeToImmunity.critical}m threshold
              </p>
            </div>
          </div>,
          { duration: 10000 }
        );
      } else if (tti > ALERT_THRESHOLDS.timeToImmunity.warning) {
        newAlerts.push({
          id: `tti-warning-${now}`,
          type: "warning",
          category: "time_to_immunity",
          title: "Warning: Time to Immunity Elevated",
          message: `Time to Immunity is ${tti} minutes - approaching critical threshold`,
          value: tti,
          threshold: ALERT_THRESHOLDS.timeToImmunity.warning,
          timestamp: now,
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
      if (lastTTI && tti < lastTTI && tti <= ALERT_THRESHOLDS.timeToImmunity.good) {
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
      
      if (sr < ALERT_THRESHOLDS.successRate.critical) {
        newAlerts.push({
          id: `sr-critical-${now}`,
          type: "critical",
          category: "success_rate",
          title: "Critical: Low Detection Rate",
          message: `Success rate dropped to ${sr}% - attacks may be getting through!`,
          value: sr,
          threshold: ALERT_THRESHOLDS.successRate.critical,
          timestamp: now,
        });
        
        toast.error(
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold">Detection Rate Critical!</p>
              <p className="text-sm text-muted-foreground">
                Success rate at {sr}% - below {ALERT_THRESHOLDS.successRate.critical}% threshold
              </p>
            </div>
          </div>,
          { duration: 10000 }
        );
      }
    }

    // Money at Risk Check
    if (metrics.money_at_risk !== undefined) {
      const mar = metrics.money_at_risk;
      
      if (mar > ALERT_THRESHOLDS.moneyAtRisk.critical) {
        newAlerts.push({
          id: `mar-critical-${now}`,
          type: "critical",
          category: "money_at_risk",
          title: "Critical: High Financial Exposure",
          message: `$${mar.toLocaleString()} at risk - exceeds safety threshold!`,
          value: mar,
          threshold: ALERT_THRESHOLDS.moneyAtRisk.critical,
          timestamp: now,
        });
      }
    }

    // Add new alerts to state
    if (newAlerts.length > 0) {
      setAlerts(prev => [...newAlerts, ...prev].slice(0, 50)); // Keep last 50 alerts
    }

    setLastMetrics(metrics);
  }, [alertsEnabled, lastMetrics]);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Dismiss single alert
  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  return (
    <AlertContext.Provider value={{
      alerts,
      checkMetrics,
      clearAlerts,
      dismissAlert,
      alertsEnabled,
      setAlertsEnabled,
      thresholds: ALERT_THRESHOLDS,
    }}>
      {children}
    </AlertContext.Provider>
  );
};

export default AlertProvider;
