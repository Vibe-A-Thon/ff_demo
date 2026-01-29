import React from "react";
import { Badge } from "./ui/badge";
import { Scale } from "lucide-react";

const JudgeModeBanner = ({ active }) => {
  if (!active) return null;
  return (
    <div className="mb-4 rounded-md border border-purple-500/30 bg-purple-500/10 px-4 py-2" data-testid="judge-mode-banner">
      <div className="flex items-center gap-2 text-purple-400 text-sm">
        <Scale className="h-4 w-4" />
        Judge Mode enabled: simplified KPIs and curated visuals for demo.
        <Badge className="ml-auto bg-purple-500/20 text-purple-300">LIVE</Badge>
      </div>
    </div>
  );
};

export default JudgeModeBanner;
