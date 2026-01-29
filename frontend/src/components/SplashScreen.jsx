import React from "react";
import { Activity, Shield, Swords, Brain, Sparkles, Crown } from "lucide-react";

const teamIcons = [
  { icon: Swords, color: "text-red-400" },
  { icon: Shield, color: "text-blue-400" },
  { icon: Brain, color: "text-purple-400" },
  { icon: Sparkles, color: "text-yellow-400" },
  { icon: Crown, color: "text-amber-400" },
];

const SplashScreen = () => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur" data-testid="splash-screen">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/20 splash-glow">
          <Activity className="h-8 w-8 text-blue-400" />
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight">Fraud Forge</h1>
        <p className="mt-1 text-sm text-muted-foreground">War Room initializing...</p>
        <div className="mt-6 flex items-center justify-center gap-3">
          {teamIcons.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={index}
                className={`h-10 w-10 rounded-full border border-border/80 bg-card flex items-center justify-center ${item.color} animate-pulse`}
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <Icon className="h-5 w-5" />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
