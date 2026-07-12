import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatusPill } from "../components/titan/primitives";

export const Route = createFileRoute("/account")({ component: Account });

function Account() {
  return (
    <>
      <PageHeader eyebrow="Identity" title="Account" description="Your Titan seat and organization access." />
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="p-6 lg:col-span-1">
          <div className="grid h-20 w-20 place-items-center rounded-2xl bg-gradient-to-br from-primary to-emerald text-2xl font-bold text-[oklch(0.14_0.02_260)]">TN</div>
          <h2 className="mt-4 font-display text-lg font-semibold">Titan Analyst</h2>
          <p className="text-sm text-muted-foreground">analyst@titan.ops</p>
          <div className="mt-3"><StatusPill status="online" label="Active" /></div>
        </GlassCard>
        <GlassCard className="p-6 lg:col-span-2">
          <h3 className="font-display font-semibold">Plan</h3>
          <p className="mt-1 text-sm text-muted-foreground">Enterprise · Unlimited seats · SLA 99.99%</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {[
              { l: "Seats used", v: "24 / ∞" },
              { l: "API calls (30d)", v: "8.4M" },
              { l: "Renewal", v: "Jan 12, 2027" },
            ].map((s) => (
              <div key={s.l} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{s.l}</div>
                <div className="mt-1 font-mono">{s.v}</div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </>
  );
}
