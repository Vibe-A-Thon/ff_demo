import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { toast } from "sonner";
import { xaiAPI } from "../lib/api";
import {
  ArrowRightIcon,
  Link2Icon,
  SparklesIcon,
  GitCompareIcon,
  AlertTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CopyIcon,
  RefreshCwIcon,
  TargetIcon,
  ScaleIcon,
  ShieldIcon,
  FileSearchIcon,
} from "lucide-react";

/**
 * CounterfactualCard - Displays a single counterfactual with evidence links
 */
const CounterfactualCard = ({ counterfactual, index, onExpand }) => {
  const [expanded, setExpanded] = useState(false);
  const confidence = counterfactual.confidence || 0;
  const confidenceColor =
    confidence >= 0.8 ? "text-green-400" : confidence >= 0.6 ? "text-yellow-400" : "text-orange-400";

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(counterfactual, null, 2));
    toast.success("Counterfactual copied to clipboard");
  };

  return (
    <div
      className="rounded-lg border border-border bg-zinc-900/40 p-4 hover:border-purple-500/30 transition-all duration-200"
      data-testid={`counterfactual-${index}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <GitCompareIcon className="h-4 w-4 text-purple-400" />
            <span className="font-medium text-sm">{counterfactual.label}</span>
            <Badge variant="outline" className={`text-xs ${confidenceColor}`}>
              {(confidence * 100).toFixed(0)}% confident
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-2">{counterfactual.description}</p>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleCopy}
            data-testid={`copy-cf-${index}`}
          >
            <CopyIcon className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setExpanded(!expanded)}
            data-testid={`expand-cf-${index}`}
          >
            {expanded ? (
              <ChevronDownIcon className="h-3.5 w-3.5" />
            ) : (
              <ChevronRightIcon className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>

      {/* Expected outcome badge */}
      <div className="flex items-center gap-2 mt-3">
        <ArrowRightIcon className="h-3 w-3 text-muted-foreground" />
        <Badge className="bg-blue-500/15 text-blue-400 border border-blue-500/20 text-xs">
          Expected: {counterfactual.expected_outcome}
        </Badge>
        {counterfactual.rule_id && (
          <Badge variant="outline" className="text-xs font-mono">
            {counterfactual.rule_id}
          </Badge>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 space-y-3 pt-3 border-t border-border/50">
          {/* Changes */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Changes Required</p>
            <div className="grid gap-2">
              {Object.entries(counterfactual.changes || {}).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded bg-black/30 px-3 py-2 text-xs"
                >
                  <span className="font-mono text-muted-foreground">{key}</span>
                  <div className="flex items-center gap-2">
                    {counterfactual.original_value !== undefined && (
                      <>
                        <span className="text-red-400/80">{String(counterfactual.original_value)}</span>
                        <ArrowRightIcon className="h-3 w-3 text-muted-foreground" />
                      </>
                    )}
                    <span className="text-green-400">{String(value)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Feature importance */}
          {counterfactual.feature_importance !== undefined && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Feature Importance</p>
              <div className="flex items-center gap-3">
                <Progress value={counterfactual.feature_importance * 100} className="h-2 flex-1" />
                <span className="text-xs font-mono text-muted-foreground">
                  {(counterfactual.feature_importance * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}

          {/* Evidence links */}
          {counterfactual.evidence_links?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Evidence Links</p>
              <div className="flex flex-wrap gap-2">
                {counterfactual.evidence_links.map((link, idx) => (
                  <Badge key={idx} variant="outline" className="text-[10px] font-mono">
                    <Link2Icon className="h-2.5 w-2.5 mr-1" />
                    {link.length > 20 ? `${link.slice(0, 20)}...` : link}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * SimilarCaseCard - Displays a similar case with similarity breakdown
 */
const SimilarCaseCard = ({ similarCase, index, onViewPack }) => {
  const [expanded, setExpanded] = useState(false);
  const similarity = similarCase.similarity || 0;
  const similarityColor =
    similarity >= 0.7 ? "text-green-400" : similarity >= 0.5 ? "text-yellow-400" : "text-orange-400";

  return (
    <div
      className="rounded-lg border border-border bg-zinc-900/40 p-4 hover:border-cyan-500/30 transition-all duration-200"
      data-testid={`similar-case-${index}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <FileSearchIcon className="h-4 w-4 text-cyan-400" />
            <span className="font-medium text-sm font-mono">{similarCase.case_id?.slice(0, 12)}...</span>
            <Badge variant="outline" className={`text-xs ${similarityColor}`}>
              {(similarity * 100).toFixed(1)}% similar
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{similarCase.summary}</p>
        </div>
        <div className="flex items-center gap-1">
          {onViewPack && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => onViewPack(similarCase.metadata?.evidence_pack_id)}
              data-testid={`view-pack-${index}`}
            >
              View Pack
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setExpanded(!expanded)}
            data-testid={`expand-case-${index}`}
          >
            {expanded ? (
              <ChevronDownIcon className="h-3.5 w-3.5" />
            ) : (
              <ChevronRightIcon className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>

      {/* Matched rules */}
      {similarCase.metadata?.matched_rules?.length > 0 && (
        <div className="flex items-center gap-2 mt-3">
          <ShieldIcon className="h-3 w-3 text-muted-foreground" />
          <div className="flex flex-wrap gap-1">
            {similarCase.metadata.matched_rules.slice(0, 5).map((rule) => (
              <Badge key={rule} variant="outline" className="text-[10px] font-mono">
                {rule}
              </Badge>
            ))}
            {similarCase.metadata.matched_rules.length > 5 && (
              <Badge variant="outline" className="text-[10px]">
                +{similarCase.metadata.matched_rules.length - 5} more
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Expanded details */}
      {expanded && similarCase.metadata?.score_breakdown && (
        <div className="mt-4 space-y-3 pt-3 border-t border-border/50">
          <p className="text-xs font-medium text-muted-foreground">Similarity Breakdown</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(similarCase.metadata.score_breakdown)
              .filter(([key]) => typeof similarCase.metadata.score_breakdown[key] === "number")
              .slice(0, 6)
              .map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded bg-black/30 px-3 py-2 text-xs"
                >
                  <span className="text-muted-foreground capitalize">{key.replace("_", " ")}</span>
                  <span className={value > 0.5 ? "text-green-400" : "text-muted-foreground"}>
                    {(value * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
          </div>

          {/* Additional metadata */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {similarCase.metadata?.run_id && (
              <div className="rounded bg-black/30 px-3 py-2">
                <span className="text-muted-foreground">Run: </span>
                <span className="font-mono">{similarCase.metadata.run_id.slice(0, 8)}...</span>
              </div>
            )}
            {similarCase.metadata?.decision && (
              <div className="rounded bg-black/30 px-3 py-2">
                <span className="text-muted-foreground">Decision: </span>
                <span className="text-white capitalize">{similarCase.metadata.decision}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * CounterfactualPanel - Main component for displaying counterfactuals and similar cases
 */
const CounterfactualPanel = ({ runId, packId, onViewPack }) => {
  const [activeTab, setActiveTab] = useState("counterfactuals");
  const [counterfactuals, setCounterfactuals] = useState([]);
  const [similarCases, setSimilarCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [featuresUsed, setFeaturesUsed] = useState(0);
  const [rulesUsed, setRulesUsed] = useState(0);
  const [signatureHash, setSignatureHash] = useState("");

  const loadData = async () => {
    if (!runId && !packId) return;
    setLoading(true);

    try {
      if (runId) {
        const [cfResponse, scResponse] = await Promise.all([
          xaiAPI.getCounterfactuals({ run_id: runId, max_counterfactuals: 5 }),
          xaiAPI.getSimilarCases({ run_id: runId, min_similarity: 0.2, max_results: 5 }),
        ]);
        setCounterfactuals(cfResponse.data.counterfactuals || []);
        setFeaturesUsed(cfResponse.data.features_used || 0);
        setRulesUsed(cfResponse.data.rules_used || 0);
        setSimilarCases(scResponse.data.similar_cases || []);
        setSignatureHash(scResponse.data.signature_hash || "");
      } else if (packId) {
        const scResponse = await xaiAPI.getSimilarToPack(packId, {
          min_similarity: 0.2,
          max_results: 5,
        });
        setSimilarCases(scResponse.data.similar_cases || []);
        setSignatureHash(scResponse.data.signature?.signature_hash || "");
      }
    } catch (error) {
      console.error("Failed to load counterfactual data:", error);
      toast.error("Failed to load explainability data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [runId, packId]);

  return (
    <Card className="border-border" data-testid="counterfactual-panel">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <SparklesIcon className="h-4 w-4 text-purple-400" />
            Counterfactuals & Similar Cases
          </CardTitle>
          <div className="flex items-center gap-2">
            {signatureHash && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      SIG: {signatureHash.slice(0, 8)}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>Case signature hash for matching</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={loadData}
              disabled={loading}
              data-testid="refresh-cf-panel"
            >
              <RefreshCwIcon className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full grid grid-cols-2 mb-4">
            <TabsTrigger value="counterfactuals" className="text-xs" data-testid="tab-counterfactuals">
              <GitCompareIcon className="h-3.5 w-3.5 mr-1.5" />
              Counterfactuals ({counterfactuals.length})
            </TabsTrigger>
            <TabsTrigger value="similar" className="text-xs" data-testid="tab-similar-cases">
              <FileSearchIcon className="h-3.5 w-3.5 mr-1.5" />
              Similar Cases ({similarCases.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="counterfactuals" className="space-y-4">
            {/* Summary stats */}
            {counterfactuals.length > 0 && (
              <div className="flex items-center gap-4 text-xs text-muted-foreground border-b border-border pb-3 mb-3">
                <div className="flex items-center gap-1.5">
                  <TargetIcon className="h-3.5 w-3.5" />
                  <span>{featuresUsed} features analyzed</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldIcon className="h-3.5 w-3.5" />
                  <span>{rulesUsed} rules extracted</span>
                </div>
              </div>
            )}

            {loading ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                <RefreshCwIcon className="h-6 w-6 mx-auto mb-2 animate-spin" />
                Generating counterfactuals...
              </div>
            ) : counterfactuals.length > 0 ? (
              <div className="space-y-3">
                {counterfactuals.map((cf, idx) => (
                  <CounterfactualCard key={cf.label || idx} counterfactual={cf} index={idx} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangleIcon className="h-6 w-6 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No counterfactuals generated</p>
                <p className="text-xs mt-1">Run needs sufficient evidence data</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="similar" className="space-y-4">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                <RefreshCwIcon className="h-6 w-6 mx-auto mb-2 animate-spin" />
                Searching for similar cases...
              </div>
            ) : similarCases.length > 0 ? (
              <div className="space-y-3">
                {similarCases.map((sc, idx) => (
                  <SimilarCaseCard
                    key={sc.case_id || idx}
                    similarCase={sc}
                    index={idx}
                    onViewPack={onViewPack}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <ScaleIcon className="h-6 w-6 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No similar cases found</p>
                <p className="text-xs mt-1">Expand evidence pack history for more matches</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default CounterfactualPanel;
export { CounterfactualCard, SimilarCaseCard };
