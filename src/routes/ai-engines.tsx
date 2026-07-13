import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Brain, Activity, CheckCircle2, AlertCircle, Clock, Zap, RefreshCw,
  ChevronDown, ChevronRight, Database, TrendingUp, BarChart2, Shield,
  Microscope, BookOpen, Cpu, Eye, MessageSquare, Layers, Server,
} from "lucide-react";
import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts";
import { PageHeader } from "../components/titan/AppShell";

export const Route = createFileRoute("/ai-engines")({ component: AIEnginesPage });

/* ─── Types ─── */
type EngineStatus = "healthy" | "running" | "idle" | "training" | "beta" | "planned" | "degraded";

interface Engine {
  id: string;
  name: string;
  shortName: string;
  version: string;
  status: EngineStatus;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  accuracy: number;
  latency: number;       // ms
  throughput: number;    // req/min
  uptime: number;        // %
  lastHeartbeat: string;
  sparkline: { v: number }[];
  tags: string[];
  dependencies?: string[];
}

/* ─── Engine data ─── */
const ENGINES: Engine[] = [
  {
    id: "market-intel",
    name: "Market Intelligence Engine",
    shortName: "Market Intel",
    version: "v3.2.1",
    status: "healthy",
    description: "Monitors 42 bookmakers in real time; detects sharp money, line movement, and arbitrage windows.",
    icon: TrendingUp,
    accuracy: 94.2,
    latency: 28,
    throughput: 1840,
    uptime: 99.97,
    lastHeartbeat: "2s ago",
    sparkline: [{ v: 88 }, { v: 91 }, { v: 89 }, { v: 93 }, { v: 94 }, { v: 92 }, { v: 95 }, { v: 94 }],
    tags: ["Core", "Live"],
    dependencies: ["Statistical Engine", "Consensus Engine"],
  },
  {
    id: "statistical",
    name: "Statistical Engine",
    shortName: "Statistical",
    version: "v4.1.0",
    status: "running",
    description: "Dixon-Coles Poisson model with dynamic time-decay. Computes xG, xGA, and fair-line probabilities.",
    icon: BarChart2,
    accuracy: 91.6,
    latency: 42,
    throughput: 960,
    uptime: 99.94,
    lastHeartbeat: "4s ago",
    sparkline: [{ v: 85 }, { v: 88 }, { v: 90 }, { v: 88 }, { v: 91 }, { v: 90 }, { v: 92 }, { v: 91 }],
    tags: ["Core", "Modelling"],
  },
  {
    id: "simulation",
    name: "Simulation Engine",
    shortName: "Simulation",
    version: "v2.0.4",
    status: "idle",
    description: "Monte Carlo match simulation — 100k iterations per fixture. Activated on demand for high-value events.",
    icon: Cpu,
    accuracy: 89.3,
    latency: 340,
    throughput: 18,
    uptime: 99.80,
    lastHeartbeat: "1m ago",
    sparkline: [{ v: 70 }, { v: 68 }, { v: 71 }, { v: 69 }, { v: 72 }, { v: 70 }, { v: 69 }, { v: 70 }],
    tags: ["Compute-Heavy"],
    dependencies: ["Statistical Engine"],
  },
  {
    id: "risk",
    name: "Risk Engine",
    shortName: "Risk",
    version: "v1.8.3",
    status: "healthy",
    description: "Real-time portfolio risk manager. Monitors Kelly fraction, drawdown limits, and correlated exposures.",
    icon: Shield,
    accuracy: 96.1,
    latency: 15,
    throughput: 2400,
    uptime: 99.99,
    lastHeartbeat: "1s ago",
    sparkline: [{ v: 93 }, { v: 95 }, { v: 94 }, { v: 96 }, { v: 95 }, { v: 97 }, { v: 96 }, { v: 96 }],
    tags: ["Core", "Live", "Risk"],
  },
  {
    id: "learning",
    name: "Learning Engine",
    shortName: "Learning",
    version: "v1.3.0",
    status: "training",
    description: "Automated retraining pipeline. Currently ingesting Q2 2024 match data across 12 leagues.",
    icon: BookOpen,
    accuracy: 87.4,
    latency: 0,
    throughput: 0,
    uptime: 98.50,
    lastHeartbeat: "Training…",
    sparkline: [{ v: 78 }, { v: 80 }, { v: 82 }, { v: 81 }, { v: 83 }, { v: 84 }, { v: 85 }, { v: 87 }],
    tags: ["Background", "Training"],
  },
  {
    id: "tactical",
    name: "Tactical Engine",
    shortName: "Tactical",
    version: "v2.1.2",
    status: "running",
    description: "Formation and press-intensity analysis. Uses player-tracking data to model tactical matchups.",
    icon: Layers,
    accuracy: 88.1,
    latency: 180,
    throughput: 120,
    uptime: 99.85,
    lastHeartbeat: "8s ago",
    sparkline: [{ v: 82 }, { v: 84 }, { v: 83 }, { v: 85 }, { v: 86 }, { v: 87 }, { v: 87 }, { v: 88 }],
    tags: ["Modelling"],
    dependencies: ["Statistical Engine", "Historical Engine"],
  },
  {
    id: "historical",
    name: "Historical Engine",
    shortName: "Historical",
    version: "v3.0.1",
    status: "healthy",
    description: "Indexes 1.2M historical fixtures. Pattern-matches analogous games and surfaces base-rate statistics.",
    icon: Database,
    accuracy: 92.7,
    latency: 65,
    throughput: 420,
    uptime: 99.96,
    lastHeartbeat: "3s ago",
    sparkline: [{ v: 90 }, { v: 91 }, { v: 92 }, { v: 91 }, { v: 93 }, { v: 92 }, { v: 93 }, { v: 93 }],
    tags: ["Core", "Data"],
  },
  {
    id: "consensus",
    name: "Consensus Engine",
    shortName: "Consensus",
    version: "v5.0.1",
    status: "running",
    description: "Ensemble aggregator. Combines all engine outputs using learned weight vectors updated daily.",
    icon: Brain,
    accuracy: 93.8,
    latency: 55,
    throughput: 840,
    uptime: 99.92,
    lastHeartbeat: "5s ago",
    sparkline: [{ v: 89 }, { v: 91 }, { v: 92 }, { v: 91 }, { v: 93 }, { v: 94 }, { v: 93 }, { v: 94 }],
    tags: ["Core"],
    dependencies: ["All Engines"],
  },
  {
    id: "explainability",
    name: "Explainability Engine",
    shortName: "Explainability",
    version: "v0.8.1",
    status: "beta",
    description: "SHAP-based attribution — explains which features drive each prediction in plain language.",
    icon: Microscope,
    accuracy: 84.2,
    latency: 230,
    throughput: 90,
    uptime: 97.30,
    lastHeartbeat: "22s ago",
    sparkline: [{ v: 72 }, { v: 75 }, { v: 78 }, { v: 77 }, { v: 80 }, { v: 82 }, { v: 83 }, { v: 84 }],
    tags: ["Beta", "Explainability"],
  },
  {
    id: "sentiment",
    name: "Sentiment Engine",
    shortName: "Sentiment",
    version: "v0.2.0",
    status: "training",
    description: "NLP pipeline parsing team news, injury reports, and social signals. In active development.",
    icon: MessageSquare,
    accuracy: 71.5,
    latency: 0,
    throughput: 0,
    uptime: 94.10,
    lastHeartbeat: "Training…",
    sparkline: [{ v: 55 }, { v: 58 }, { v: 62 }, { v: 65 }, { v: 68 }, { v: 70 }, { v: 71 }, { v: 71 }],
    tags: ["Future", "Training"],
  },
  {
    id: "computer-vision",
    name: "Computer Vision Engine",
    shortName: "Vision",
    version: "v0.1.0",
    status: "planned",
    description: "Video analysis for press intensity, heatmaps, and set-piece pattern extraction. Roadmap Q3 2024.",
    icon: Eye,
    accuracy: 0,
    latency: 0,
    throughput: 0,
    uptime: 0,
    lastHeartbeat: "—",
    sparkline: [],
    tags: ["Planned"],
  },
  {
    id: "arbitrage",
    name: "Arbitrage Scanner",
    shortName: "Arbitrage",
    version: "v2.3.0",
    status: "running",
    description: "Cross-book opportunity scanner. Monitors 3-way, 2-way, and Asian handicap markets for positive ROI windows.",
    icon: Activity,
    accuracy: 99.1,
    latency: 12,
    throughput: 3200,
    uptime: 99.88,
    lastHeartbeat: "1s ago",
    sparkline: [{ v: 96 }, { v: 97 }, { v: 96 }, { v: 98 }, { v: 97 }, { v: 99 }, { v: 98 }, { v: 99 }],
    tags: ["Core", "Live", "Arbitrage"],
  },
];

/* ─── Status config ─── */
const STATUS_CONFIG: Record<EngineStatus, { label: string; color: string; dot: string; bg: string }> = {
  healthy:  { label: "Healthy",  color: "text-emerald",          dot: "bg-emerald",          bg: "border-emerald/20 bg-emerald/[0.06]"   },
  running:  { label: "Running",  color: "text-sky-400",          dot: "bg-sky-400",          bg: "border-sky-400/20 bg-sky-400/[0.06]"   },
  idle:     { label: "Idle",     color: "text-muted-foreground", dot: "bg-muted-foreground", bg: "border-white/10 bg-white/[0.03]"       },
  training: { label: "Training", color: "text-amber-400",        dot: "bg-amber-400",        bg: "border-amber-400/20 bg-amber-400/[0.06]"},
  beta:     { label: "Beta",     color: "text-violet-400",       dot: "bg-violet-400",       bg: "border-violet-400/20 bg-violet-400/[0.06]"},
  planned:  { label: "Planned",  color: "text-muted-foreground/50", dot: "bg-muted-foreground/30", bg: "border-white/5 bg-white/[0.01]" },
  degraded: { label: "Degraded", color: "text-red-400",          dot: "bg-red-400",          bg: "border-red-400/20 bg-red-400/[0.06]"  },
};

type Filter = "all" | "healthy" | "running" | "training" | "idle" | "beta" | "planned";

/* ─── Engine card ─── */
function EngineCard({ engine }: { engine: Engine }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[engine.status];
  const Icon = engine.icon;
  const isPlanned = engine.status === "planned";

  return (
    <div className={`rounded-xl border transition-all duration-200 ${expanded ? "shadow-lg" : ""} ${cfg.bg} card-lift`}>
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full text-left p-4"
        aria-expanded={expanded}
        aria-label={`${engine.name} — ${cfg.label}. Click to ${expanded ? "collapse" : "expand"}`}
      >
        <div className="flex items-start gap-3">
          <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border ${cfg.bg}`}>
            <Icon className={`h-4.5 w-4.5 ${cfg.color} ${isPlanned ? "opacity-40" : ""}`} aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm leading-tight">{engine.name}</span>
              <span className="text-[10px] font-mono text-muted-foreground">{engine.version}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={`relative flex h-1.5 w-1.5 shrink-0`} aria-hidden="true">
                {(engine.status === "healthy" || engine.status === "running") && (
                  <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${cfg.dot} opacity-60`} />
                )}
                <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
              </span>
              <span className={`text-[11px] font-medium ${cfg.color}`}>{cfg.label}</span>
              <span className="text-muted-foreground/30 text-[10px]">·</span>
              <span className="text-[10px] text-muted-foreground">{engine.lastHeartbeat}</span>
              <div className="ml-auto flex items-center gap-1">
                {engine.tags.slice(0, 2).map((t) => (
                  <span key={t} className="rounded-full border border-white/10 bg-white/5 px-1.5 py-0.5 text-[9px] text-muted-foreground">{t}</span>
                ))}
              </div>
            </div>
          </div>
          {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden="true" /> : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden="true" />}
        </div>
      </button>

      {/* Body — metrics */}
      {!isPlanned && (
        <div className="border-t border-white/[0.06] px-4 py-3 grid grid-cols-4 gap-3">
          {[
            { label: "Accuracy",    value: `${engine.accuracy}%`,   color: engine.accuracy > 90 ? "text-emerald" : engine.accuracy > 80 ? "text-foreground" : "text-amber-400" },
            { label: "Latency",     value: engine.latency > 0 ? `${engine.latency}ms` : "—", color: engine.latency < 50 ? "text-emerald" : engine.latency < 200 ? "text-foreground" : "text-amber-400" },
            { label: "Throughput",  value: engine.throughput > 0 ? `${engine.throughput}/m` : "—", color: "text-foreground" },
            { label: "Uptime",      value: engine.uptime > 0 ? `${engine.uptime}%` : "—",  color: engine.uptime > 99.9 ? "text-emerald" : engine.uptime > 99 ? "text-foreground" : "text-amber-400" },
          ].map((m) => (
            <div key={m.label} className="text-center">
              <div className="text-[9px] text-muted-foreground uppercase tracking-wider">{m.label}</div>
              <div className={`font-mono text-sm font-bold ${m.color}`}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Sparkline */}
      {engine.sparkline.length > 0 && (
        <div className="border-t border-white/[0.06] px-4 pt-2 pb-1">
          <div className="text-[9px] text-muted-foreground/60 mb-1">Performance (1h)</div>
          <ResponsiveContainer width="100%" height={32}>
            <LineChart data={engine.sparkline}>
              <Line
                type="monotone"
                dataKey="v"
                stroke={engine.status === "healthy" ? "oklch(0.74 0.18 158)" : engine.status === "running" ? "#38bdf8" : engine.status === "training" ? "#fbbf24" : "oklch(0.72 0.19 245)"}
                strokeWidth={1.5}
                dot={false}
              />
              <Tooltip
                contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(0.25 0.02 260)", borderRadius: 8, fontSize: 10 }}
                itemStyle={{ color: "oklch(0.85 0.01 260)" }}
                formatter={(v: number) => [`${v}%`, "Score"]}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {isPlanned && (
        <div className="border-t border-white/[0.06] px-4 py-3 text-center">
          <span className="text-[10px] text-muted-foreground/50">Not yet active — scheduled for future release</span>
        </div>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-white/[0.06] px-4 py-3 space-y-3">
          <div>
            <div className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground/60 mb-1">Description</div>
            <p className="text-xs text-muted-foreground leading-relaxed">{engine.description}</p>
          </div>
          {engine.dependencies && (
            <div>
              <div className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground/60 mb-1">Dependencies</div>
              <div className="flex flex-wrap gap-1">
                {engine.dependencies.map((d) => (
                  <span key={d} className="rounded-md border border-white/5 bg-white/5 px-2 py-0.5 text-[10px] text-muted-foreground">{d}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Page ─── */
function AIEnginesPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return ENGINES.filter((e) => {
      if (filter !== "all" && e.status !== filter) return false;
      if (search && !e.name.toLowerCase().includes(search.toLowerCase()) && !e.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))) return false;
      return true;
    });
  }, [filter, search]);

  const counts = useMemo(() => ({
    healthy:  ENGINES.filter((e) => e.status === "healthy").length,
    running:  ENGINES.filter((e) => e.status === "running").length,
    training: ENGINES.filter((e) => e.status === "training").length,
    idle:     ENGINES.filter((e) => e.status === "idle").length,
    beta:     ENGINES.filter((e) => e.status === "beta").length,
    planned:  ENGINES.filter((e) => e.status === "planned").length,
  }), []);

  const FILTERS: { key: Filter; label: string; count: number }[] = [
    { key: "all",      label: "All",      count: ENGINES.length },
    { key: "healthy",  label: "Healthy",  count: counts.healthy },
    { key: "running",  label: "Running",  count: counts.running },
    { key: "training", label: "Training", count: counts.training },
    { key: "idle",     label: "Idle",     count: counts.idle },
    { key: "beta",     label: "Beta",     count: counts.beta },
    { key: "planned",  label: "Planned",  count: counts.planned },
  ];

  const onlineCount = counts.healthy + counts.running;

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence Infrastructure"
        title="AI Engine Monitor"
        description="Real-time status and performance telemetry across all TITAN intelligence engines."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-lg border border-white/5 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors btn-press" aria-label="Refresh engine status">
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Refresh
          </button>
        }
      />

      {/* Summary strip */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Online",   value: onlineCount,       icon: CheckCircle2, color: "text-emerald",    bg: "border-emerald/20 bg-emerald/[0.06]"    },
          { label: "Training", value: counts.training,   icon: RefreshCw,    color: "text-amber-400",  bg: "border-amber-400/20 bg-amber-400/[0.06]" },
          { label: "Idle",     value: counts.idle,       icon: Clock,        color: "text-muted-foreground", bg: "border-white/10 bg-white/[0.03]"  },
          { label: "Total",    value: ENGINES.length,    icon: Server,       color: "text-primary",    bg: "border-primary/20 bg-primary/[0.06]"    },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className={`flex items-center gap-3 rounded-xl border p-4 ${s.bg}`}>
              <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border ${s.bg}`}>
                <Icon className={`h-4.5 w-4.5 ${s.color}`} aria-hidden="true" />
              </div>
              <div>
                <div className={`font-display text-2xl font-bold ${s.color}`}>{s.value}</div>
                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filters + search */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)}
              aria-pressed={filter === f.key}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors btn-press ${filter === f.key ? "border-primary/30 bg-primary/10 text-foreground" : "border-white/5 bg-white/5 text-muted-foreground hover:text-foreground"}`}>
              {f.label}
              <span className={`rounded-full px-1 text-[9px] ${filter === f.key ? "bg-primary/20 text-primary" : "bg-white/5"}`}>{f.count}</span>
            </button>
          ))}
        </div>
        <div className="ml-auto relative">
          <Brain className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search engines…" aria-label="Search engines"
            className="h-8 w-48 rounded-lg border border-white/5 bg-white/5 pl-8 pr-3 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/20" />
        </div>
      </div>

      {/* Engine grid */}
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2" role="list" aria-label="AI Engines">
        {filtered.map((engine) => (
          <div key={engine.id} role="listitem">
            <EngineCard engine={engine} />
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
          <div className="grid h-12 w-12 place-items-center rounded-full bg-white/5">
            <Brain className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
          </div>
          <div>
            <div className="text-sm font-medium">No engines match</div>
            <div className="text-xs text-muted-foreground mt-0.5">Try a different filter or search term.</div>
          </div>
        </div>
      )}
    </div>
  );
}
