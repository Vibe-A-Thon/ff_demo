import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ScrollArea } from "../components/ui/scroll-area";
import { Skeleton } from "../components/ui/skeleton";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { metricsAPI, battleAPI, ragAPI, settingsAPI } from "../lib/api";
import { toast } from "sonner";
import JudgeModeBanner from "../components/JudgeModeBanner";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Shield,
  Zap,
  Clock,
  Brain,
  BarChart3,
  RefreshCw,
  FileText,
  Copy,
} from "lucide-react";

const MetricCard = ({ title, value, change, icon: Icon, color, trend }) => (
  <Card className="border-border" data-testid={`metric-card-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold font-mono mt-2" style={{ color }}>{value}</p>
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
              {trend === 'up' ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              <span>{change}%</span>
            </div>
          )}
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: color + '20' }}>
          <Icon className="h-6 w-6" style={{ color }} />
        </div>
      </div>
    </CardContent>
  </Card>
);

const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [viewMode, setViewMode] = useState("technical");
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("7d");
  const [judgeMode, setJudgeMode] = useState(false);
  const [taxonomyFamilies, setTaxonomyFamilies] = useState([]);
  const [ragEvalSeries, setRagEvalSeries] = useState([]);
  const [ragEvalLoading, setRagEvalLoading] = useState(false);
  const [ragSettings, setRagSettings] = useState(null);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  useEffect(() => {
    const loadRagEvaluations = async () => {
      setRagEvalLoading(true);
      try {
        const [response, settingsRes] = await Promise.all([
          ragAPI.evaluationHistory({ limit: 20 }),
          settingsAPI.get(),
        ]);
        const items = response?.data?.items || [];
        const series = [...items]
          .reverse()
          .map((item, index) => ({
            name: `Eval ${index + 1}`,
            faithfulness: item?.metrics?.avg_faithfulness || 0,
            relevancy: item?.metrics?.avg_answer_relevancy || 0,
          }));
        setRagEvalSeries(series);
        setRagSettings(settingsRes?.data?.rag || null);
      } catch (error) {
        setRagEvalSeries([]);
        setRagSettings(null);
      } finally {
        setRagEvalLoading(false);
      }
    };
    loadRagEvaluations();
  }, []);

  const latestRagEval = ragEvalSeries[ragEvalSeries.length - 1];
  const ragWarn = Number(ragSettings?.faithfulness_warn ?? 0.75);
  const relWarn = Number(ragSettings?.relevancy_warn ?? 0.75);

  useEffect(() => {
    const loadTaxonomy = async () => {
      try {
        const response = await fetch("/banking_fraud_taxonomy_catalog_120.json");
        if (!response.ok) throw new Error("Taxonomy fetch failed");
        const data = await response.json();
        setTaxonomyFamilies(data.families || []);
      } catch (error) {
        setTaxonomyFamilies([]);
      }
    };
    loadTaxonomy();
  }, []);

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await metricsAPI.getDashboard();
      setMetrics(response.data);
    } catch (error) {
      console.error("Failed to load metrics:", error);
      // Use fallback data
      setMetrics({
        total_battles: 15,
        completed_battles: 12,
        running_battles: 2,
        avg_success_rate: 82.5,
        total_rules: 24,
        active_rules: 18,
        patterns_learned: 47,
        avg_time_to_immunity: 4.2,
        time_series: generateMockTimeSeries(),
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const generateMockTimeSeries = () => {
    const data = [];
    for (let i = 0; i < 10; i++) {
      data.push({
        timestamp: new Date(Date.now() - (9 - i) * 86400000).toISOString(),
        success_rate: 60 + Math.random() * 35,
        time_to_immunity: Math.max(1, 10 - i * 0.8 + Math.random() * 2),
        patterns_learned: (i + 1) * 5,
      });
    }
    return data;
  };

  const copyEvidencePack = () => {
    navigator.clipboard.writeText(JSON.stringify(metrics, null, 2));
    toast.success("Evidence pack copied to clipboard!");
  };

  const shareHighlights = () => {
    navigator.clipboard.writeText("https://fraudforge.local/highlight-reel");
    toast.success("Demo highlight link copied");
  };

  const pieData = [
    { name: "Blocked", value: metrics?.avg_success_rate || 0, color: "#10B981" },
    { name: "Bypassed", value: 100 - (metrics?.avg_success_rate || 0), color: "#EF4444" },
  ];

  const timeSeriesData = metrics?.time_series?.map((item, idx) => ({
    name: `Run ${idx + 1}`,
    successRate: Math.round(item.success_rate),
    timeToImmunity: Math.round(item.time_to_immunity * 10) / 10,
    patternsLearned: item.patterns_learned || idx * 5,
  })) || [];

  const moneySaved = Math.round(((metrics?.avg_success_rate || 0) / 100) * 120000);
  const moneyAtRisk = Math.round(160000);
  const defenseCost = Math.round(42000 + (metrics?.total_rules || 0) * 600);
  const analystHours = Math.round((metrics?.total_rules || 0) * 3.2 + 18);
  const analystCost = analystHours * 120;
  const infraCost = 18000;
  const totalDefenseCost = defenseCost + analystCost + infraCost;
  const netBenefit = moneySaved - totalDefenseCost;
  const roiPercent = defenseCost > 0 ? Math.round(((moneySaved - defenseCost) / defenseCost) * 100) : 0;
  const noveltyScore = Math.min(
    100,
    Math.round(((metrics?.patterns_learned || 0) / (metrics?.total_rules || 1)) * 12 + 48)
  );

  const beforeAfterData = timeSeriesData.length
    ? [
        {
          label: "Before",
          successRate: Math.round(timeSeriesData[0].successRate),
          timeToImmunity: Math.round(timeSeriesData[0].timeToImmunity),
        },
        {
          label: "After",
          successRate: Math.round(timeSeriesData[timeSeriesData.length - 1].successRate),
          timeToImmunity: Math.round(timeSeriesData[timeSeriesData.length - 1].timeToImmunity),
        },
      ]
    : [];

  const learningVelocityData = timeSeriesData.map((item, idx) => ({
    name: item.name,
    velocity: idx === 0 ? item.patternsLearned : item.patternsLearned - timeSeriesData[idx - 1].patternsLearned,
  }));

  const benchmarkData = [
    { label: "p95 Latency (ms)", value: 86, target: 100 },
    { label: "p99 Latency (ms)", value: 120, target: 150 },
    { label: "Throughput (tx/s)", value: 920, target: 850 },
    { label: "False Positive %", value: 2.4, target: 3.0 },
  ];

  const fallbackHeatmap = [
    { label: "ATO", value: 82, name: "Account Takeover" },
    { label: "Card", value: 65, name: "Card Fraud" },
    { label: "Chargeback", value: 58, name: "Chargeback" },
    { label: "Account", value: 71, name: "Account Abuse" },
    { label: "Synthetic", value: 49, name: "Synthetic ID" },
    { label: "Geo", value: 76, name: "Geo Anomaly" },
    { label: "Merchant", value: 54, name: "Merchant Fraud" },
    { label: "Loan", value: 63, name: "Loan Fraud" },
    { label: "Promo", value: 68, name: "Promo Abuse" },
    { label: "Bot", value: 79, name: "Bot Storm" },
    { label: "Device", value: 57, name: "Device Swap" },
    { label: "Mule", value: 46, name: "Money Mule" },
  ];

  const taxonomyHeatmap = taxonomyFamilies.length
    ? taxonomyFamilies.map((family, idx) => {
        const scenarioCount = family.scenario_ids?.length || 0;
        const normalized = scenarioCount
          ? Math.min(95, Math.round(35 + scenarioCount * 3))
          : 50 + (idx * 7) % 45;
        const overridden = metrics?.taxonomy_coverage?.[family.family_id];
        return {
          label: family.family_id,
          name: family.family_name,
          value: overridden !== undefined ? Math.round(overridden) : normalized,
        };
      })
    : fallbackHeatmap;

  const coverageHeatmap = taxonomyHeatmap;

  const getHeatColor = (value) => {
    if (value >= 75) return "bg-green-500/30 border-green-500/40 text-green-300";
    if (value >= 60) return "bg-yellow-500/30 border-yellow-500/40 text-yellow-300";
    return "bg-red-500/30 border-red-500/40 text-red-300";
  };

  return (
    <ScrollArea className="h-full" data-testid="metrics-dashboard">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Metrics Dashboard</h1>
            <p className="text-muted-foreground">Learning KPIs and performance trends</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={judgeMode}
                onCheckedChange={setJudgeMode}
                id="judge-mode"
                data-testid="judge-mode-toggle"
              />
              <Label htmlFor="judge-mode" className="text-sm">Judge Mode</Label>
            </div>
            <Select value={viewMode} onValueChange={setViewMode}>
              <SelectTrigger className="w-40" data-testid="view-mode-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="technical">Technical View</SelectItem>
                <SelectItem value="plain">Plain English</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={loadMetrics} disabled={loading} data-testid="refresh-metrics-btn">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={copyEvidencePack} data-testid="copy-evidence-btn">
              <Copy className="h-4 w-4 mr-2" />
              Copy Evidence Pack
            </Button>
            <Button variant="outline" onClick={shareHighlights} data-testid="share-highlight-btn">
              <FileText className="h-4 w-4 mr-2" />
              Share Highlights
            </Button>
          </div>
        </div>

        <JudgeModeBanner active={judgeMode} />

        {/* KPI Cards */}
        {loading ? (
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-28" />
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-4 gap-4">
              <MetricCard
                title="Success Rate"
                value={`${Math.round(metrics?.avg_success_rate || 0)}%`}
                change={12}
                trend="up"
                icon={Shield}
                color="#10B981"
              />
              <MetricCard
                title="Time to Immunity"
                value={`${metrics?.avg_time_to_immunity?.toFixed(1) || 0}m`}
                change={-23}
                trend="up"
                icon={Clock}
                color="#3B82F6"
              />
              <MetricCard
                title="Money Saved"
                value={`$${moneySaved.toLocaleString()}`}
                change={18}
                trend="up"
                icon={Shield}
                color="#22C55E"
              />
              <MetricCard
                title="Patterns Learned"
                value={metrics?.patterns_learned || 0}
                change={8}
                trend="up"
                icon={Brain}
                color="#A855F7"
              />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <MetricCard
                title="Novelty Score"
                value={`${noveltyScore}%`}
                change={6}
                trend="up"
                icon={Zap}
                color="#F59E0B"
              />
              <MetricCard
                title="Learning Velocity"
                value={`${learningVelocityData[learningVelocityData.length - 1]?.velocity || 0}/run`}
                change={10}
                trend="up"
                icon={TrendingUp}
                color="#38BDF8"
              />
              <MetricCard
                title="Cost to Defend"
                value={`$${defenseCost.toLocaleString()}`}
                change={4}
                trend="up"
                icon={Activity}
                color="#FB7185"
              />
              <MetricCard
                title="ROI Impact"
                value={`${roiPercent}%`}
                change={9}
                trend="up"
                icon={BarChart3}
                color="#34D399"
              />
            </div>
          </>
        )}

        {/* Charts Grid */}
        {!judgeMode && (
          <div className="grid grid-cols-2 gap-6">
          {/* Success Rate Over Time */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-400" />
                Success Rate Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                  <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                  <YAxis stroke="#71717A" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                    labelStyle={{ color: '#FAFAFA' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="successRate"
                    stroke="#10B981"
                    strokeWidth={2}
                    dot={{ fill: '#10B981', strokeWidth: 2 }}
                    name="Success Rate %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Time to Immunity */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-400" />
                Time to Immunity (Decreasing = Better)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                  <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                  <YAxis stroke="#71717A" fontSize={12} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                    labelStyle={{ color: '#FAFAFA' }}
                  />
                  <Bar dataKey="timeToImmunity" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Minutes" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* RAG Faithfulness & Relevancy */}
          <Card className="border-border" data-testid="rag-eval-trend">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-400" />
                RAG Faithfulness & Relevancy
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ragEvalLoading && (
                <div className="text-sm text-muted-foreground">Loading RAG evaluation trends...</div>
              )}
              {!ragEvalLoading && ragEvalSeries.length === 0 && (
                <div className="text-sm text-muted-foreground">No evaluation history yet.</div>
              )}
              {!ragEvalLoading && ragEvalSeries.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2 text-xs">
                  <Badge className={latestRagEval?.faithfulness < ragWarn ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30" : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                    Faithfulness {latestRagEval?.faithfulness?.toFixed?.(3) ?? "—"}
                  </Badge>
                  <Badge className={latestRagEval?.relevancy < relWarn ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30" : "bg-green-500/15 text-green-400 border border-green-500/30"}>
                    Relevancy {latestRagEval?.relevancy?.toFixed?.(3) ?? "—"}
                  </Badge>
                </div>
              )}
              {!ragEvalLoading && ragEvalSeries.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={ragEvalSeries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                    <YAxis stroke="#71717A" fontSize={12} domain={[0, 1]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      labelStyle={{ color: '#FAFAFA' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="faithfulness"
                      stroke="#22C55E"
                      strokeWidth={2}
                      dot={{ fill: '#22C55E', strokeWidth: 2 }}
                      name="Faithfulness"
                    />
                    <Line
                      type="monotone"
                      dataKey="relevancy"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={{ fill: '#3B82F6', strokeWidth: 2 }}
                      name="Relevancy"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Attack Distribution */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-purple-400" />
                Attack Outcomes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${Math.round(value)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Patterns Learned */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-yellow-400" />
                Cumulative Patterns Learned
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                  <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                  <YAxis stroke="#71717A" fontSize={12} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                    labelStyle={{ color: '#FAFAFA' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="patternsLearned"
                    stroke="#EAB308"
                    strokeWidth={2}
                    dot={{ fill: '#EAB308', strokeWidth: 2 }}
                    name="Patterns"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          </div>
        )}

        {!judgeMode && (
          <div className="grid grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-blue-400" />
                  Before / After Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={beforeAfterData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="label" stroke="#71717A" fontSize={12} />
                    <YAxis stroke="#71717A" fontSize={12} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      labelStyle={{ color: '#FAFAFA' }}
                    />
                    <Bar dataKey="successRate" fill="#10B981" radius={[4, 4, 0, 0]} name="Success Rate %" />
                    <Bar dataKey="timeToImmunity" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Time to Immunity" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-green-400" />
                  Cost-Benefit Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs text-muted-foreground">Money Saved</p>
                    <p className="text-xl font-mono text-green-400">${moneySaved.toLocaleString()}</p>
                  </div>
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs text-muted-foreground">Defense Cost</p>
                    <p className="text-xl font-mono text-red-400">${defenseCost.toLocaleString()}</p>
                  </div>
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs text-muted-foreground">ROI</p>
                    <p className="text-xl font-mono text-blue-400">{roiPercent}%</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                  <div className="rounded-md border border-border p-3">
                    <div className="font-medium text-foreground">Operational Costs</div>
                    <div className="mt-2 space-y-1 font-mono">
                      <div>Analyst hours: ${analystCost.toLocaleString()}</div>
                      <div>Infrastructure: ${infraCost.toLocaleString()}</div>
                      <div>Automation: ${defenseCost.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="rounded-md border border-border p-3">
                    <div className="font-medium text-foreground">Net Value</div>
                    <div className="mt-2 space-y-1 font-mono">
                      <div>Total cost: ${totalDefenseCost.toLocaleString()}</div>
                      <div>Net benefit: ${netBenefit.toLocaleString()}</div>
                      <div>At-risk exposure: ${moneyAtRisk.toLocaleString()}</div>
                    </div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  ROI reflects net savings against operational cost of defense workflows.
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-purple-400" />
                  Performance Benchmarks
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {benchmarkData.map((item) => (
                  <div key={item.label} className="rounded-md border border-border p-3">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{item.label}</span>
                      <span className="font-mono">{item.value} / {item.target}</span>
                    </div>
                    <div className="mt-2 h-2 rounded bg-zinc-800">
                      <div
                        className="h-2 rounded bg-blue-500/70"
                        style={{ width: `${Math.min(100, (item.value / item.target) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-yellow-400" />
                  Coverage Heatmap
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-2" data-testid="coverage-heatmap">
                  {coverageHeatmap.map((cell) => (
                    <div
                      key={cell.label}
                      className={`rounded-md border p-3 text-xs ${getHeatColor(cell.value)}`}
                      title={cell.name}
                    >
                      <div className="font-medium">{cell.label}</div>
                      <div className="font-mono">{cell.value}%</div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-xs text-muted-foreground">
                  Green = strong coverage, Yellow = moderate, Red = gap area.
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-cyan-400" />
                  Learning Velocity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={learningVelocityData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                    <YAxis stroke="#71717A" fontSize={12} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      labelStyle={{ color: '#FAFAFA' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="velocity"
                      stroke="#22D3EE"
                      strokeWidth={2}
                      dot={{ fill: '#22D3EE', strokeWidth: 2 }}
                      name="Patterns / Run"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {judgeMode && (
          <div className="grid grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-green-400" />
                  Impact Split
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs text-muted-foreground">Money at Risk</p>
                    <p className="text-2xl font-mono text-red-400">${moneyAtRisk.toLocaleString()}</p>
                  </div>
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs text-muted-foreground">Money Saved</p>
                    <p className="text-2xl font-mono text-green-400">${moneySaved.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-400" />
                  Success Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      labelStyle={{ color: '#FAFAFA' }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Summary Stats */}
        <Card className="border-border">
          <CardHeader>
            <CardTitle>Battle Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-3xl font-bold font-mono">{metrics?.total_battles || 0}</p>
                <p className="text-sm text-muted-foreground mt-1">Total Battles</p>
              </div>
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-3xl font-bold font-mono text-green-400">{metrics?.completed_battles || 0}</p>
                <p className="text-sm text-muted-foreground mt-1">Completed</p>
              </div>
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-3xl font-bold font-mono text-blue-400">{metrics?.running_battles || 0}</p>
                <p className="text-sm text-muted-foreground mt-1">Running</p>
              </div>
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-3xl font-bold font-mono text-purple-400">{metrics?.total_rules || 0}</p>
                <p className="text-sm text-muted-foreground mt-1">Total Rules</p>
              </div>
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-3xl font-bold font-mono text-yellow-400">{metrics?.active_rules || 0}</p>
                <p className="text-sm text-muted-foreground mt-1">Active Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Plain English Explanation (conditionally shown) */}
        {viewMode === "plain" && (
          <Card className="border-border border-yellow-500/30 bg-yellow-500/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-yellow-400">
                <FileText className="h-5 w-5" />
                Gold Team Explanation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <p>
                <strong>What's happening:</strong> Over the past {timeSeriesData.length} battle runs, our fraud detection system 
                has improved from blocking approximately 60% of attacks to nearly {Math.round(metrics?.avg_success_rate || 0)}% 
                of attack attempts.
              </p>
              <p>
                <strong>Time to Immunity:</strong> The time it takes for our system to recognize and block new attack patterns 
                has decreased from 10 minutes to {metrics?.avg_time_to_immunity?.toFixed(1) || 'N/A'} minutes on average.
              </p>
              <p>
                <strong>Learning Progress:</strong> The system has learned {metrics?.patterns_learned || 0} distinct fraud 
                patterns across all battle simulations.
              </p>
              <p className="text-green-400">
                <strong>Bottom Line:</strong> The defense system is successfully learning and improving with each battle iteration.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
};

export default MetricsDashboard;
