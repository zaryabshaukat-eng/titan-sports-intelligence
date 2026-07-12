import type { ReactNode } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

export function GlassCard({
  children, className = "",
}: { children: ReactNode; className?: string }) {
  return <div className={`glass rounded-xl ${className}`}>{children}</div>;
}

export function StatCard({
  label, value, delta, icon: Icon, accent = "primary", sub,
}: {
  label: string;
  value: string | number;
  delta?: { value: string; positive?: boolean };
  icon?: React.ComponentType<{ className?: string }>;
  accent?: "primary" | "emerald" | "warning" | "destructive";
  sub?: string;
}) {
  const accentMap = {
    primary: "text-primary from-primary/20",
    emerald: "text-emerald from-emerald/20",
    warning: "text-warning from-warning/20",
    destructive: "text-destructive from-destructive/20",
  } as const;
  return (
    <div className="glass group relative overflow-hidden rounded-xl p-5 transition-all hover:border-white/15">
      <div className={`absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br ${accentMap[accent]} to-transparent opacity-40 blur-2xl transition-opacity group-hover:opacity-60`} />
      <div className="relative flex items-start justify-between">
        <div className="min-w-0">
          <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
          <div className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">{value}</div>
          {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
        </div>
        {Icon && (
          <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 ${accentMap[accent].split(" ")[0]}`}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      {delta && (
        <div className={`mt-3 inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium ${
          delta.positive ? "bg-emerald/10 text-emerald" : "bg-destructive/10 text-destructive"
        }`}>
          {delta.positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          {delta.value}
        </div>
      )}
    </div>
  );
}

export function StatusPill({
  status, label,
}: { status: "online" | "training" | "idle" | "offline" | "beta"; label?: string }) {
  const PILL_MAP: Record<string, { c: string; dot: string; t: string }> = {
    online:   { c: "text-emerald bg-emerald/10 border-emerald/20", dot: "bg-emerald", t: label ?? "Online" },
    training: { c: "text-primary bg-primary/10 border-primary/20", dot: "bg-primary", t: label ?? "Training" },
    idle:     { c: "text-muted-foreground bg-white/5 border-white/10", dot: "bg-muted-foreground", t: label ?? "Idle" },
    offline:  { c: "text-destructive bg-destructive/10 border-destructive/20", dot: "bg-destructive", t: label ?? "Offline" },
    beta:     { c: "text-warning bg-warning/10 border-warning/20", dot: "bg-warning", t: label ?? "Beta" },
  };
  const map = PILL_MAP[status] ?? { c: "text-muted-foreground bg-white/5 border-white/10", dot: "bg-muted-foreground", t: label ?? status };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${map.c}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${map.dot}`} />
      {map.t}
    </span>
  );
}

export function SectionTitle({
  title, description, action,
}: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div className="min-w-0">
        <h2 className="font-display text-base font-semibold tracking-tight">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}
