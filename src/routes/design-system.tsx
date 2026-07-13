import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import {
  Badge, StatusChip, ProgressBar, MiniProgress,
  Skeleton, SkeletonCard, SkeletonTable, SkeletonText,
  EmptyState, Dialog, Drawer, MetricCard, MetricGrid, Panel, PanelHeader,
} from "../components/titan/ds";
import { ConfidenceGauge, ProbabilityRing, RiskMeter, SignalStrength, MarketStrength, HealthIndicator, AccuracyWidget, TrendIndicator } from "../components/titan/ConfidenceWidgets";
import { Timeline } from "../components/titan/Timeline";
import {
  Activity, Brain, Target, Palette, Layers, BarChart3,
  AlertTriangle, Database, FileText, Zap,
} from "lucide-react";

export const Route = createFileRoute("/design-system")({ component: DesignSystemPage });

const NAV_SECTIONS = [
  "Badges & Chips", "Progress & Metrics", "Skeletons", "Empty States",
  "Dialogs & Drawers", "Cards & Panels", "Confidence Widgets", "Timeline", "Primitives",
];

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-6">
      <div className="mb-4 flex items-center gap-3">
        <h2 className="font-display text-lg font-bold">{title}</h2>
        <div className="flex-1 h-px bg-white/[0.06]" />
      </div>
      {children}
    </section>
  );
}

function ShowCase({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`glass rounded-xl p-5 ${className}`}>
      <div className="mb-4 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">{label}</div>
      {children}
    </div>
  );
}

function DesignSystemPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("Badges & Chips");

  const scrollTo = (label: string) => {
    const id = label.toLowerCase().replace(/[^a-z]+/g, "-");
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveSection(label);
  };

  return (
    <div className="flex gap-6">
      {/* Sticky left nav */}
      <aside className="sticky top-20 hidden h-fit w-44 shrink-0 xl:block">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-3">Components</div>
        <nav className="space-y-0.5">
          {NAV_SECTIONS.map((s) => (
            <button
              key={s}
              onClick={() => scrollTo(s)}
              className={`w-full text-left rounded-md px-2.5 py-1.5 text-xs transition-colors ${
                activeSection === s ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              {s}
            </button>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0 space-y-10">
        <PageHeader
          eyebrow="Design System"
          title="Component Library"
          description="Enterprise-grade reusable components — the complete TITAN design language."
        />

        {/* ── Badges & Chips ── */}
        <Section id="badges-chips" title="Badges & Chips">
          <div className="grid gap-4 sm:grid-cols-2">
            <ShowCase label="Badge variants">
              <div className="flex flex-wrap gap-2">
                {(["default","primary","emerald","warning","destructive","outline","muted"] as const).map((v) => (
                  <Badge key={v} variant={v}>{v}</Badge>
                ))}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(["primary","emerald","warning","destructive"] as const).map((v) => (
                  <Badge key={v} variant={v} dot>{v} with dot</Badge>
                ))}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge variant="primary" size="sm">Small</Badge>
                <Badge variant="primary" size="md">Medium</Badge>
                <Badge variant="primary" size="lg">Large</Badge>
              </div>
            </ShowCase>
            <ShowCase label="Status chips">
              <div className="flex flex-wrap gap-2">
                {(["online","offline","degraded","training","beta","pending","error"] as const).map((s) => (
                  <StatusChip key={s} status={s} />
                ))}
              </div>
              <div className="mt-4 space-y-2">
                {(["online","idle","training","beta"] as const).map((s) => (
                  <StatusPill key={s} status={s} />
                ))}
              </div>
            </ShowCase>
          </div>
        </Section>

        {/* ── Progress & Metrics ── */}
        <Section id="progress-metrics" title="Progress & Metrics">
          <div className="grid gap-4 sm:grid-cols-2">
            <ShowCase label="Progress bars">
              <div className="space-y-4">
                <ProgressBar value={87} label="Ensemble Health" variant="gradient" size="lg" />
                <ProgressBar value={72} label="Win Rate"        variant="emerald" />
                <ProgressBar value={54} label="CPU Usage"       variant="warning"  size="sm" />
                <ProgressBar value={34} label="Error Rate"      variant="destructive" size="sm" />
              </div>
            </ShowCase>
            <ShowCase label="Metric cards">
              <MetricGrid cols={2}>
                <MetricCard label="EV Score"   value="+8.4%" trend="up"   trendValue="+1.2%" variant="emerald" icon={Target} />
                <MetricCard label="Confidence" value="87.4%"  trend="up"   trendValue="+1.6%" variant="primary" icon={Brain} />
                <MetricCard label="Latency"    value="42ms"   trend="flat" trendValue="stable"                  icon={Zap} />
                <MetricCard label="Errors"     value="0.02%"  trend="down" trendValue="-0.01%" variant="warning" icon={AlertTriangle} />
              </MetricGrid>
            </ShowCase>
          </div>
        </Section>

        {/* ── Skeletons ── */}
        <Section id="skeletons" title="Skeletons">
          <div className="grid gap-4 sm:grid-cols-3">
            <ShowCase label="Skeleton card">
              <SkeletonCard />
            </ShowCase>
            <ShowCase label="Skeleton text">
              <SkeletonText lines={4} />
            </ShowCase>
            <ShowCase label="Custom skeletons">
              <div className="space-y-3">
                <Skeleton className="h-8 w-full rounded-lg" />
                <div className="flex gap-2">
                  <Skeleton className="h-8 w-8 rounded-full" />
                  <Skeleton className="h-8 flex-1 rounded-lg" />
                </div>
                <Skeleton className="h-24 w-full rounded-xl" />
              </div>
            </ShowCase>
          </div>
          <div className="mt-4">
            <ShowCase label="Skeleton table">
              <SkeletonTable rows={4} cols={5} />
            </ShowCase>
          </div>
        </Section>

        {/* ── Empty States ── */}
        <Section id="empty-states" title="Empty States">
          <div className="grid gap-4 sm:grid-cols-3">
            <ShowCase label="No data">
              <EmptyState
                icon={Database}
                title="No data available"
                description="Connect a data source to start seeing intelligence signals here."
                action={<button className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">Connect source</button>}
              />
            </ShowCase>
            <ShowCase label="No results">
              <EmptyState
                icon={Target}
                title="No matches found"
                description="Try adjusting your filters or search query."
              />
            </ShowCase>
            <ShowCase label="Offline">
              <EmptyState
                icon={Activity}
                title="Engine offline"
                description="The Tactical Engine is currently in training mode. Signals will resume at full capacity shortly."
              />
            </ShowCase>
          </div>
        </Section>

        {/* ── Dialogs & Drawers ── */}
        <Section id="dialogs-drawers" title="Dialogs & Drawers">
          <div className="grid gap-4 sm:grid-cols-2">
            <ShowCase label="Dialog">
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setDialogOpen(true)} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">
                  Open Dialog
                </button>
              </div>
              <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
                title="Confirm Model Deployment"
                description="You are about to deploy Tactical Engine v2.1.0 into production. This will affect all live predictions."
                variant="warning"
                footer={
                  <>
                    <button onClick={() => setDialogOpen(false)} className="rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">Cancel</button>
                    <button onClick={() => setDialogOpen(false)} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">Deploy</button>
                  </>
                }
              >
                <div className="text-sm text-muted-foreground">
                  <ul className="space-y-1 list-disc list-inside">
                    <li>Training accuracy: 78.4%</li>
                    <li>Formation dataset: 2024-25 season</li>
                    <li>Rollout: gradual (10% → 50% → 100%)</li>
                  </ul>
                </div>
              </Dialog>
            </ShowCase>
            <ShowCase label="Drawer">
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setDrawerOpen(true)} className="rounded-md bg-primary/10 border border-primary/20 px-3 py-1.5 text-xs font-medium text-primary">
                  Open Drawer
                </button>
              </div>
              <Drawer
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                title="Engine Configuration"
                description="Statistical Engine v4.1.0"
                width="md"
                footer={
                  <>
                    <button onClick={() => setDrawerOpen(false)} className="rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">Cancel</button>
                    <button onClick={() => setDrawerOpen(false)} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">Save</button>
                  </>
                }
              >
                <div className="space-y-4">
                  {[["Decay parameter", "0.0065"], ["Min fixtures", "5"], ["Home advantage", "1.18"], ["Weight cap", "0.40"]].map(([l, v]) => (
                    <div key={l}>
                      <label className="text-xs text-muted-foreground">{l}</label>
                      <input defaultValue={v} className="mt-1 h-9 w-full rounded-md border border-white/5 bg-white/5 px-3 text-sm focus:border-primary/30 focus:outline-none focus:ring-1 focus:ring-primary/20" />
                    </div>
                  ))}
                </div>
              </Drawer>
            </ShowCase>
          </div>
        </Section>

        {/* ── Cards & Panels ── */}
        <Section id="cards-panels" title="Cards & Panels">
          <div className="grid gap-4 sm:grid-cols-2">
            <ShowCase label="Stat cards">
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Markets"   value="18.4K" delta={{ value: "+3.2%", positive: true }} icon={BarChart3} accent="primary" />
                <StatCard label="Accuracy"  value="72.1%"                                            icon={Target}   accent="emerald" />
              </div>
            </ShowCase>
            <ShowCase label="Panel + header">
              <Panel>
                <PanelHeader
                  eyebrow="Intelligence"
                  title="Engine Status"
                  description="Real-time health across neural fabric"
                  action={<StatusPill status="online" label="Live" />}
                />
                <div className="space-y-2">
                  <HealthIndicator status="healthy"  label="Statistical Engine"  detail="96% health · 312ms" />
                  <HealthIndicator status="degraded" label="Tactical Engine"     detail="71% health · training" />
                  <HealthIndicator status="healthy"  label="Consensus Engine"    detail="89% health · 428ms" />
                </div>
              </Panel>
            </ShowCase>
          </div>
        </Section>

        {/* ── Confidence Widgets ── */}
        <Section id="confidence-widgets" title="Confidence Widgets">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <ShowCase label="Confidence gauge">
              <div className="flex justify-center"><ConfidenceGauge value={87} size={130} /></div>
            </ShowCase>
            <ShowCase label="Probability ring">
              <div className="flex justify-center gap-4">
                <ProbabilityRing value={82} label="Over 2.5" sublabel="Win" size={80} />
                <ProbabilityRing value={64} label="BTTS Yes" sublabel="Moderate" size={80} />
              </div>
            </ShowCase>
            <ShowCase label="Risk meter">
              <RiskMeter value={28} label="Market Risk" />
              <div className="mt-3"><RiskMeter value={71} label="Correlation Risk" /></div>
            </ShowCase>
            <ShowCase label="Signal strength">
              <div className="flex justify-around">
                <SignalStrength value={5} label="Strong" />
                <SignalStrength value={3} label="Moderate" />
                <SignalStrength value={1} label="Weak" />
              </div>
            </ShowCase>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <ShowCase label="Market strength">
              <MarketStrength value={8} label="Liquidity" />
              <div className="mt-3"><MarketStrength value={4} label="Edge" /></div>
            </ShowCase>
            <ShowCase label="Accuracy widget">
              <AccuracyWidget value={72.1} delta={0.4} label="Model Accuracy" period="Rolling 90d" />
            </ShowCase>
            <ShowCase label="Trend indicators">
              <div className="space-y-2">
                <TrendIndicator direction="up"   value="+6.8% EV"  label="Expected value edge" magnitude="strong" />
                <TrendIndicator direction="down" value="-0.08 line" label="Line movement"       magnitude="moderate" />
                <TrendIndicator direction="flat" value="82%"        label="Confidence stable"   magnitude="weak" />
              </div>
            </ShowCase>
          </div>
        </Section>

        {/* ── Timeline ── */}
        <Section id="timeline" title="Timeline">
          <GlassCard className="p-5">
            <SectionTitle title="Event timeline (compact)" description="Live event stream sample" />
            <Timeline
              showFilters={true}
              showGrouping={false}
              maxHeight="440px"
            />
          </GlassCard>
        </Section>

        {/* ── Primitives ── */}
        <Section id="primitives" title="Primitives">
          <div className="grid gap-4 sm:grid-cols-2">
            <ShowCase label="Glass cards">
              <div className="space-y-2">
                <GlassCard className="p-3 text-xs text-muted-foreground">Base glass card</GlassCard>
                <div className="glass-strong rounded-xl p-3 text-xs text-muted-foreground">Glass strong variant</div>
              </div>
            </ShowCase>
            <ShowCase label="Status pills">
              <div className="flex flex-wrap gap-2">
                {(["online","training","idle","offline","beta"] as const).map((s) => (
                  <StatusPill key={s} status={s} />
                ))}
              </div>
            </ShowCase>
          </div>
        </Section>
      </div>
    </div>
  );
}
