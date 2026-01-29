import React, { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Badge } from "./ui/badge";

const steps = [
  {
    title: "Welcome to Fraud Forge",
    description: "You’re entering a live war room where AI teams defend banks in real time.",
  },
  {
    title: "War Room",
    description: "Watch Red vs Blue thinking streams, control turns, and track Time-to-Immunity.",
  },
  {
    title: "Brain Surgery",
    description: "Drag patches onto the knowledge graph and validate safety before deployment.",
  },
  {
    title: "Metrics & Governance",
    description: "Use Judge Mode for simplified KPIs and verify approvals with full audit trails.",
  },
];

const OnboardingWizard = () => {
  const [open, setOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const hasSeen = window.localStorage.getItem("ff_onboarded");
    if (!hasSeen) setOpen(true);
  }, []);

  const progress = useMemo(() => ((stepIndex + 1) / steps.length) * 100, [stepIndex]);
  const isLast = stepIndex === steps.length - 1;

  const handleClose = () => {
    window.localStorage.setItem("ff_onboarded", "true");
    setOpen(false);
  };

  const handleNext = () => {
    if (isLast) {
      handleClose();
    } else {
      setStepIndex((prev) => prev + 1);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(value) => { if (!value) handleClose(); }}>
      <DialogContent className="bg-card border-border" data-testid="onboarding-dialog">
        <DialogHeader>
          <DialogTitle>{steps[stepIndex].title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-muted-foreground">{steps[stepIndex].description}</p>
          <div className="flex items-center justify-between">
            <Badge variant="outline" className="text-xs">Step {stepIndex + 1} of {steps.length}</Badge>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={handleClose} data-testid="onboarding-skip">Skip</Button>
              <Button onClick={handleNext} data-testid="onboarding-next">
                {isLast ? "Finish" : "Next"}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingWizard;
