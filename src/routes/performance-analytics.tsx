import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard, StatCard } from "../components/titan/primitives";
import { Target, TrendingUp, Activity, Percent } from "lucide-react";

export const Route = createFileRoute("/performance-analytics")({ component: PA });

function PA() {
  return (
    <PlaceholderPage eyebrow="Attribution" title="Performance Analytics" description="Rolling accuracy, ROI, and calibration across markets and models.">
      <div className="grid gap-3 md:grid-cols-4">
        <StatCard label="Rolling ROI" value="+11.4%" delta={{ value: "+1.8%", positive: true }} icon={TrendingUp} accent="emerald" />
        <StatCard label="Model Accuracy" value="72.1%" sub="calibrated" icon={Target} />
        <StatCard label="CLV" value="+2.7%" icon={Activity} accent="emerald" />
        <StatCard label="Yield" value="+3.9%" icon={Percent} accent="primary" />
      </div>
      <GlassCard className="mt-4 flex flex-col items-center justify-center gap-4 py-16 text-center">
        <div className="relative">
          <div className="grid h-14 w-14 place-items-center rounded-xl bg-gradient-to-br from-primary/20 to-emerald/10 ring-1 ring-white/10">
            <Activity className="h-6 w-6 text-primary" />
          </div>
          <div className="absolute inset-0 rounded-xl bg-primary/10 blur-xl" />
        </div>
        <div className="max-w-xs space-y-1.5">
          <p className="font-display text-sm font-semibold">Calibration curves pending</p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Detailed attribution, Brier scores, and ROI breakdown will appear here once the Prediction Engine completes its first full cycle.
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
          <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
          Engine Warming
        </div>
      </GlassCard>
    </PlaceholderPage>
  );
}
