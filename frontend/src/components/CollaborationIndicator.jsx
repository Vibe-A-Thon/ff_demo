import React from "react";
import { Badge } from "./ui/badge";

const collaborators = [
  { name: "Red Ops", color: "bg-red-500/20 text-red-400" },
  { name: "Blue Ops", color: "bg-blue-500/20 text-blue-400" },
  { name: "Gold QA", color: "bg-yellow-500/20 text-yellow-400" },
];

const CollaborationIndicator = () => {
  return (
    <div className="flex items-center gap-2" data-testid="collab-indicator">
      <span className="text-xs text-muted-foreground">Collaborating:</span>
      {collaborators.map((c) => (
        <Badge key={c.name} className={`border border-border ${c.color}`}>
          <span className="mr-2 inline-block h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          {c.name}
        </Badge>
      ))}
    </div>
  );
};

export default CollaborationIndicator;
