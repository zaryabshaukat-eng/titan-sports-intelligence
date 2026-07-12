import { useState, useEffect, useRef } from "react";
import {
  Activity, X, Cpu, Database, Radio, Zap, Server, GitBranch,
  CheckCircle2, Clock, AlertTriangle, Loader2,
} from "lucide-react";

interface LiveMetric {
  id: string;
  label: string;
  value: string;
  sub?: string;
  status: "healthy" | "warning" | "busy" | "idle";
  icon: React.ComponentType<{ className?: string }>;
  trend?: number; // percentage change
}

interface Job {
  id: string;
  name: string;
  status: "running" | "queued" | "complete" | "failed";
  progress?: number;
  elapsed: string;
}

function useFlicker<T>(base: T, variance: (v: T) => T, interval = 2000): T {
  const [val, setVal] = useState(base);
  useEffect(() => {
    const t = setInterval(() => setVal(variance(base)), interval + Math.random() * 1000);
    return () => clearInterval(t);
  }, []);
  return val;
}

interface LiveActivityCenterProps {
  open: boolean;
  onClose: () => void;
}

export function LiveActivityCenter({ open, onClose }: LiveActivityCenterProps) {
  const apiReqs = useFlicker(847, (v) => Math.round(v + (Math.random() - 0.4) * 30));
  const latency = useFlicker(42, (v) => Math.round(Math.max(18, v + (Math.random() - 0.5) * 8)));
  const workers = useFlicker(12, (v) => Math.max(8, Math.min(16, v + Math.round((Math.random() - 0.5) * 2))));
  const oddsUpdates = useFlicker(2840, (v) => Math.round(v + (Math.random() - 0.3) * 120));

  const metrics: LiveMetric[] = [
    { id: "api", label: "API Requests / min", value: String(apiReqs), sub: "across all sources", status: "healthy", icon: Radio },
    { id: "latency", label: "Avg Latency", value: `${latency}ms`, sub: "p95: 94ms", status: latency > 60 ? "warning" : "healthy", icon: Zap },
    { id: "workers", label: "Workers Active", value: String(workers), sub: "of 16 capacity", status: workers >= 14 ? "warning" : "healthy", icon: Cpu },
    { id: "odds", label: "Odds Updated / min", value: String(oddsUpdates.toLocaleString()), sub: "42 bookmakers", status: "healthy", icon: Activity },
    { id: "queue", label: "Jobs Queue", value: "3", sub: "2 running · 1 pending", status: "busy", icon: GitBranch },
    { id: "storage", label: "Storage I/O", value: "1.4 GB/s", sub: "read 1.1 · write 0.3", status: "healthy", icon: Database },
    { id: "sources", label: "Connected Sources", value: "41 / 42", sub: "BetVictor degraded", status: "warning", icon: Server },
    { id: "health", label: "System Health", value: "97.2%", sub: "SLO: 99.5%", status: "healthy", icon: CheckCircle2 },
  ];

  const jobs: Job[] = [
    { id: "j1", name: "Statistical Engine — Serie A slate", status: "running", progress: 67, elapsed: "2m 14s" },
    { id: "j2", name: "Historical pattern match — UCL R16", status: "running", progress: 31, elapsed: "48s" },
    { id: "j3", name: "Backtesting — Bundesliga Q1 2025", status: "queued", elapsed: "—" },
    { id: "j4", name: "Report generation — Weekly Value Digest", status: "complete", elapsed: "Done" },
    { id: "j5", name: "Market Intelligence refresh", status: "complete", elapsed: "Done" },
  ];

  const statusColor: Record<LiveMetric["status"], string> = {
    healthy: "text-emerald",
    warning: "text-warning",
    busy:    "text-primary",
    idle:    "text-muted-foreground",
  };

  const statusBg: Record<LiveMetric["status"], string> = {
    healthy: "bg-emerald/10",
    warning: "bg-warning/10",
    busy:    "bg-primary/10",
    idle:    "bg-white/5",
  };

  const jobStatusIcon = (s: Job["status"]) => {
    if (s === "running")  return <Loader2 className="h-3 w-3 animate-spin text-primary" />;
    if (s === "queued")   return <Clock className="h-3 w-3 text-muted-foreground" />;
    if (s === "complete") return <CheckCircle2 className="h-3 w-3 text-emerald" />;
    return <AlertTriangle className="h-3 w-3 text-destructive" />;
  };

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-[140] bg-black/30 backdrop-blur-[2px]" onClick={onClose} />
      )}
      <div
        className={`fixed right-0 top-0 z-[150] h-full w-full max-w-sm flex flex-col bg-[oklch(0.15_0.025_260)] border-l border-white/5 shadow-2xl transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald/10">
              <Activity className="h-3.5 w-3.5 text-emerald" />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-emerald shadow-[0_0_6px] shadow-emerald" />
            </div>
            <div>
              <div className="font-display text-sm font-semibold">Live Activity</div>
              <div className="text-[11px] text-muted-foreground">Real-time telemetry</div>
            </div>
          </div>
          <button onClick={onClose} className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Live Metrics */}
          <div className="border-b border-white/5 p-4">
            <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">
              Live Metrics
            </div>
            <div className="grid grid-cols-2 gap-2">
              {metrics.map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.id} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                    <div className="flex items-center justify-between gap-1">
                      <div className={`grid h-6 w-6 place-items-center rounded-md ${statusBg[m.status]}`}>
                        <Icon className={`h-3 w-3 ${statusColor[m.status]}`} />
                      </div>
                      <div className={`h-1.5 w-1.5 rounded-full ${
                        m.status === "healthy" ? "bg-emerald animate-pulse" :
                        m.status === "warning" ? "bg-warning animate-pulse" :
                        m.status === "busy" ? "bg-primary animate-pulse" : "bg-muted-foreground"
                      }`} />
                    </div>
                    <div className="mt-2 font-display text-base font-bold leading-none">
                      {m.value}
                    </div>
                    <div className="mt-0.5 text-[10px] text-muted-foreground truncate">{m.label}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Jobs Queue */}
          <div className="p-4">
            <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">
              Jobs Queue
            </div>
            <div className="space-y-2">
              {jobs.map((job) => (
                <div key={job.id} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                  <div className="flex items-start gap-2">
                    <div className="mt-0.5 shrink-0">{jobStatusIcon(job.status)}</div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-medium leading-tight truncate">{job.name}</div>
                      <div className="mt-1 flex items-center justify-between gap-2">
                        <span className={`text-[10px] font-semibold uppercase tracking-wider ${
                          job.status === "running"  ? "text-primary" :
                          job.status === "queued"   ? "text-muted-foreground" :
                          job.status === "complete" ? "text-emerald" : "text-destructive"
                        }`}>
                          {job.status}
                        </span>
                        <span className="text-[10px] font-mono text-muted-foreground">{job.elapsed}</span>
                      </div>
                      {job.status === "running" && job.progress !== undefined && (
                        <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/5">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-primary to-emerald transition-all duration-1000"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-white/5 px-4 py-3">
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald" />
            </span>
            <span>Streaming live · updated every 2s</span>
          </div>
        </div>
      </div>
    </>
  );
}
