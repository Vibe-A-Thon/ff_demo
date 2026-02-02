import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Label } from "../components/ui/label";
import { ScrollArea } from "../components/ui/scroll-area";
import { settingsAPI } from "../lib/api";
import { toast } from "sonner";

const PROVIDER_OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "local", label: "Local / vLLM" },
];

const LLMProviderSetup = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    provider: "openai",
    model: "gpt-4o-mini",
    version_pin: "",
    api_key: "",
    base_url: "",
  });

  const loadSettings = useCallback(async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.get();
      const llm = response.data?.llm || {};
      setForm({
        provider: llm.provider || "openai",
        model: llm.model || "gpt-4o-mini",
        version_pin: llm.version_pin || "",
        api_key: llm.api_key || "",
        base_url: llm.base_url || "",
      });
    } catch (error) {
      toast.error("Failed to load LLM settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = await settingsAPI.get();
      const current = payload.data || {};
      const update = {
        ...current,
        llm: { ...form },
      };
      await settingsAPI.update(update);
      toast.success("LLM settings updated");
    } catch (error) {
      toast.error("Failed to update LLM settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-sm text-muted-foreground">Loading LLM settings...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col" data-testid="llm-provider-setup">
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-lg">LLM Provider Setup</CardTitle>
              <p className="text-xs text-muted-foreground">
                Configure provider details for demo routing. API key updates apply after service restart.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Provider</Label>
                  <Select
                    value={form.provider}
                    onValueChange={(value) => setForm((prev) => ({ ...prev, provider: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {PROVIDER_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Input
                    value={form.model}
                    onChange={(event) => setForm((prev) => ({ ...prev, model: event.target.value }))}
                    placeholder="gpt-4o-mini"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Version Pin</Label>
                  <Input
                    value={form.version_pin}
                    onChange={(event) => setForm((prev) => ({ ...prev, version_pin: event.target.value }))}
                    placeholder="2025-11-20"
                  />
                </div>
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input
                    type="password"
                    value={form.api_key}
                    onChange={(event) => setForm((prev) => ({ ...prev, api_key: event.target.value }))}
                    placeholder="sk-..."
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label>Base URL (optional)</Label>
                  <Input
                    value={form.base_url}
                    onChange={(event) => setForm((prev) => ({ ...prev, base_url: event.target.value }))}
                    placeholder="https://api.openai.com/v1"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSave} disabled={saving} data-testid="llm-provider-save">
                  {saving ? "Saving..." : "Save Settings"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
};

export default LLMProviderSetup;
