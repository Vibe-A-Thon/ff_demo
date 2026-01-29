import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { Shield, FileText, Users, Download, Eye, AlertTriangle, Sparkles } from "lucide-react";

const defaultPayload = {
  title: "Explainability Panel",
  summary: "Right-click any metric or decision to see why it happened.",
  confidence: 0.86,
  triggeredRules: ["R-ATO-001", "R-VELOCITY-004"],
  evidence: ["New device + geo shift", "Payee added within 5 minutes"],
  similarCases: ["Case-1128", "Case-1136"],
  contradictions: [
    {
      id: "contradiction-1",
      title: "Rule conflict",
      detail: "R-VELOCITY-004 flagged while R-WHITELIST-009 allowed same payee.",
      severity: "medium",
    },
  ],
  learningContext: {
    summary: "This rule strengthens detection for high-velocity transfers without increasing false positives.",
    impact: "Expected to reduce missed ATO attempts by 12% within two cycles.",
    nextActions: ["Add edge-case coverage for new device baselines", "Monitor rollback triggers for 7 days"],
  },
  audienceViews: {
    regulator: "Controls enforced with documented evidence chain and SoD gates.",
    customer: "We blocked an unusual transfer from a new device to protect your account.",
    investigator: "Velocity breach with device mismatch; risk score 0.91. Rule set: ATO+Velocity.",
  },
};

const ExplainabilityPanel = ({ open, onOpenChange, payload }) => {
  const data = payload || defaultPayload;

  const handleExport = () => {
    toast.success("Explanation exported as ZIP");
  };

  if (!open) {
    return null;
  }

  return (
    <div className="flex h-full flex-col" data-testid="explain-panel">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">{data.title}</h2>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)} data-testid="explain-close-btn">
            <FileText className="h-4 w-4 mr-2" />
            Close
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-auto px-4 py-4 space-y-4 text-sm">
        <div className="rounded-md border border-border p-3">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Confidence</span>
            <Badge className="bg-green-500/15 text-green-400 border border-green-500/20">
              {Math.round((data.confidence || 0) * 100)}%
            </Badge>
          </div>
          <p className="mt-2 text-muted-foreground">{data.summary}</p>
        </div>

        <div className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-foreground">
            <Shield className="h-4 w-4 text-blue-400" />
            <span className="font-semibold">Triggered Rules</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(data.triggeredRules || []).map((rule) => (
              <Badge key={rule} variant="outline" className="font-mono">{rule}</Badge>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-foreground">
            <Eye className="h-4 w-4 text-yellow-400" />
            <span className="font-semibold">Evidence Chain</span>
          </div>
          <ul className="mt-2 list-disc pl-4 text-muted-foreground">
            {(data.evidence || []).map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-foreground">
            <AlertTriangle className="h-4 w-4 text-orange-400" />
            <span className="font-semibold">Contradiction Detection</span>
          </div>
          <div className="mt-3 space-y-2">
            {(data.contradictions || []).length > 0 ? (
              data.contradictions.map((item) => (
                <div key={item.id} className="p-2 rounded bg-black/30 border border-border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.title}</span>
                    <Badge variant="outline" className="text-xs capitalize">
                      {item.severity}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{item.detail}</p>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted-foreground">No contradictions detected in this context.</p>
            )}
          </div>
        </div>

        <div className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-foreground">
            <Sparkles className="h-4 w-4 text-purple-400" />
            <span className="font-semibold">Learning Context</span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{data.learningContext?.summary}</p>
          <p className="mt-2 text-xs text-muted-foreground">{data.learningContext?.impact}</p>
          <div className="mt-3">
            <p className="text-xs text-muted-foreground">Next actions</p>
            <ul className="mt-2 list-disc pl-4 text-xs text-muted-foreground">
              {(data.learningContext?.nextActions || []).map((action, idx) => (
                <li key={idx}>{action}</li>
              ))}
            </ul>
          </div>
        </div>

        <Tabs defaultValue="regulator">
          <TabsList className="w-full">
            <TabsTrigger value="regulator" className="flex-1">Regulator</TabsTrigger>
            <TabsTrigger value="customer" className="flex-1">Customer</TabsTrigger>
            <TabsTrigger value="investigator" className="flex-1">Investigator</TabsTrigger>
          </TabsList>
          <TabsContent value="regulator" className="mt-3">
            <div className="rounded-md border border-border p-3 text-muted-foreground">
              {data.audienceViews?.regulator}
            </div>
          </TabsContent>
          <TabsContent value="customer" className="mt-3">
            <div className="rounded-md border border-border p-3 text-muted-foreground">
              {data.audienceViews?.customer}
            </div>
          </TabsContent>
          <TabsContent value="investigator" className="mt-3">
            <div className="rounded-md border border-border p-3 text-muted-foreground">
              {data.audienceViews?.investigator}
            </div>
          </TabsContent>
        </Tabs>

        <div className="rounded-md border border-border p-3">
          <div className="flex items-center gap-2 text-foreground">
            <Users className="h-4 w-4 text-purple-400" />
            <span className="font-semibold">Similar Cases</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(data.similarCases || []).map((caseId) => (
              <Badge key={caseId} variant="outline">{caseId}</Badge>
            ))}
          </div>
        </div>
      </div>
      <div className="border-t border-border p-4">
        <Button variant="outline" className="w-full" onClick={handleExport} data-testid="explain-export-btn">
          <Download className="h-4 w-4 mr-2" />
          Export ZIP
        </Button>
      </div>
    </div>
  );
};

export default ExplainabilityPanel;
