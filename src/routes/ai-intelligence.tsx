import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import { HealthIndicator, ConfidenceGauge, RiskMeter } from "../components/titan/ConfidenceWidgets";
import {
  LineChart as LineIcon, Database, History, Swords, ShieldAlert, Layers,
  MessageSquareCode, Sparkles, Rewind, ArrowRight, Cpu, MemoryStick,
  Clock, Zap, Activity, RefreshCw, BarChart3, TrendingUp,
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";

export const Route = createFileRoute("/ai-intelligence")({ component: AIPage });

interface Engine {
  name: string;
  desc: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "online" | "training" | "idle" | "offline" | "beta";
  health: number;
  latency: number;  // ms
  version: string;
  memory: number;   // GB used
  memoryMax: number;
  cpu: number;      // %
  uptime: string;
  updated: string;
  requests24h: number;
}

const engines: Engine[] = [
  { name: "Market Intelligence Engine", desc: "Cross-book line movement, sharp flow detection, and consensus modelling.", icon: LineIcon,          status: "online",   health: 98, latency: 241,  version: "v3.2.1", memory: 4.2,  memoryMax: 8,  cpu: 34, uptime: "47d 12h",  updated: "2s ago",  requests24h: 48_200 },
  { name: "Statistical Engine",         desc: "Poisson, Dixon-Coles, xG/xGA regression and generalised team strength models.", icon: Database,        status: "online",   health: 96, latency: 312,  version: "v4.1.0", memory: 6.8,  memoryMax: 12, cpu: 52, uptime: "47d 12h",  updated: "8s ago",  requests24h: 61_440 },
  { name: "Historical Engine",          desc: "Deep-history pattern matching across 30+ seasons and 200K+ fixtures.", icon: History,              status: "online",   health: 94, latency: 198,  version: "v2.8.3", memory: 18.2, memoryMax: 32, cpu: 28, uptime: "22d 6h",   updated: "1m ago",  requests24h: 29_100 },
  { name: "Tactical Engine",            desc: "Formation, pressing intensity, and matchup mismatch analysis.", icon: Swords,                     status: "training", health: 71, latency: 890,  version: "v2.1.0", memory: 11.4, memoryMax: 16, cpu: 89, uptime: "2d 3h",    updated: "12s ago", requests24h: 8_400  },
  { name: "Risk Engine",                desc: "Bankroll modelling, Kelly sizing, drawdown & correlation risk.", icon: ShieldAlert,                status: "online",   health: 92, latency: 189,  version: "v3.0.2", memory: 2.1,  memoryMax: 4,  cpu: 21, uptime: "47d 12h",  updated: "4s ago",  requests24h: 35_800 },
  { name: "Consensus Engine",           desc: "Ensembles across all engines with dynamic weighting.", icon: Layers,                              status: "online",   health: 89, latency: 428,  version: "v5.0.1", memory: 3.4,  memoryMax: 8,  cpu: 44, uptime: "47d 12h",  updated: "1s ago",  requests24h: 52_100 },
  { name: "Explainability Engine",      desc: "SHAP-style attribution and natural-language rationale for every signal.", icon: MessageSquareCode, status: "beta",     health: 68, latency: 1240, version: "v0.9.4", memory: 5.6,  memoryMax: 8,  cpu: 61, uptime: "8d 4h",    updated: "22s ago", requests24h: 4_200  },
  { name: "Prediction Engine",          desc: "Calibrated probability outputs across all supported markets.", icon: Sparkles,                    status: "training", health: 74, latency: 621,  version: "v1.3.0", memory: 9.1,  memoryMax: 12, cpu: 78, uptime: "1d 18h",   updated: "6s ago",  requests24h: 18_900 },
  { name: "Backtesting Engine",         desc: "Reproducible historical simulations with slippage and closing-line value.", icon: Rewind,          status: "online",   health: 90, latency: 3400, version: "v2.4.1", memory: 12.8, memoryMax: 16, cpu: 18, uptime: "47d 12h",  updated: "5m ago",  requests24h: 1_240  },
];

const performanceSeries = [
  { t: "00:00", stat: 94, market: 91, hist: 88 },
  { t: "04:00", t2: "04:00", stat: 95, market: 89, hist: 90 },
  { t: "08:00", stat: 96, market: 92, hist: 89 },
  { t: "12:00", stat: 97, market: 94, hist: 91 },
  { t: "16:00", stat: 95, market: 96, hist: 90 },
  { t: "20:00", stat: 98, market: 95, hist: 92 },
  { t: "Now",   stat: 96, market: 93, hist: 94 },
];

function MiniBar({ value, max, color = "bg-primary" }: { value: number; max: number; color?: string }) {
  return (
    <div className="h-1 overflow-hidden rounded-full bg-white/5">
      <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${(value / max) * 100}%` }} />
    </div>
  );
}

function AIPage() {
  const totalOnline   = engines.filter((e) => e.status === "online").length;
  const totalTraining = engines.filter((e) => e.status === "training").length;
  const avgHealth     = Math.round(engines.reduce((s, e) => s + e.health, 0) / engines.length);
  const totalReqs     = engines.reduce((s, e) => s + e.requests24h, 0);

  return (
    <>
      <PageHeader
        eyebrow="Neural Fabric"
        title="AI Intelligence"
        description="The Titan intelligence stack — nine engines converging into a single decision surface."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        }
      />

      {/* KPI row */}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Engines Online"     value={`${totalOnline} / ${engines.length}`} sub={`${totalTraining} training`}                         icon={Activity}  accent="emerald" />
        <StatCard label="Ensemble Health"    value={`${avgHealth}%`}        delta={{ value: "+1.6%", positive: true }}                               icon={BarChart3} accent="primary" />
        <StatCard label="Requests / 24h"     value={`${(totalReqs / 1000).toFixed(0)}K`}  sub="across all engines"                                  icon={Zap}       accent="emerald" />
        <StatCard label="Avg Inference Lag"  value="428ms"                  sub="p95: 1.2s"                                                          icon={Clock} />
      </div>

      {/* Performance chart */}
      <GlassCard className="mb-6 p-5">
        <SectionTitle
          title="Engine performance — 24h"
          description="Health scores across top-3 engines"
          action={<StatusPill status="online" label="Live" />}
        />
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={performanceSeries} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gStat"   x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gMarket" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gHist"   x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.78 0.16 75)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="oklch(0.78 0.16 75)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
              <XAxis dataKey="t" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis domain={[60, 100]} stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }}
                formatter={(v: number, name: string) => [`${v}%`, { stat: "Statistical", market: "Market", hist: "Historical" }[name] ?? name]}
              />
              <Area type="monotone" dataKey="stat"   stroke="oklch(0.72 0.19 245)" strokeWidth={2} fill="url(#gStat)" />
              <Area type="monotone" dataKey="market" stroke="oklch(0.75 0.18 155)" strokeWidth={2} fill="url(#gMarket)" />
              <Area type="monotone" dataKey="hist"   stroke="oklch(0.78 0.16 75)"  strokeWidth={2} fill="url(#gHist)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex items-center gap-6 text-[11px] text-muted-foreground">
          {[["oklch(0.72 0.19 245)", "Statistical"], ["oklch(0.75 0.18 155)", "Market"], ["oklch(0.78 0.16 75)", "Historical"]].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1.5">
              <div className="h-1.5 w-4 rounded-full" style={{ background: c }} />
              <span>{l}</span>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Engine cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {engines.map((e) => (
          <GlassCard key={e.name} className="group relative overflow-hidden p-5 transition-all hover:border-white/15">
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br from-primary/20 to-emerald/10 opacity-40 blur-2xl transition-opacity group-hover:opacity-70" />
            <div className="relative">
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 text-primary">
                  <e.icon className="h-5 w-5" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">{e.version}</span>
                  <StatusPill status={e.status} />
                </div>
              </div>

              <h3 className="mt-3 font-display text-sm font-semibold leading-tight">{e.name}</h3>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{e.desc}</p>

              {/* Health bar */}
              <div className="mt-4">
                <div className="mb-1 flex justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
                  <span>Engine Health</span>
                  <span className="font-mono text-foreground">{e.health}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-emerald transition-all duration-700"
                    style={{ width: `${e.health}%` }}
                  />
                </div>
              </div>

              {/* Metrics grid */}
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
                  <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
                    <Zap className="h-2.5 w-2.5" /> Latency
                  </div>
                  <div className="font-mono text-sm font-semibold">{e.latency >= 1000 ? `${(e.latency / 1000).toFixed(1)}s` : `${e.latency}ms`}</div>
                </div>
                <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
                  <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
                    <Clock className="h-2.5 w-2.5" /> Uptime
                  </div>
                  <div className="font-mono text-xs font-semibold">{e.uptime}</div>
                </div>
                <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
                  <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
                    <Cpu className="h-2.5 w-2.5" /> CPU
                  </div>
                  <div className="font-mono text-sm font-semibold">{e.cpu}%</div>
                  <MiniBar value={e.cpu} max={100} color={e.cpu > 80 ? "bg-warning" : e.cpu > 60 ? "bg-primary" : "bg-emerald"} />
                </div>
                <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
                  <div className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
                    <MemoryStick className="h-2.5 w-2.5" /> Memory
                  </div>
                  <div className="font-mono text-xs font-semibold">{e.memory}  / {e.memoryMax} GB</div>
                  <MiniBar value={e.memory} max={e.memoryMax} color={(e.memory / e.memoryMax) > 0.85 ? "bg-warning" : "bg-primary"} />
                </div>
              </div>

              {/* Footer */}
              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Reqs (24h): </span>
                  <span className="font-mono">{e.requests24h.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-muted-foreground">Updated {e.updated}</span>
                  <button className="inline-flex items-center gap-1 text-primary hover:underline">
                    Configure <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Health summary */}
      <GlassCard className="mt-6 p-5">
        <SectionTitle
          title="Ensemble health overview"
          description="Aggregate status across the neural fabric"
        />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {engines.map((e) => (
            <HealthIndicator
              key={e.name}
              status={e.status === "online" ? "healthy" : e.status === "training" ? "degraded" : e.status === "beta" ? "degraded" : "offline"}
              label={e.name}
              detail={`${e.health}% health · ${e.latency >= 1000 ? `${(e.latency / 1000).toFixed(1)}s` : `${e.latency}ms`} latency`}
            />
          ))}
        </div>
      </GlassCard>

      {/* API surface */}
      <GlassCard className="mt-6 p-5">
        <SectionTitle title="Extension surface" description="Every engine exposes a strict service contract, ready to bind to production intelligence." />
        <div className="grid gap-3 md:grid-cols-3">
          {["Signal ingest → /engines/*/ingest", "Inference → /engines/*/infer", "Explainability → /engines/*/explain"].map((t) => (
            <div key={t} className="rounded-lg border border-white/5 bg-white/[0.02] p-3 font-mono text-xs text-muted-foreground hover:border-white/10 hover:text-foreground transition-colors">
              {t}
            </div>
          ))}
        </div>
      </GlassCard>
    </>
  );
}
