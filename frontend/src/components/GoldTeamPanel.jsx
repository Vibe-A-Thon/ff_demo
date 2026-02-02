/**
 * GoldTeamPanel - Contextual Explainability Side Panel
 * 
 * A slide-over panel available on every screen that provides:
 * - Decision explanation with confidence scores
 * - Evidence chain linking
 * - Audit trail references
 * - Multi-audience views (Regulator, Customer, Investigator)
 */

import React, { useState, useEffect, createContext, useContext } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ScrollArea } from "./ui/scroll-area";
import { toast } from "sonner";
import {
  Sparkles,
  Shield,
  FileText,
  Eye,
  Users,
  Download,
  Link2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Hash,
  Lightbulb,
  Brain,
  Scale,
  Gavel,
  User,
  Search,
  Copy,
  ExternalLink,
} from "lucide-react";

// Context for panel state
const GoldTeamContext = createContext(null);

export const useGoldTeam = () => {
  const context = useContext(GoldTeamContext);
  if (!context) {
    // Return safe defaults if not in provider
    return {
      openPanel: () => {},
      closePanel: () => {},
      explain: () => {},
      isOpen: false,
    };
  }
  return context;
};

// Provider component
export const GoldTeamProvider = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  const openPanel = (context = null) => {
    if (context) {
      generateExplanation(context);
    }
    setIsOpen(true);
  };

  const closePanel = () => {
    setIsOpen(false);
  };

  const generateExplanation = async (context) => {
    setLoading(true);
    
    // Simulate API call - in production, this would call the backend
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    const mockExplanation = {
      id: `exp-${Date.now()}`,
      decision: context.decision || "Blocked",
      confidence: context.confidence || 0.98,
      timestamp: new Date().toISOString(),
      
      summary: context.summary || "Transaction blocked due to multiple high-risk indicators.",
      
      triggeredRules: context.rules || [
        { id: "VEL-001", name: "Velocity Check", score: 0.92 },
        { id: "ATO-099", name: "Account Takeover", score: 0.88 },
        { id: "GEO-008", name: "Impossible Travel", score: 0.95 },
      ],
      
      evidence: context.evidence || [
        { type: "signal", value: "New device fingerprint detected" },
        { type: "signal", value: "Payee added within 5 minutes of login" },
        { type: "pattern", value: "Matched ATO Pattern #P-2847" },
        { type: "vector", value: "Similarity: 0.92 to known fraud vector" },
      ],
      
      ragRetrievals: context.ragRetrievals || [
        { collection: "patterns", docId: "PAT-2847", title: "ATO Velocity Pattern", similarity: 0.92 },
        { collection: "attacks", docId: "ATK-1128", title: "Credential Stuffing v3", similarity: 0.87 },
        { collection: "taxonomy", docId: "TAX-042", title: "Account Takeover Scenario", similarity: 0.85 },
      ],
      
      auditTrail: {
        logId: context.logId || `#${Math.floor(Math.random() * 100000)}`,
        agentId: context.agentId || "blue-sentinel-01",
        battleId: context.battleId,
        timestamp: new Date().toISOString(),
      },
      
      counterfactual: context.counterfactual || {
        question: "What would change the outcome?",
        factors: [
          "If transaction amount was below $500",
          "If device was previously recognized",
          "If payee was on trusted list",
        ],
      },
      
      audienceViews: {
        regulator: "Controls enforced per AML/CFT guidelines. Evidence chain documented with full audit trail. Separation of duties maintained through HitL approval gates.",
        customer: "We blocked an unusual transfer from a new device to protect your account. Please verify this was you by calling our support line.",
        investigator: "High-risk transaction blocked. Velocity breach detected with device mismatch. Risk score: 0.98. Primary signals: new device + rapid payee addition. Recommend SDA review.",
      },
    };
    
    setExplanation(mockExplanation);
    setLoading(false);
  };

  const explain = (context) => {
    generateExplanation(context);
    setIsOpen(true);
  };

  const value = {
    isOpen,
    openPanel,
    closePanel,
    explain,
    explanation,
    loading,
  };

  return (
    <GoldTeamContext.Provider value={value}>
      {children}
      <GoldTeamSlidePanel />
    </GoldTeamContext.Provider>
  );
};

// The actual slide panel component
const GoldTeamSlidePanel = () => {
  const { isOpen, closePanel, explanation, loading } = useGoldTeam();

  const handleExport = () => {
    toast.success("Explanation exported as Evidence Package", {
      description: `Log ID: ${explanation?.auditTrail?.logId}`,
    });
  };

  const handleCopyLogId = () => {
    navigator.clipboard.writeText(explanation?.auditTrail?.logId || "");
    toast.success("Log ID copied to clipboard");
  };

  return (
    <Sheet open={isOpen} onOpenChange={closePanel}>
      <SheetContent className="w-[450px] sm:w-[500px] overflow-hidden flex flex-col">
        <SheetHeader className="border-b border-border pb-4">
          <SheetTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-yellow-500/20">
              <Sparkles className="h-5 w-5 text-yellow-400" />
            </div>
            <div>
              <span className="text-yellow-400">Gold Team</span>
              <span className="ml-2">Explainability</span>
            </div>
          </SheetTitle>
        </SheetHeader>

        <ScrollArea className="flex-1 py-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <div className="relative">
                <Brain className="h-12 w-12 text-yellow-400 animate-pulse" />
                <div className="absolute inset-0 animate-ping">
                  <Brain className="h-12 w-12 text-yellow-400 opacity-30" />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Generating explanation...
              </p>
            </div>
          ) : explanation ? (
            <div className="space-y-4 px-1">
              {/* Decision Summary */}
              <Card className="bg-card/50 border-yellow-500/20">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {explanation.decision === "Blocked" ? (
                        <XCircle className="h-5 w-5 text-red-400" />
                      ) : explanation.decision === "Flagged" ? (
                        <AlertTriangle className="h-5 w-5 text-amber-400" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-green-400" />
                      )}
                      <span className="font-semibold">Decision: {explanation.decision}</span>
                    </div>
                    <Badge 
                      className={`
                        ${explanation.confidence >= 0.9 ? "bg-green-500/20 text-green-400 border-green-500/30" :
                          explanation.confidence >= 0.7 ? "bg-amber-500/20 text-amber-400 border-amber-500/30" :
                          "bg-red-500/20 text-red-400 border-red-500/30"}
                      `}
                    >
                      {Math.round(explanation.confidence * 100)}% Confidence
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {explanation.summary}
                  </p>
                </CardContent>
              </Card>

              {/* Triggered Rules */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-400" />
                  <span className="text-sm font-semibold">Triggered Rules</span>
                </div>
                <div className="space-y-2">
                  {explanation.triggeredRules.map((rule) => (
                    <div 
                      key={rule.id}
                      className="flex items-center justify-between p-2 rounded-lg bg-blue-500/10 border border-blue-500/20"
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {rule.id}
                        </Badge>
                        <span className="text-sm">{rule.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress value={rule.score * 100} className="w-16 h-1.5" />
                        <span className="text-xs text-muted-foreground">
                          {Math.round(rule.score * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Evidence Chain */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Link2 className="h-4 w-4 text-purple-400" />
                  <span className="text-sm font-semibold">Evidence Chain</span>
                </div>
                <div className="space-y-1">
                  {explanation.evidence.map((item, idx) => (
                    <div 
                      key={idx}
                      className="flex items-start gap-2 p-2 rounded-lg bg-purple-500/10 border border-purple-500/20"
                    >
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {item.type}
                      </Badge>
                      <span className="text-sm text-muted-foreground">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* RAG Retrievals */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Search className="h-4 w-4 text-cyan-400" />
                  <span className="text-sm font-semibold">Vector DB Matches</span>
                </div>
                <div className="space-y-2">
                  {explanation.ragRetrievals.map((retrieval) => (
                    <div 
                      key={retrieval.docId}
                      className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20"
                    >
                      <div className="flex items-center justify-between">
                        <Badge 
                          variant="outline" 
                          className="text-[10px] uppercase"
                        >
                          {retrieval.collection}
                        </Badge>
                        <span className="text-xs text-cyan-400">
                          Similarity: {Math.round(retrieval.similarity * 100)}%
                        </span>
                      </div>
                      <p className="text-sm mt-1">{retrieval.title}</p>
                      <p className="text-xs text-muted-foreground font-mono">
                        {retrieval.docId}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Counterfactual */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-400" />
                  <span className="text-sm font-semibold">Counterfactual Analysis</span>
                </div>
                <Card className="bg-amber-500/10 border-amber-500/20">
                  <CardContent className="pt-3">
                    <p className="text-sm font-medium text-amber-400">
                      {explanation.counterfactual.question}
                    </p>
                    <ul className="mt-2 space-y-1">
                      {explanation.counterfactual.factors.map((factor, idx) => (
                        <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                          <span className="text-amber-400">•</span>
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* Audience Views */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-green-400" />
                  <span className="text-sm font-semibold">Audience Views</span>
                </div>
                <Tabs defaultValue="regulator" className="w-full">
                  <TabsList className="w-full grid grid-cols-3">
                    <TabsTrigger value="regulator" className="text-xs">
                      <Gavel className="h-3 w-3 mr-1" />
                      Regulator
                    </TabsTrigger>
                    <TabsTrigger value="customer" className="text-xs">
                      <User className="h-3 w-3 mr-1" />
                      Customer
                    </TabsTrigger>
                    <TabsTrigger value="investigator" className="text-xs">
                      <Search className="h-3 w-3 mr-1" />
                      Investigator
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="regulator">
                    <Card className="bg-green-500/10 border-green-500/20">
                      <CardContent className="pt-3 text-sm text-muted-foreground">
                        {explanation.audienceViews.regulator}
                      </CardContent>
                    </Card>
                  </TabsContent>
                  <TabsContent value="customer">
                    <Card className="bg-blue-500/10 border-blue-500/20">
                      <CardContent className="pt-3 text-sm text-muted-foreground">
                        {explanation.audienceViews.customer}
                      </CardContent>
                    </Card>
                  </TabsContent>
                  <TabsContent value="investigator">
                    <Card className="bg-purple-500/10 border-purple-500/20">
                      <CardContent className="pt-3 text-sm text-muted-foreground">
                        {explanation.audienceViews.investigator}
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </div>

              {/* Audit Trail */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-semibold">Audit Trail</span>
                </div>
                <Card className="bg-gray-500/10 border-gray-500/20">
                  <CardContent className="pt-3">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-muted-foreground text-xs">Log ID</span>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="font-mono">
                            {explanation.auditTrail.logId}
                          </Badge>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-6 w-6 p-0"
                            onClick={handleCopyLogId}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-xs">Agent</span>
                        <Badge variant="outline" className="font-mono mt-1 block w-fit">
                          {explanation.auditTrail.agentId}
                        </Badge>
                      </div>
                      <div className="col-span-2">
                        <span className="text-muted-foreground text-xs">Timestamp</span>
                        <p className="text-xs font-mono mt-1">
                          {new Date(explanation.auditTrail.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <Sparkles className="h-12 w-12 text-yellow-400/50" />
              <p className="text-sm text-muted-foreground text-center">
                Click "Explain" on any decision or event<br />to generate an explanation.
              </p>
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="border-t border-border pt-4 space-y-2">
          <Button 
            variant="outline" 
            className="w-full" 
            onClick={handleExport}
            disabled={!explanation}
          >
            <Download className="h-4 w-4 mr-2" />
            Export Evidence Package
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// Floating "Explain" button component
export const ExplainButton = ({ context, size = "default", className = "" }) => {
  const { explain } = useGoldTeam();

  return (
    <Button
      variant="outline"
      size={size}
      className={`bg-yellow-500/10 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/20 ${className}`}
      onClick={() => explain(context)}
    >
      <Sparkles className="h-4 w-4 mr-2" />
      Explain
    </Button>
  );
};

export default GoldTeamProvider;
