import React, { useState } from "react";
import { useAlerts, BANK_PRESETS } from "../contexts/AlertContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Slider } from "../components/ui/slider";
import {
  Bell,
  AlertTriangle,
  Clock,
  Shield,
  DollarSign,
  CheckCircle2,
  Trash2,
  X,
  Settings,
  Building2,
  RotateCcw,
  Eye,
  EyeOff,
} from "lucide-react";

// Alert History Panel Component
export const AlertHistoryPanel = ({ open, onOpenChange }) => {
  const { 
    alerts, 
    clearAlerts, 
    dismissAlert, 
    markAsRead, 
    markAllAsRead,
    unreadCount,
    criticalCount 
  } = useAlerts();
  const [filter, setFilter] = useState("all");

  const filteredAlerts = alerts.filter(alert => {
    if (filter === "all") return true;
    if (filter === "unread") return !alert.read;
    return alert.type === filter;
  });

  const getAlertIcon = (type) => {
    switch (type) {
      case "critical": return <AlertTriangle className="h-4 w-4 text-red-400" />;
      case "warning": return <Clock className="h-4 w-4 text-yellow-400" />;
      case "success": return <CheckCircle2 className="h-4 w-4 text-green-400" />;
      default: return <Bell className="h-4 w-4" />;
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "time_to_immunity": return <Clock className="h-3 w-3" />;
      case "success_rate": return <Shield className="h-3 w-3" />;
      case "money_at_risk": return <DollarSign className="h-3 w-3" />;
      default: return null;
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[450px] bg-card border-border" data-testid="alert-history-panel">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Alert History
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">{unreadCount} unread</Badge>
            )}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4 space-y-4">
          {/* Filter Tabs */}
          <Tabs value={filter} onValueChange={setFilter}>
            <TabsList className="w-full">
              <TabsTrigger value="all" className="flex-1">All</TabsTrigger>
              <TabsTrigger value="unread" className="flex-1">
                Unread {unreadCount > 0 && `(${unreadCount})`}
              </TabsTrigger>
              <TabsTrigger value="critical" className="flex-1">
                Critical {criticalCount > 0 && `(${criticalCount})`}
              </TabsTrigger>
              <TabsTrigger value="warning" className="flex-1">Warning</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="sm" onClick={markAllAsRead} disabled={unreadCount === 0}>
              <Eye className="h-4 w-4 mr-2" />
              Mark All Read
            </Button>
            <Button variant="ghost" size="sm" onClick={clearAlerts} disabled={alerts.length === 0}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          </div>

          {/* Alert List */}
          <ScrollArea className="h-[calc(100vh-280px)]">
            <div className="space-y-2 pr-4">
              {filteredAlerts.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No alerts to display</p>
                </div>
              ) : (
                filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg border transition-all ${
                      !alert.read 
                        ? 'bg-zinc-800/50 border-zinc-600' 
                        : 'bg-card border-border opacity-75'
                    } ${
                      alert.type === 'critical' ? 'border-l-4 border-l-red-500' :
                      alert.type === 'warning' ? 'border-l-4 border-l-yellow-500' :
                      alert.type === 'success' ? 'border-l-4 border-l-green-500' : ''
                    }`}
                    onClick={() => markAsRead(alert.id)}
                    data-testid={`alert-item-${alert.id}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        {getAlertIcon(alert.type)}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{alert.title}</p>
                          <p className="text-xs text-muted-foreground mt-1">{alert.message}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs">
                              {getCategoryIcon(alert.category)}
                              <span className="ml-1 capitalize">{alert.category.replace(/_/g, ' ')}</span>
                            </Badge>
                            <span className="text-xs text-muted-foreground">{formatTime(alert.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-50 hover:opacity-100"
                        onClick={(e) => { e.stopPropagation(); dismissAlert(alert.id); }}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// Threshold Configuration Panel Component
export const ThresholdConfigPanel = ({ open, onOpenChange }) => {
  const { 
    thresholds, 
    updateThreshold, 
    applyPreset, 
    resetThresholds,
    currentPreset,
    presets 
  } = useAlerts();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[500px] bg-card border-border" data-testid="threshold-config-panel">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Alert Threshold Configuration
          </SheetTitle>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-100px)] mt-4">
          <div className="space-y-6 pr-4">
            {/* Presets */}
            <Card className="border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Bank Risk Profiles
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(presets).map(([key, preset]) => (
                    <Button
                      key={key}
                      variant={currentPreset === key ? "default" : "outline"}
                      className="h-auto py-3 flex flex-col items-start"
                      onClick={() => applyPreset(key)}
                      data-testid={`preset-${key}`}
                    >
                      <span className="font-medium">{preset.name}</span>
                      <span className="text-xs text-muted-foreground">{preset.description}</span>
                    </Button>
                  ))}
                </div>
                {currentPreset === "custom" && (
                  <Badge variant="outline" className="mt-2">Custom configuration</Badge>
                )}
              </CardContent>
            </Card>

            {/* Time to Immunity Thresholds */}
            <Card className="border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-400" />
                  Time to Immunity (minutes)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-red-400">Critical Threshold (alert when &gt;)</Label>
                    <span className="font-mono text-sm">{thresholds.timeToImmunity.critical}m</span>
                  </div>
                  <Slider
                    value={[thresholds.timeToImmunity.critical]}
                    onValueChange={([v]) => updateThreshold("timeToImmunity", "critical", v)}
                    min={1}
                    max={20}
                    step={1}
                    className="w-full"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-yellow-400">Warning Threshold (alert when &gt;)</Label>
                    <span className="font-mono text-sm">{thresholds.timeToImmunity.warning}m</span>
                  </div>
                  <Slider
                    value={[thresholds.timeToImmunity.warning]}
                    onValueChange={([v]) => updateThreshold("timeToImmunity", "warning", v)}
                    min={1}
                    max={15}
                    step={1}
                    className="w-full"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-green-400">Good Threshold (celebrate when ≤)</Label>
                    <span className="font-mono text-sm">{thresholds.timeToImmunity.good}m</span>
                  </div>
                  <Slider
                    value={[thresholds.timeToImmunity.good]}
                    onValueChange={([v]) => updateThreshold("timeToImmunity", "good", v)}
                    min={1}
                    max={10}
                    step={1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Success Rate Thresholds */}
            <Card className="border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-400" />
                  Success Rate (%)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-red-400">Critical Threshold (alert when &lt;)</Label>
                    <span className="font-mono text-sm">{thresholds.successRate.critical}%</span>
                  </div>
                  <Slider
                    value={[thresholds.successRate.critical]}
                    onValueChange={([v]) => updateThreshold("successRate", "critical", v)}
                    min={30}
                    max={80}
                    step={5}
                    className="w-full"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-yellow-400">Warning Threshold (alert when &lt;)</Label>
                    <span className="font-mono text-sm">{thresholds.successRate.warning}%</span>
                  </div>
                  <Slider
                    value={[thresholds.successRate.warning]}
                    onValueChange={([v]) => updateThreshold("successRate", "warning", v)}
                    min={50}
                    max={95}
                    step={5}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Money at Risk Thresholds */}
            <Card className="border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-red-400" />
                  Money at Risk ($)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-red-400">Critical Threshold (alert when &gt;)</Label>
                    <span className="font-mono text-sm">${thresholds.moneyAtRisk.critical.toLocaleString()}</span>
                  </div>
                  <Slider
                    value={[thresholds.moneyAtRisk.critical]}
                    onValueChange={([v]) => updateThreshold("moneyAtRisk", "critical", v)}
                    min={10000}
                    max={100000}
                    step={5000}
                    className="w-full"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs text-yellow-400">Warning Threshold (alert when &gt;)</Label>
                    <span className="font-mono text-sm">${thresholds.moneyAtRisk.warning.toLocaleString()}</span>
                  </div>
                  <Slider
                    value={[thresholds.moneyAtRisk.warning]}
                    onValueChange={([v]) => updateThreshold("moneyAtRisk", "warning", v)}
                    min={5000}
                    max={75000}
                    step={5000}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Reset Button */}
            <Button variant="outline" className="w-full" onClick={resetThresholds}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};

export default AlertHistoryPanel;
