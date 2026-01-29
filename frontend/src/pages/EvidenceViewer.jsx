import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { evidenceAPI, battleAPI } from "../lib/api";
import { toast } from "sonner";
import {
  FileSearch,
  Download,
  FileText,
  Shield,
  Clock,
  Hash,
  Eye,
  RefreshCw,
  Folder,
  CheckCircle2,
  AlertTriangle,
  Copy,
  ExternalLink,
} from "lucide-react";

const EvidenceViewer = () => {
  const [evidencePacks, setEvidencePacks] = useState([]);
  const [selectedPack, setSelectedPack] = useState(null);
  const [battles, setBattles] = useState([]);
  const [selectedBattle, setSelectedBattle] = useState("");
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [evidenceRes, battlesRes] = await Promise.all([
        evidenceAPI.getAll(),
        battleAPI.getAll(),
      ]);
      setEvidencePacks(evidenceRes.data);
      setBattles(battlesRes.data);
      if (evidenceRes.data.length > 0) {
        setSelectedPack(evidenceRes.data[0]);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateEvidencePack = async () => {
    if (!selectedBattle) {
      toast.error("Please select a battle");
      return;
    }
    setGenerating(true);
    try {
      const response = await evidenceAPI.generate(selectedBattle);
      setEvidencePacks([...evidencePacks, response.data]);
      setSelectedPack(response.data);
      toast.success("Evidence pack generated!");
    } catch (error) {
      toast.error("Failed to generate evidence pack");
    } finally {
      setGenerating(false);
    }
  };

  const exportPack = async () => {
    if (!selectedPack) return;
    try {
      const response = await evidenceAPI.export(selectedPack.id);
      const data = response.data;
      
      // Create downloadable JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success("Evidence pack exported!");
    } catch (error) {
      toast.error("Export failed");
    }
  };

  const copyChecksum = () => {
    if (selectedPack?.checksum) {
      navigator.clipboard.writeText(selectedPack.checksum);
      toast.success("Checksum copied to clipboard!");
    }
  };

  return (
    <div className="h-full flex" data-testid="evidence-viewer">
      {/* Pack List */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold mb-4">Evidence Packs</h2>
          
          {/* Generate New */}
          <div className="space-y-2">
            <Select value={selectedBattle} onValueChange={setSelectedBattle}>
              <SelectTrigger data-testid="battle-select-evidence">
                <SelectValue placeholder="Select battle" />
              </SelectTrigger>
              <SelectContent>
                {battles.filter(b => b.status === "completed").map((battle) => (
                  <SelectItem key={battle.id} value={battle.id}>
                    {battle.scenario_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              className="w-full"
              onClick={generateEvidencePack}
              disabled={!selectedBattle || generating}
              data-testid="generate-evidence-btn"
              data-explain="Generate Evidence Pack"
              data-explain-title="Evidence pack generated"
              data-explain-summary="Creates a compliance-grade evidence bundle from a completed battle with rule triggers, scores, and artifacts."
              data-explain-rules="EV-001,EV-014"
              data-explain-evidence="Battle timeline,Rule hits,Score traces"
            >
              <FileSearch className={`h-4 w-4 mr-2 ${generating ? 'animate-spin' : ''}`} />
              Generate Pack
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {evidencePacks.map((pack) => (
              <div
                key={pack.id}
                onClick={() => setSelectedPack(pack)}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedPack?.id === pack.id
                    ? "border-yellow-500 bg-yellow-500/10"
                    : "border-border hover:border-zinc-600 bg-card"
                }`}
                data-testid={`evidence-pack-${pack.id}`}
              >
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4 text-yellow-400" />
                  <span className="font-mono text-sm truncate">
                    {pack.id.slice(0, 8)}...
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {new Date(pack.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {pack.triggered_rules?.length || 0} rules
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {Math.round(pack.confidence * 100)}% conf.
                  </Badge>
                </div>
              </div>
            ))}
            {evidencePacks.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <FileSearch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No evidence packs yet</p>
                <p className="text-sm">Generate from a battle</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Pack Details */}
      <div className="flex-1 overflow-hidden">
        {selectedPack ? (
          <ScrollArea className="h-full">
            <div className="p-6 space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-2">
                    <FileSearch className="h-6 w-6 text-yellow-400" />
                    Evidence Pack
                  </h1>
                  <p className="text-muted-foreground mt-1 font-mono text-sm">
                    ID: {selectedPack.id}
                  </p>
                </div>
                <Button
                  onClick={exportPack}
                  data-testid="export-evidence-btn"
                  data-explain="Export Evidence Pack"
                  data-explain-title="Evidence export"
                  data-explain-summary="Packages evidence into a tamper-evident archive with checksum and audit trail."
                  data-explain-rules="EV-021,EV-032"
                  data-explain-evidence="Checksum,Artifacts,Audit log"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export ZIP
                </Button>
              </div>

              {/* XAI Narrative */}
              <Card className="border-border border-yellow-500/30 bg-yellow-500/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-yellow-400">
                    <FileText className="h-5 w-5" />
                    Gold Team Explanation (XAI Narrative)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{selectedPack.narrative}</p>
                </CardContent>
              </Card>

              {/* Metadata Grid */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <Shield className="h-4 w-4" />
                      <span className="text-sm">Triggered Rules</span>
                    </div>
                    <div className="space-y-1">
                      {selectedPack.triggered_rules?.length > 0 ? (
                        selectedPack.triggered_rules.map((rule, idx) => (
                          <Badge key={idx} variant="outline" className="mr-1 text-xs font-mono">
                            {rule}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground text-sm">No rules triggered</span>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="text-sm">Confidence Score</span>
                    </div>
                    <p className="text-3xl font-bold font-mono">
                      {Math.round(selectedPack.confidence * 100)}%
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <Clock className="h-4 w-4" />
                      <span className="text-sm">Created</span>
                    </div>
                    <p className="text-sm font-mono">
                      {new Date(selectedPack.created_at).toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Contributing Factors */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-400" />
                    Contributing Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedPack.contributing_factors?.map((factor, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                        <span className="font-medium">{factor.factor}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-zinc-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-orange-400 rounded-full"
                              style={{ width: `${factor.weight * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-mono w-12">
                            {Math.round(factor.weight * 100)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Checksum & Lineage */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hash className="h-5 w-5 text-green-400" />
                    Integrity & Lineage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-muted-foreground">Checksum (SHA-256)</label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="flex-1 p-2 bg-black/30 rounded font-mono text-xs break-all">
                          {selectedPack.checksum || "Not computed"}
                        </code>
                        <Button variant="ghost" size="icon" onClick={copyChecksum} data-testid="copy-checksum-btn">
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm text-muted-foreground">Battle Reference</label>
                      <p className="font-mono text-sm mt-1">{selectedPack.battle_id}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Logs Preview */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-blue-400" />
                    Event Logs (Last 10)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-black/30 rounded-lg p-4 max-h-64 overflow-auto">
                    <pre className="font-mono text-xs whitespace-pre-wrap">
                      {JSON.stringify(selectedPack.logs, null, 2)}
                    </pre>
                  </div>
                </CardContent>
              </Card>

              {/* Approvals */}
              {selectedPack.approvals?.length > 0 && (
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-400" />
                      Approvals
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {selectedPack.approvals.map((approval, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-zinc-800/50 rounded">
                          <span className="font-mono text-sm">{approval.approver_id}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(approval.timestamp).toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </ScrollArea>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <FileSearch className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select an evidence pack to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceViewer;
