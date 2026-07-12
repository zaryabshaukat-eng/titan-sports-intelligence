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
      <GlassCard className="mt-4 p-10 text-center text-sm text-muted-foreground">
        Detailed attribution & calibration curves connect once the Prediction Engine goes online.
      </GlassCard>
    </PlaceholderPage>
  );
}
