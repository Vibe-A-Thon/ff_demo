import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Badge } from "./ui/badge";

const shortcuts = [
  { key: "Space", action: "Play / Pause Auto" },
  { key: "→", action: "Next turn" },
  { key: "←", action: "Previous turn" },
  { key: "D", action: "Toggle demo mode" },
  { key: "?", action: "Open shortcuts" },
  { key: "H", action: "Open help center" },
];

const KeyboardShortcutsOverlay = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-card border-border" data-testid="shortcuts-dialog">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          {shortcuts.map((item) => (
            <div key={item.key} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
              <span className="text-sm text-muted-foreground">{item.action}</span>
              <Badge variant="outline" className="font-mono">{item.key}</Badge>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default KeyboardShortcutsOverlay;
