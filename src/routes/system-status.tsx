import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, SectionTitle } from "../components/titan/primitives";
import { HealthIndicator } from "../components/titan/ConfidenceWidgets";
import {
  Server, Database, HardDrive, Shield, Bell, Cpu, Calendar,
  Clock, CheckCircle2, AlertTriangle, RefreshCw, ExternalLink,
  Activity, Globe, Lock, Zap, Radio, GitBranch,
} from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/system-status")({ component: SystemStatusPage });

type ServiceStatus = "healthy" | "degraded" | "critical" | "offline" | "unknown";

interface Service {
  name: string;
  status: ServiceStatus;
  uptime: string;
  latency: string;
  detail: string;
  icon: React.ComponentType<{ className?: string }>;
  category: string;
}

const services: Service[] = [
  // Core
  { name: "Application Server", status: "healthy",  uptime: "99.98%", latency: "42ms",  detail: "All nodes responsive",          icon: Server,   category: "Core Infrastructure" },
  { name: "Primary Database",   status: "healthy",  uptime: "99.99%", latency: "8ms",   detail: "Replication lag: 0ms",           icon: Database, category: "Core Infrastructure" },
  { name: "Read Replica",       status: "healthy",  uptime: "99.97%", latency: "11ms",  detail: "2 replicas active",              icon: Database, category: "Core Infrastructure" },
  { name: "Cache Layer",        status: "healthy",  uptime: "100%",   latency: "1ms",   detail: "Hit rate: 94.2%",                icon: Zap,      category: "Core Infrastructure" },
  { name: "Object Storage",     status: "healthy",  uptime: "100%",   latency: "23ms",  detail: "8.4 TB used of 20 TB",          icon: HardDrive,category: "Core Infrastructure" },
  // Workers & Schedulers
  { name: "Job Workers",        status: "healthy",  uptime: "99.94%", latency: "—",     detail: "12 / 16 workers active",        icon: Cpu,      category: "Workers & Schedulers" },
  { name: "Task Scheduler",     status: "healthy",  uptime: "99.96%", latency: "—",     detail: "Next run: in 4 minutes",        icon: Calendar, category: "Workers & Schedulers" },
  { name: "Cron Jobs",          status: "healthy",  uptime: "99.9%",  latency: "—",     detail: "14 jobs, all on schedule",      icon: Clock,    category: "Workers & Schedulers" },
  { name: "Message Queue",      status: "healthy",  uptime: "99.99%", latency: "3ms",   detail: "Queue depth: 0 messages",       icon: GitBranch,category: "Workers & Schedulers" },
  // Auth & Security
  { name: "Authentication",     status: "healthy",  uptime: "100%",   latency: "18ms",  detail: "OAuth + JWT verified",          icon: Lock,     category: "Auth & Security" },
  { name: "Authorization",      status: "healthy",  uptime: "100%",   latency: "4ms",   detail: "RBAC active · 3 roles",         icon: Shield,   category: "Auth & Security" },
  { name: "API Gateway",        status: "healthy",  uptime: "99.97%", latency: "6ms",   detail: "Rate limit: 94% headroom",      icon: Globe,    category: "Auth & Security" },
  // Data Sources
  { name: "Pinnacle Feed",      status: "healthy",  uptime: "99.8%",  latency: "84ms",  detail: "2,840 markets streaming",       icon: Radio,    category: "Data Sources" },
  { name: "Bet365 Feed",        status: "healthy",  uptime: "99.4%",  latency: "102ms", detail: "2,107 markets streaming",       icon: Radio,    category: "Data Sources" },
  { name: "Betfair Exchange",   status: "healthy",  uptime: "99.6%",  latency: "91ms",  detail: "1,894 markets streaming",       icon: Radio,    category: "Data Sources" },
  { name: "BetVictor Feed",     status: "degraded", uptime: "96.2%",  latency: "680ms", detail: "High latency · investigating",  icon: Radio,    category: "Data Sources" },
  { name: "William Hill Feed",  status: "healthy",  uptime: "99.1%",  latency: "118ms", detail: "1,542 markets streaming",       icon: Radio,    category: "Data Sources" },
  // Notifications
  { name: "Notification Engine",status: "healthy",  uptime: "99.95%", latency: "12ms",  detail: "128 alerts delivered today",    icon: Bell,     category: "Notifications" },
  { name: "Email Service",      status: "healthy",  uptime: "99.9%",  latency: "—",     detail: "Delivery rate: 99.7%",          icon: Bell,     category: "Notifications" },
  // AI Services
  { name: "Statistical Engine", status: "healthy",  uptime: "99.8%",  latency: "312ms", detail: "Inference running",             icon: Activity, category: "AI Services" },
  { name: "Market Engine",      status: "healthy",  uptime: "99.7%",  latency: "241ms", detail: "Inference running",             icon: Activity, category: "AI Services" },
  { name: "Tactical Engine",    status: "degraded", uptime: "97.4%",  latency: "890ms", detail: "Training — reduced capacity",   icon: Activity, category: "AI Services" },
  { name: "Risk Engine",        status: "healthy",  uptime: "99.6%",  latency: "189ms", detail: "Inference running",             icon: Activity, category: "AI Services" },
  { name: "Consensus Engine",   status: "healthy",  uptime: "99.5%",  latency: "428ms", detail: "Ensemble active",               icon: Activity, category: "AI Services" },
];

const uptimeData = [
  { t: "Jan", uptime: 99.94 }, { t: "Feb", uptime: 99.97 }, { t: "Mar", uptime: 99.89 },
  { t: "Apr", uptime: 99.99 }, { t: "May", uptime: 99.95 }, { t: "Jun", uptime: 99.98 },
  { t: "Jul", uptime: 99.96 },
];

const incidents = [
  { id: "INC-0041", title: "BetVictor Feed elevated latency", status: "investigating", severity: "warning", started: "41 min ago", updated: "12 min ago" },
  { id: "INC-0040", title: "Tactical Engine training overhead", status: "monitoring",   severity: "info",    started: "3h ago",     updated: "1h ago" },
  { id: "INC-0039", title: "Statistical Engine cache flush",   status: "resolved",     severity: "info",    started: "Yesterday",  updated: "Resolved" },
  { id: "INC-0038", title: "Bet365 feed intermittent errors",  status: "resolved",     severity: "warning", started: "3 days ago", updated: "Resolved" },
];

const categories = Array.from(new Set(services.map((s) => s.category)));

function ServiceRow({ service }: { service: Service }) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto_auto_auto] items-center gap-4 px-4 py-3 border-b border-white/[0.04] hover:bg-white/[0.02] last:border-0">
      <div className={`grid h-7 w-7 place-items-center rounded-md ${
        service.status === "healthy"  ? "bg-emerald/10 text-emerald" :
        service.status === "degraded" ? "bg-warning/10 text-warning" :
        service.status === "critical" ? "bg-destructive/10 text-destructive" : "bg-white/5 text-muted-foreground"
      }`}>
        <service.icon className="h-3.5 w-3.5" />
      </div>
      <div>
        <div className="text-sm font-medium">{service.name}</div>
        <div className="text-[11px] text-muted-foreground">{service.detail}</div>
      </div>
      <div className="text-right">
        <div className="text-[11px] font-mono text-muted-foreground">{service.latency}</div>
        <div className="text-[9px] text-muted-foreground/60">latency</div>
      </div>
      <div className="text-right">
        <div className="text-[11px] font-mono">{service.uptime}</div>
        <div className="text-[9px] text-muted-foreground/60">30d uptime</div>
      </div>
      <div className="flex justify-end">
        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
          service.status === "healthy"  ? "border-emerald/20 bg-emerald/10 text-emerald" :
          service.status === "degraded" ? "border-warning/20 bg-warning/10 text-warning" :
          service.status === "critical" ? "border-destructive/20 bg-destructive/10 text-destructive" :
          "border-white/10 bg-white/5 text-muted-foreground"
        }`}>
          <span className={`h-1.5 w-1.5 rounded-full ${
            service.status === "healthy"  ? "bg-emerald" :
            service.status === "degraded" ? "bg-warning" :
            service.status === "critical" ? "bg-destructive" : "bg-muted-foreground"
          }`} />
          {service.status}
        </span>
      </div>
    </div>
  );
}

function SystemStatusPage() {
  const healthyCnt  = services.filter((s) => s.status === "healthy").length;
  const degradedCnt = services.filter((s) => s.status === "degraded").length;
  const criticalCnt = services.filter((s) => s.status === "critical").length;
  const totalCnt    = services.length;

  const overallStatus: ServiceStatus =
    criticalCnt > 0 ? "critical" :
    degradedCnt > 0 ? "degraded" : "healthy";

  const overallLabel = overallStatus === "healthy" ? "All Systems Operational" :
    overallStatus === "degraded" ? "Partial Service Degradation" : "Service Disruption";

  return (
    <>
      <PageHeader
        eyebrow="Infrastructure"
        title="System Status"
        description="Real-time health monitoring across all platform services and integrations."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        }
      />

      {/* Overall status banner */}
      <div className={`mb-6 flex items-center gap-4 rounded-xl border p-4 ${
        overallStatus === "healthy"  ? "border-emerald/20 bg-emerald/[0.06]" :
        overallStatus === "degraded" ? "border-warning/20 bg-warning/[0.06]" :
        "border-destructive/20 bg-destructive/[0.06]"
      }`}>
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-full ${
          overallStatus === "healthy"  ? "bg-emerald/20 text-emerald" :
          overallStatus === "degraded" ? "bg-warning/20 text-warning" : "bg-destructive/20 text-destructive"
        }`}>
          {overallStatus === "healthy" ? <CheckCircle2 className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
        </div>
        <div>
          <div className={`font-display text-base font-semibold ${
            overallStatus === "healthy" ? "text-emerald" :
            overallStatus === "degraded" ? "text-warning" : "text-destructive"
          }`}>{overallLabel}</div>
          <div className="text-xs text-muted-foreground">
            {healthyCnt} healthy · {degradedCnt} degraded · {criticalCnt} critical · Last updated just now
          </div>
        </div>
        <div className="ml-auto hidden sm:flex items-center gap-4 text-center">
          <div>
            <div className="font-display text-xl font-bold text-emerald">{healthyCnt}</div>
            <div className="text-[10px] text-muted-foreground">Healthy</div>
          </div>
          <div>
            <div className="font-display text-xl font-bold text-warning">{degradedCnt}</div>
            <div className="text-[10px] text-muted-foreground">Degraded</div>
          </div>
          <div>
            <div className="font-display text-xl font-bold">{totalCnt}</div>
            <div className="text-[10px] text-muted-foreground">Total</div>
          </div>
        </div>
      </div>

      {/* KPI row */}
      <div className="mb-6 grid gap-3 sm:grid-cols-4">
        <StatCard label="Platform Uptime" value="99.96%" sub="rolling 30 days" icon={Activity} accent="emerald" />
        <StatCard label="Avg Response" value="42ms" sub="p95: 94ms" icon={Zap} accent="primary" />
        <StatCard label="Services Online" value={`${healthyCnt}/${totalCnt}`} sub={`${degradedCnt} degraded`} icon={Server} />
        <StatCard label="Open Incidents" value={String(incidents.filter((i) => i.status !== "resolved").length)} sub="2 under investigation" icon={AlertTriangle} accent="warning" />
      </div>

      {/* Uptime chart */}
      <GlassCard className="mb-6 p-5">
        <SectionTitle title="Platform uptime — 7 months" description="Monthly availability percentage" />
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={uptimeData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gUptime" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
              <XAxis dataKey="t" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis domain={[99.5, 100]} stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }}
                formatter={(v: number) => [`${v.toFixed(2)}%`, "Uptime"]}
              />
              <Area type="monotone" dataKey="uptime" stroke="oklch(0.75 0.18 155)" strokeWidth={2} fill="url(#gUptime)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      {/* Service tables by category */}
      <div className="space-y-4 mb-6">
        {categories.map((cat) => {
          const catServices = services.filter((s) => s.category === cat);
          const catHealthy = catServices.filter((s) => s.status === "healthy").length;
          const catDegraded = catServices.filter((s) => s.status === "degraded").length;
          return (
            <GlassCard key={cat} className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className={`h-1.5 w-1.5 rounded-full ${catDegraded > 0 ? "bg-warning animate-pulse" : "bg-emerald"}`} />
                  <span className="font-display text-sm font-semibold">{cat}</span>
                </div>
                <div className="text-[11px] text-muted-foreground">
                  {catHealthy} / {catServices.length} healthy
                </div>
              </div>
              {catServices.map((s) => <ServiceRow key={s.name} service={s} />)}
            </GlassCard>
          );
        })}
      </div>

      {/* Incidents */}
      <GlassCard className="overflow-hidden">
        <div className="border-b border-white/5 px-4 py-3">
          <SectionTitle title="Incident History" description="Recent events and resolutions" />
        </div>
        <div className="divide-y divide-white/[0.04]">
          {incidents.map((inc) => (
            <div key={inc.id} className="flex items-start gap-4 px-4 py-3 hover:bg-white/[0.02]">
              <div className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                inc.status === "resolved" ? "bg-muted-foreground" :
                inc.severity === "warning" ? "bg-warning animate-pulse" : "bg-primary animate-pulse"
              }`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{inc.title}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{inc.id}</span>
                </div>
                <div className="mt-1 flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span>Started: {inc.started}</span>
                  <span>·</span>
                  <span>Updated: {inc.updated}</span>
                </div>
              </div>
              <div className="shrink-0 flex items-center gap-2">
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${
                  inc.status === "resolved"     ? "border-white/10 bg-white/5 text-muted-foreground" :
                  inc.status === "monitoring"   ? "border-primary/20 bg-primary/10 text-primary" :
                  "border-warning/20 bg-warning/10 text-warning"
                }`}>
                  {inc.status}
                </span>
                <button className="text-muted-foreground hover:text-foreground">
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </>
  );
}
