import React from "react";
import { Activity, Shield, Swords, Brain, Sparkles, Crown } from "lucide-react";

const teamIcons = [
  { icon: Swords, color: "text-red-400" },
  { icon: Shield, color: "text-blue-400" },
  { icon: Brain, color: "text-purple-400" },
  { icon: Sparkles, color: "text-yellow-400" },
  { icon: Crown, color: "text-amber-400" },
];

const teamAvatars = [
  { name: "Red", initials: "RD", color: "bg-red-500/20 text-red-300", ring: "border-red-400/40" },
  { name: "Blue", initials: "BL", color: "bg-blue-500/20 text-blue-300", ring: "border-blue-400/40" },
  { name: "Purple", initials: "PR", color: "bg-purple-500/20 text-purple-300", ring: "border-purple-400/40" },
  { name: "Green", initials: "GR", color: "bg-green-500/20 text-green-300", ring: "border-green-400/40" },
  { name: "Gold", initials: "GD", color: "bg-yellow-500/20 text-yellow-300", ring: "border-yellow-400/40" },
];

const SplashScreen = () => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur" data-testid="splash-screen">
      <div className="text-center glass-panel px-10 py-8 rounded-3xl border border-blue-500/20">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/20 splash-glow">
          <Activity className="h-8 w-8 text-blue-400" />
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight">Fraud Forge</h1>
        <p className="mt-1 text-sm text-muted-foreground">War Room initializing...</p>
        <div className="mt-6 avatar-orbit">
          {teamAvatars.map((avatar, index) => (
            <div
              key={avatar.name}
              className="avatar-orbit-item"
              style={{ animationDelay: `${index * 0.4}s` }}
            >
              <div className={`h-10 w-10 rounded-full border ${avatar.ring} ${avatar.color} flex items-center justify-center avatar-ring text-xs font-semibold`}>
                {avatar.initials}
              </div>
            </div>
          ))}
        </div>
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
