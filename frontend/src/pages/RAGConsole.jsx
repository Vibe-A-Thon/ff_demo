import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { ScrollArea } from "../components/ui/scroll-area";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { ragAPI } from "../lib/api";
import { toast } from "sonner";
import { Brain, Search, Database, Sparkles } from "lucide-react";

const RAGConsole = () => {
  const [collections, setCollections] = useState([]);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedCollection, setSelectedCollection] = useState("all");
  const [topK, setTopK] = useState([5]);
  const [hybrid, setHybrid] = useState(true);
  const [includeGraph, setIncludeGraph] = useState(true);
  const [response, setResponse] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const loadRag = async () => {
      setLoading(true);
      try {
        const [collectionsRes, docsRes] = await Promise.all([
          ragAPI.listCollections(),
          ragAPI.listDocuments({ limit: 25 }),
        ]);
        setCollections(collectionsRes?.data?.collections || []);
        setDocs(docsRes?.data || []);
      } catch (error) {
        toast.error("Failed to load RAG collections.");
        setCollections([]);
        setDocs([]);
      } finally {
        setLoading(false);
      }
    };
    loadRag();
  }, []);

  const filteredDocs = useMemo(() => {
    if (selectedCollection === "all") return docs;
    return docs.filter((doc) => doc.collection === selectedCollection);
  }, [docs, selectedCollection]);

  const runQuery = async () => {
    if (!query.trim()) {
      toast.error("Enter a query to run retrieval.");
      return;
    }
    setRunning(true);
    try {
      const payload = {
        query,
        collections: selectedCollection === "all" ? null : [selectedCollection],
        top_k: topK[0],
        use_hybrid: hybrid,
        include_graph_context: includeGraph,
        synthetic_only: true,
      };
      const result = await ragAPI.query(payload);
      setResponse(result?.data || null);
      toast.success("RAG response generated.");
    } catch (error) {
      toast.error("RAG query failed.");
    } finally {
      setRunning(false);
    }
  };

  const seedRag = async () => {
    try {
      await ragAPI.seed();
      toast.success("RAG seed executed.");
    } catch (error) {
      toast.error("Failed to seed RAG data.");
    }
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">RAG Ops</p>
            <h1 className="text-2xl font-semibold">RAG Console</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-500/15 text-purple-300 border border-purple-500/30" data-testid="rag-collections">
              {collections.length} collections
            </Badge>
            <Button variant="outline" size="sm" onClick={seedRag} data-testid="rag-seed">
              <Database className="mr-2 h-4 w-4" />
              Seed RAG
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Query the synthetic knowledge base, inspect hits, and review context windows used by the RAG pipeline.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-border" data-testid="rag-query">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-400" />
              Retrieval Query
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="rag-query-input">Question</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="rag-query-input"
                  className="pl-9"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about fraud patterns, rules, or taxonomy signals"
                  data-testid="rag-query-input"
                />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Collection Scope</Label>
                <Select value={selectedCollection} onValueChange={setSelectedCollection}>
                  <SelectTrigger data-testid="rag-collection">
                    <SelectValue placeholder="All collections" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All collections</SelectItem>
                    {collections.map((collection) => (
                      <SelectItem key={collection} value={collection}>
                        {collection}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Top-K</Label>
                <Slider
                  value={topK}
                  onValueChange={setTopK}
                  max={10}
                  min={1}
                  step={1}
                  data-testid="rag-topk"
                />
                <div className="text-xs text-muted-foreground">{topK[0]} hits</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <Switch checked={hybrid} onCheckedChange={setHybrid} data-testid="rag-hybrid" />
                <Label>Hybrid Retrieval</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={includeGraph} onCheckedChange={setIncludeGraph} data-testid="rag-graph" />
                <Label>Include Graph Context</Label>
              </div>
            </div>
            <Button onClick={runQuery} disabled={running} data-testid="rag-run">
              <Sparkles className="mr-2 h-4 w-4" />
              {running ? "Running..." : "Run Query"}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="rag-docs">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-400" />
              Corpus Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[420px]">
              <div className="divide-y divide-border">
                {loading && (
                  <div className="p-4 text-sm text-muted-foreground">Loading documents...</div>
                )}
                {!loading && filteredDocs.length === 0 && (
                  <div className="p-4 text-sm text-muted-foreground">No documents loaded yet.</div>
                )}
                {filteredDocs.map((doc) => (
                  <div key={doc.id} className="px-4 py-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{doc.title || doc.collection}</p>
                      <Badge variant="outline" className="border-border text-xs">
                        {doc.collection}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {doc.content}
                    </p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border" data-testid="rag-response">
        <CardHeader>
          <CardTitle className="text-lg">RAG Response</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!response && <p className="text-sm text-muted-foreground">Run a query to view the generated response.</p>}
          {response && (
            <div className="space-y-4">
              <div className="rounded-md border border-border bg-muted/30 p-4 text-sm">
                {response.answer}
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Top Hits</p>
                  <div className="space-y-2">
                    {(response.hits || []).map((hit) => (
                      <div key={hit.doc_id} className="rounded-md border border-border p-3 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{hit.title || hit.collection}</span>
                          <Badge variant="outline" className="border-border text-[10px]">
                            {hit.score}
                          </Badge>
                        </div>
                        <p className="text-muted-foreground mt-1">{hit.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Context Window</p>
                  <div className="space-y-2">
                    {(response.context || []).map((chunk, idx) => (
                      <div key={`ctx-${idx}`} className="rounded-md border border-border p-3 text-xs text-muted-foreground">
                        {chunk}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RAGConsole;
