import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { xaiAPI } from "../lib/api";
import { Bot, RefreshCw, X } from "lucide-react";

const XAICommentator = ({ screen, role, summary, highlights = [] }) => {
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [timestamp, setTimestamp] = useState("");

  const payload = useMemo(() => ({
    screen,
    role,
    summary,
    highlights,
    timestamp: new Date().toISOString(),
  }), [screen, role, summary, highlights]);

  const fetchCommentary = async () => {
    setLoading(true);
    try {
      const response = await xaiAPI.commentor(payload);
      setMessage(response?.data?.text || "Operational commentary unavailable.");
      setTimestamp(response?.data?.timestamp || new Date().toISOString());
    } catch (error) {
      setMessage("Operational commentary unavailable.");
      setTimestamp(new Date().toISOString());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommentary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, role]);

  if (!open) {
    return (
      <Button
        className="fixed bottom-6 right-6 z-50 gap-2 shadow-lg"
        onClick={() => setOpen(true)}
        data-testid="commentator-open"
      >
        <span className="relative inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/20 text-[10px] font-semibold text-blue-300">
          M
          <Bot className="absolute -bottom-1 -right-1 h-3 w-3 text-blue-400" />
        </span>
        MIRA
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 z-50 w-80 border-border bg-black/70 backdrop-blur-md">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <div className="relative h-7 w-7 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center text-[11px] font-semibold">
            M
            <Bot className="absolute -bottom-1 -right-1 h-4 w-4 text-blue-400" />
          </div>
          MIRA
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-border text-xs">
            {role || "analyst"}
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setOpen(false)}
            data-testid="commentator-close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-xs text-muted-foreground">{screen}</div>
        <div className="text-sm text-white">
          {loading ? "Generating commentary..." : message}
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{timestamp ? new Date(timestamp).toLocaleTimeString() : ""}</span>
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={fetchCommentary}
            disabled={loading}
            data-testid="commentator-refresh"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default XAICommentator;
