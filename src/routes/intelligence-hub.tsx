import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import { Badge, ProgressBar } from "../components/titan/ds";
import {
  Brain, Activity, FlaskConical, Clock, Bell, FileText, Database,
  Zap, Play, RefreshCw, ArrowRight, CheckCircle2, Loader2,
  AlertTriangle, Wifi, WifiOff, Layers, BookOpen, Search,
  Target, ChevronRight, Plus, CircleDot, Cpu,
} from "lucide-react";

export const Route = createFileRoute("/intelligence-hub")({ component: IntelligenceHub });

/* ─── mock data ─── */

const engines = [
  { name: "Market Intelligence", short: "Market", status: "online" as const,  health: 98, cpu: 34, latency: "241ms" },
  { name: "Statistical Engine",  short: "Stats",  status: "online" as const,  health: 96, cpu: 52, latency: "312ms" },
  { name: "Historical Engine",   short: "History",status: "online" as const,  health: 94, cpu: 28, latency: "198ms" },
  { name: "Tactical Engine",     short: "Tactical",status: "training" as const,health: 71, cpu: 89, latency: "890ms" },
  { name: "Risk Engine",         short: "Risk",   status: "online" as const,  health: 92, cpu: 21, latency: "189ms" },
  { name: "Consensus Engine",    short: "Consensus",status:"online" as const, health: 89, cpu: 44, latency: "428ms" },
  { name: "Explainability",      short: "Explain",status: "beta" as const,    health: 68, cpu: 61, latency: "1.2s"  },
  { name: "Prediction Engine",   short: "Predict",status: "training" as const,health: 74, cpu: 78, latency: "621ms" },
  { name: "Backtesting Engine",  short: "Backtest",status:"online" as const,  health: 90, cpu: 18, latency: "3.4s"  },
];

const activeSessions = [
  { id: "s1", title: "Man City vs Arsenal — Pre-match deep analysis", engine: "Consensus Engine", started: "4m ago",  progress: 72, status: "running"  },
  { id: "s2", title: "Bundesliga Week 32 — Value sweep",              engine: "Statistical Engine",started: "11m ago", progress: 45, status: "running"  },
  { id: "s3", title: "Serie A Historical Pattern — Over 2.5",         engine: "Historical Engine", started: "23m ago", progress: 91, status: "finishing"},
];

const researchQueue = [
  { id: "q1", title: "UCL Quarterfinal — Tactical breakdown",  priority: "high",   engines: 4, eta: "~6m"  },
  { id: "q2", title: "Premier League EV sweep — GW32",         priority: "medium", engines: 6, eta: "~14m" },
  { id: "q3", title: "La Liga Over/Under model recalibration", priority: "low",    engines: 2, eta: "~31m" },
  { id: "q4", title: "Arbitrage window scan — all books",      priority: "medium", engines: 3, eta: "~8m"  },
];

const dataSources = [
  { name: "Opta / StatsPerform",  type: "Match Data",    status: "placeholder", note: "Connect when live" },
  { name: "Betfair Exchange API",  type: "Live Odds",     status: "placeholder", note: "Connect when live" },
  { name: "Pinnacle Feed",         type: "Bookmaker",     status: "placeholder", note: "Connect when live" },
  { name: "WhoScored / FBref",     type: "Analytics",     status: "placeholder", note: "Connect when live" },
  { name: "Internal Match DB",     type: "Historical",    status: "active",      note: "Mock data active" },
  { name: "AI Model Store",        type: "ML Models",     status: "active",      note: "Local models only" },
];

const recentAlerts = [
  { t: "2m ago",  type: "Value",     msg: "EV spike detected — Man City vs Arsenal (+6.8%)",           level: "primary" as const },
  { t: "8m ago",  type: "Arbitrage", msg: "3-way opportunity across Pinnacle / Bet365 / Betfair",       level: "emerald" as const },
  { t: "14m ago", type: "Model",     msg: "Confidence updated for Serie A slate (+2.1 pts)",            level: "primary" as const },
  { t: "26m ago", type: "Warning",   msg: "Tactical Engine training — signal weight reduced by 15%",    level: "warning" as const },
  { t: "41m ago", type: "System",    msg: "Historical Engine memory at 57% — within normal range",     level: "primary" as const },
];

const recentReports = [
  { id: "r1", title: "Weekly Intelligence Digest", date: "Jul 12, 2026", status: "final" as const, sections: 6 },
  { id: "r2", title: "Model Calibration Report",   date: "Jul 10, 2026", status: "final" as const, sections: 4 },
  { id: "r3", title: "Market Movement Study",       date: "Jul 8, 2026",  status: "draft" as const, sections: 8 },
];

const learningQueue = [
  { title: "Tactical Engine — Season 2026 formation data", eta: "~2d",  progress: 37, stage: "Preprocessing" },
  { title: "Prediction Engine — Recalibration cycle",      eta: "~18h", progress: 61, stage: "Training"      },
  { title: "Explainability — SHAP model update",           eta: "~5h",  progress: 84, stage: "Validation"    },
];

const quickActions = [
  { label: "New Research Session", icon: FlaskConical, href: "/research",    accent: "primary" },
  { label: "View Value Analysis",  icon: Target,       href: "/value-analysis", accent: "emerald" },
  { label: "Open Alert Center",    icon: Bell,         href: "/alerts",      accent: "warning"  },
  { label: "Generate Report",      icon: FileText,     href: "/reports",     accent: "primary"  },
  { label: "Check System Status",  icon: Activity,     href: "/system-status",accent: "primary" },
  { label: "AI Intelligence",      icon: Brain,        href: "/ai-intelligence",accent: "primary"},
];

/* ─── sub-components ─── */

function EngineStatusGrid() {
  const online   = engines.filter((e) => e.status === "online").length;
  const training = engines.filter((e) => e.status === "training").length;
  const beta     = engines.filter((e) => e.status === "beta").length;

  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="AI Engine Status"
        description={`${online} online · ${training} training · ${beta} beta`}
        action={
          <Link to="/ai-intelligence" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
            Full details <ArrowRight className="h-3 w-3" />
          </Link>
        }
      />
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-3 xl:grid-cols-3">
        {engines.map((e) => {
          const statusColor = {
            online:   "border-emerald/20 bg-emerald/5",
            training: "border-primary/20 bg-primary/5",
            idle:     "border-white/10 bg-white/[0.02]",
            offline:  "border-destructive/20 bg-destructive/5",
            beta:     "border-warning/20 bg-warning/5",
          }[e.status];
          const dotColor = {
            online: "bg-emerald animate-pulse", training: "bg-primary animate-pulse",
            idle: "bg-muted-foreground", offline: "bg-destructive", beta: "bg-warning",
          }[e.status];

          return (
            <div key={e.name} className={`rounded-lg border p-2.5 ${statusColor}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold text-muted-foreground truncate">{e.short}</span>
                <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${dotColor}`} />
              </div>
              <div className="font-mono text-sm font-bold">{e.health}%</div>
              <div className="mt-1.5">
                <div className="h-0.5 overflow-hidden rounded-full bg-white/10">
                  <div
                    className={`h-full rounded-full transition-all ${
                      e.status === "online" ? "bg-emerald" : e.status === "training" ? "bg-primary" : "bg-warning"
                    }`}
                    style={{ width: `${e.health}%` }}
                  />
                </div>
              </div>
              <div className="mt-1 flex items-center justify-between">
                <span className="text-[9px] text-muted-foreground font-mono">{e.latency}</span>
                <span className="text-[9px] text-muted-foreground font-mono">{e.cpu}% cpu</span>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

function ActiveResearchSessions() {
  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Active Research Sessions"
        description="Running analyses across the intelligence stack"
        action={
          <Link to="/research" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
            Open workspace <ArrowRight className="h-3 w-3" />
          </Link>
        }
      />
      <div className="space-y-3">
        {activeSessions.map((s) => (
          <div key={s.id} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-md ${
                s.status === "finishing" ? "bg-emerald/10 text-emerald" : "bg-primary/10 text-primary"
              }`}>
                {s.status === "finishing"
                  ? <CheckCircle2 className="h-3.5 w-3.5" />
                  : <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-medium leading-tight">{s.title}</p>
                  <span className="shrink-0 font-mono text-[10px] text-muted-foreground">{s.started}</span>
                </div>
                <div className="mt-1 text-[10px] text-muted-foreground">{s.engine}</div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        s.status === "finishing" ? "bg-emerald" : "bg-gradient-to-r from-primary to-emerald"
                      }`}
                      style={{ width: `${s.progress}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-muted-foreground">{s.progress}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function ResearchQueue() {
  const priorityStyles = {
    high:   "text-destructive bg-destructive/10 border-destructive/20",
    medium: "text-warning bg-warning/10 border-warning/20",
    low:    "text-muted-foreground bg-white/5 border-white/10",
  };

  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Research Queue"
        description="Pending analyses waiting to run"
        action={
          <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-muted-foreground hover:text-foreground">
            <Plus className="h-3 w-3" /> Add
          </button>
        }
      />
      <div className="space-y-2">
        {researchQueue.map((item, i) => (
          <div key={item.id} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
            <span className="shrink-0 font-mono text-[10px] text-muted-foreground/50 w-4">{i + 1}</span>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium truncate">{item.title}</p>
              <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>{item.engines} engines</span>
                <span>·</span>
                <span className="font-mono">ETA {item.eta}</span>
              </div>
            </div>
            <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${priorityStyles[item.priority as keyof typeof priorityStyles]}`}>
              {item.priority}
            </span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function ConnectedDataSources() {
  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Connected Data Sources"
        description="Live integrations and internal feeds"
      />
      <div className="space-y-2">
        {dataSources.map((ds) => (
          <div key={ds.name} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
            <div className={`grid h-7 w-7 shrink-0 place-items-center rounded-md ${
              ds.status === "active" ? "bg-emerald/10 text-emerald" : "bg-white/5 text-muted-foreground/40"
            }`}>
              {ds.status === "active" ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium">{ds.name}</span>
                <Badge variant="muted" size="sm">{ds.type}</Badge>
              </div>
              <span className="text-[10px] text-muted-foreground">{ds.note}</span>
            </div>
            {ds.status === "placeholder" && (
              <button className="shrink-0 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[10px] text-muted-foreground hover:text-foreground">
                Connect
              </button>
            )}
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function RecentAlerts() {
  const levelStyles = {
    primary: { bg: "bg-primary/10 text-primary",     text: "text-primary"     },
    emerald: { bg: "bg-emerald/10 text-emerald",     text: "text-emerald"     },
    warning: { bg: "bg-warning/10 text-warning",     text: "text-warning"     },
  };

  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Recent Alerts"
        description="Latest signals from all engines"
        action={
          <Link to="/alerts" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
            All alerts <ArrowRight className="h-3 w-3" />
          </Link>
        }
      />
      <div className="space-y-2">
        {recentAlerts.map((a, i) => {
          const style = levelStyles[a.level];
          return (
            <div key={i} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
              <div className={`grid h-7 w-7 shrink-0 place-items-center rounded-md ${style.bg}`}>
                <Bell className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-semibold uppercase tracking-wider ${style.text}`}>{a.type}</span>
                  <span className="text-[10px] text-muted-foreground">{a.t}</span>
                </div>
                <p className="truncate text-xs text-muted-foreground">{a.msg}</p>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

function RecentReports() {
  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Recent Reports"
        description="Latest generated intelligence reports"
        action={
          <Link to="/reports" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
            All reports <ArrowRight className="h-3 w-3" />
          </Link>
        }
      />
      <div className="space-y-2">
        {recentReports.map((r) => (
          <div key={r.id} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-primary/10 text-primary">
              <FileText className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium">{r.title}</p>
              <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>{r.date}</span>
                <span>·</span>
                <span>{r.sections} sections</span>
              </div>
            </div>
            <Badge variant={r.status === "final" ? "emerald" : "warning"} size="sm">{r.status}</Badge>
          </div>
        ))}
        <Link
          to="/reports"
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-white/10 py-2.5 text-xs text-muted-foreground hover:border-white/20 hover:text-foreground transition-colors"
        >
          <Plus className="h-3.5 w-3.5" /> Generate new report
        </Link>
      </div>
    </GlassCard>
  );
}

function LearningQueue() {
  return (
    <GlassCard className="p-5">
      <SectionTitle
        title="Learning Queue"
        description="Active model training and calibration"
      />
      <div className="space-y-3">
        {learningQueue.map((item) => (
          <div key={item.title} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-medium leading-tight">{item.title}</p>
              <span className="shrink-0 font-mono text-[10px] text-muted-foreground ml-2">{item.eta}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="sm">{item.stage}</Badge>
            </div>
            <div className="mt-2">
              <ProgressBar value={item.progress} variant="gradient" size="sm" showValue={false} />
              <div className="mt-1 text-right font-mono text-[9px] text-muted-foreground">{item.progress}%</div>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-center text-[10px] text-muted-foreground">
        Training runs automatically · Engines remain available during training
      </p>
    </GlassCard>
  );
}

function QuickActions() {
  const accentStyles = {
    primary: "border-primary/20 bg-primary/5 text-primary hover:bg-primary/10",
    emerald: "border-emerald/20 bg-emerald/5 text-emerald hover:bg-emerald/10",
    warning: "border-warning/20 bg-warning/5 text-warning hover:bg-warning/10",
  };

  return (
    <GlassCard className="p-5">
      <SectionTitle title="Quick Actions" description="Frequent analyst workflows" />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {quickActions.map((a) => {
          const Icon = a.icon;
          const style = accentStyles[a.accent as keyof typeof accentStyles];
          return (
            <Link
              key={a.label}
              to={a.href as "/research" | "/value-analysis" | "/alerts" | "/reports" | "/system-status" | "/ai-intelligence"}
              className={`flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-xs font-medium transition-colors ${style}`}
            >
              <Icon className="h-3.5 w-3.5 shrink-0" />
              <span className="leading-tight">{a.label}</span>
            </Link>
          );
        })}
      </div>
    </GlassCard>
  );
}

/* ─── page ─── */

function IntelligenceHub() {
  const onlineCount   = engines.filter((e) => e.status === "online").length;
  const avgHealth     = Math.round(engines.reduce((s, e) => s + e.health, 0) / engines.length);
  const activeCount   = activeSessions.length;
  const queueCount    = researchQueue.length;

  return (
    <>
      <PageHeader
        eyebrow="Mission Control"
        title="Intelligence Hub"
        description="Platform-wide overview — engine status, active sessions, alerts, and queues in one place."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        }
      />

      {/* KPI strip */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Engines Online"     value={`${onlineCount} / ${engines.length}`} icon={Brain}       accent="emerald" />
        <StatCard label="Ensemble Health"    value={`${avgHealth}%`}  delta={{ value: "+1.6%", positive: true }} icon={Activity} accent="primary" />
        <StatCard label="Active Sessions"    value={activeCount}       sub="analyses running" icon={FlaskConical} accent="primary" />
        <StatCard label="Queued Analyses"    value={queueCount}        sub="pending execution" icon={Clock}    />
      </div>

      {/* Quick Actions — always visible at the top */}
      <div className="mb-4">
        <QuickActions />
      </div>

      {/* Main grid — 2 columns on large screens */}
      <div className="grid gap-4 xl:grid-cols-3">
        {/* Left column — wide */}
        <div className="space-y-4 xl:col-span-2">
          <EngineStatusGrid />
          <ActiveResearchSessions />
          <ConnectedDataSources />
        </div>

        {/* Right column — narrow */}
        <div className="space-y-4">
          <ResearchQueue />
          <RecentAlerts />
          <RecentReports />
          <LearningQueue />
        </div>
      </div>
    </>
  );
}
