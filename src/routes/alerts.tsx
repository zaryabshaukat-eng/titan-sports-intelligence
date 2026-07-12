import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatusPill } from "../components/titan/primitives";
import { Bell, CheckCircle2, AlertTriangle, TrendingUp, Radio } from "lucide-react";

export const Route = createFileRoute("/alerts")({ component: AlertsPage });

const alerts = [
  { t: "just now", type: "Value", msg: "EV +6.8% detected on Man City vs Arsenal — Over 2.5", level: "primary", icon: TrendingUp },
  { t: "3 min ago", type: "Arbitrage", msg: "3-way arb across Pinnacle / Bet365 / Betfair (ROI 2.4%)", level: "emerald", icon: CheckCircle2 },
  { t: "9 min ago", type: "Market", msg: "Sharp movement on Bayern -0.5 (-0.08 line over 6m)", level: "warning", icon: AlertTriangle },
  { t: "17 min ago", type: "Model", msg: "Consensus confidence rebalanced — Serie A slate", level: "primary", icon: Radio },
  { t: "34 min ago", type: "System", msg: "Historical engine finished nightly recomputation", level: "emerald", icon: CheckCircle2 },
  { t: "1 hr ago", type: "Risk", msg: "Correlation warning — 3 open positions on same slate", level: "warning", icon: AlertTriangle },
];

function AlertsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Signals"
        title="Alerts Center"
        description="Unified stream of intelligence events from every Titan engine."
        actions={<StatusPill status="online" label="Streaming" />}
      />

      <div className="grid gap-3 md:grid-cols-4">
        {[
          { l: "Total Today", v: "128" },
          { l: "High Priority", v: "12" },
          { l: "Value Signals", v: "63" },
          { l: "Arbitrage", v: "9" },
        ].map((s) => (
          <GlassCard key={s.l} className="p-4">
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{s.l}</div>
            <div className="mt-1 font-display text-2xl font-bold">{s.v}</div>
          </GlassCard>
        ))}
      </div>

      <GlassCard className="mt-4 p-2">
        <div className="divide-y divide-white/5">
          {alerts.map((a, i) => {
            const styles = { primary: "text-primary bg-primary/10", emerald: "text-emerald bg-emerald/10", warning: "text-warning bg-warning/10" }[a.level as "primary"|"emerald"|"warning"];
            const Icon = a.icon;
            return (
              <div key={i} className="flex items-center gap-3 px-3 py-3 hover:bg-white/[0.02]">
                <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-md ${styles}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
                    <span className="font-semibold text-foreground">{a.type}</span>
                    <span>·</span>
                    <span>{a.t}</span>
                  </div>
                  <div className="text-sm">{a.msg}</div>
                </div>
                <button className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-muted-foreground hover:text-foreground">
                  <Bell className="h-3.5 w-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      </GlassCard>
    </>
  );
}
