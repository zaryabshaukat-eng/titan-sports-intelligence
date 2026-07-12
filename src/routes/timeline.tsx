import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard } from "../components/titan/primitives";
import { Timeline, SAMPLE_TIMELINE } from "../components/titan/Timeline";
import { Activity, TrendingUp, Brain, Bell, RefreshCw } from "lucide-react";

export const Route = createFileRoute("/timeline")({ component: TimelinePage });

function TimelinePage() {
  const total        = SAMPLE_TIMELINE.length;
  const todayEvents  = SAMPLE_TIMELINE.filter((e) =>
    e.timestamp.includes("min") || e.timestamp.includes("h ago") || e.timestamp.includes("hr")
  ).length;
  const alerts = SAMPLE_TIMELINE.filter((e) => e.type === "alert").length;
  const modelEvents = SAMPLE_TIMELINE.filter((e) => e.type === "model" || e.type === "learning").length;

  return (
    <>
      <PageHeader
        eyebrow="History"
        title="Historical Timeline"
        description="Unified event stream — odds movements, predictions, model updates, research, and results."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        }
      />

      {/* KPIs */}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Events"      value={String(total)}       sub="last 3 days"    icon={Activity}   accent="primary" />
        <StatCard label="Today's Events"    value={String(todayEvents)} sub="streaming live"  icon={TrendingUp}  accent="emerald" />
        <StatCard label="Alerts Triggered"  value={String(alerts)}      sub="high priority"   icon={Bell}       accent="warning" />
        <StatCard label="Model / Learning"  value={String(modelEvents)} sub="engine activity" icon={Brain} />
      </div>

      {/* Timeline */}
      <GlassCard className="p-5">
        <Timeline events={SAMPLE_TIMELINE} showFilters showGrouping />
      </GlassCard>
    </>
  );
}
