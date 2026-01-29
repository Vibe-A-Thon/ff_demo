import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ExternalLink, Info, PlayCircle } from "lucide-react";

const HelpCenter = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-card border-border" data-testid="help-dialog">
        <DialogHeader>
          <DialogTitle>Help Center</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm text-muted-foreground">
          <div className="rounded-md border border-border p-3">
            <div className="flex items-center gap-2 text-foreground">
              <Info className="h-4 w-4 text-blue-400" />
              <span className="font-semibold">Quick Start</span>
            </div>
            <ul className="mt-2 space-y-1">
              <li>Start a battle in War Room to see live thinking streams.</li>
              <li>Use Brain Surgery to merge knowledge patches safely.</li>
              <li>Check Metrics for Time-to-Immunity trends.</li>
            </ul>
          </div>
          <div className="rounded-md border border-border p-3">
            <div className="flex items-center gap-2 text-foreground">
              <PlayCircle className="h-4 w-4 text-purple-400" />
              <span className="font-semibold">Demo Tips</span>
            </div>
            <p className="mt-2">Use Demo Mode and highlight “Money Saved” for judges.</p>
            <Badge className="mt-2 bg-purple-500/15 text-purple-400 border border-purple-500/20">Judge Mode Ready</Badge>
          </div>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => window.open("https://docs.fraudforge.local", "_blank")}
            data-testid="help-docs-btn"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open Playbook
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default HelpCenter;
