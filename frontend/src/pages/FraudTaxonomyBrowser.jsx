import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Skeleton } from "../components/ui/skeleton";
import { BookOpen, FolderTree, Search, ShieldAlert } from "lucide-react";

const FraudTaxonomyBrowser = () => {
  const [loading, setLoading] = useState(true);
  const [families, setFamilies] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState("all");
  const [search, setSearch] = useState("");
  const [railFilter, setRailFilter] = useState("all");

  useEffect(() => {
    const loadTaxonomy = async () => {
      try {
        const response = await fetch("/banking_fraud_taxonomy_catalog_120.json");
        const data = await response.json();
        setFamilies(data.families || []);
        setScenarios(data.scenarios || []);
      } catch (error) {
        setFamilies([]);
        setScenarios([]);
      } finally {
        setLoading(false);
      }
    };
    loadTaxonomy();
  }, []);

  const filteredScenarios = useMemo(() => {
    return scenarios.filter((scenario) => {
      const matchesFamily = selectedFamily === "all" || scenario.family_id === selectedFamily;
      const matchesSearch = scenario.scenario_name?.toLowerCase().includes(search.toLowerCase());
      const matchesRail =
        railFilter === "all" ||
        (scenario.payment_rails || []).map((rail) => rail.toLowerCase()).includes(railFilter.toLowerCase());
      return matchesFamily && matchesSearch && matchesRail;
    });
  }, [scenarios, selectedFamily, search, railFilter]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Knowledge Base</p>
            <h1 className="text-2xl font-semibold">Fraud Taxonomy Browser</h1>
          </div>
          <Badge className="bg-purple-500/15 text-purple-300 border border-purple-500/30" data-testid="taxonomy-status">
            {scenarios.length} scenarios indexed
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Explore the 120-scenario fraud taxonomy, drill into families, and map coverage gaps against current defenses.
        </p>
      </header>

      <Card className="border-border" data-testid="taxonomy-filters">
        <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search scenarios, indicators, or entry vectors"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                data-testid="taxonomy-search"
              />
            </div>
          </div>
          <Select value={selectedFamily} onValueChange={setSelectedFamily}>
            <SelectTrigger className="w-full lg:w-[220px]" data-testid="taxonomy-family-filter">
              <SelectValue placeholder="Family" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Families</SelectItem>
              {families.map((family) => (
                <SelectItem key={family.family_id || family.id} value={family.family_id || family.id}>
                  {family.family_name || family.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={railFilter} onValueChange={setRailFilter}>
            <SelectTrigger className="w-full lg:w-[220px]" data-testid="taxonomy-rail-filter">
              <SelectValue placeholder="Payment Rail" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Rails</SelectItem>
              <SelectItem value="cards">Cards</SelectItem>
              <SelectItem value="ach">ACH</SelectItem>
              <SelectItem value="wire">Wire</SelectItem>
              <SelectItem value="p2p">P2P</SelectItem>
              <SelectItem value="instant">Instant</SelectItem>
              <SelectItem value="check">Checks</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Card className="border-border" data-testid="taxonomy-families">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FolderTree className="h-4 w-4 text-purple-400" />
              Families
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[480px]">
              <div className="divide-y divide-border">
                {loading && (
                  <div className="p-4 space-y-3">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                )}
                {!loading && families.length === 0 && (
                  <div className="p-4 text-sm text-muted-foreground">No families loaded.</div>
                )}
                {families.map((family) => (
                  <button
                    key={family.family_id || family.id}
                    type="button"
                    className={`w-full text-left px-4 py-3 transition-colors ${
                      selectedFamily === (family.family_id || family.id) ? "bg-purple-500/10" : "hover:bg-muted/40"
                    }`}
                    onClick={() => setSelectedFamily(family.family_id || family.id)}
                    data-testid={`taxonomy-family-${family.family_id || family.id}`}
                  >
                    <p className="text-sm font-medium">{family.family_name || family.name}</p>
                    <p className="text-xs text-muted-foreground">{family.description || "Family overview"}</p>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="border-border" data-testid="taxonomy-scenarios">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-blue-400" />
              Scenarios
            </CardTitle>
            <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30">
              {filteredScenarios.length} results
            </Badge>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[480px]">
              <div className="divide-y divide-border">
                {loading && (
                  <div className="p-4 space-y-3">
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                )}
                {!loading && filteredScenarios.length === 0 && (
                  <div className="p-4 text-sm text-muted-foreground">No scenarios match the selected filters.</div>
                )}
                {filteredScenarios.map((scenario) => (
                  <div key={scenario.scenario_id || scenario.scenario_name} className="px-5 py-4 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium">{scenario.scenario_name}</p>
                        <p className="text-xs text-muted-foreground">{scenario.entry_vector || "Entry vector unspecified"}</p>
                      </div>
                      <Badge className="bg-red-500/15 text-red-300 border border-red-500/30">{scenario.family_id}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(scenario.payment_rails || []).slice(0, 4).map((rail) => (
                        <Badge key={rail} variant="outline" className="border-border text-xs">
                          {rail}
                        </Badge>
                      ))}
                      {(scenario.payment_rails || []).length > 4 && (
                        <Badge variant="outline" className="border-border text-xs">+{scenario.payment_rails.length - 4}</Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <ShieldAlert className="h-3.5 w-3.5 text-orange-400" />
                      {(scenario.telemetry_indicators || []).slice(0, 2).join(" • ") || "Indicators pending"}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FraudTaxonomyBrowser;
