import type { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-react";
import {
  RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer,
} from "recharts";

/* ─────────────── ConfidenceGauge ─────────────── */
export function ConfidenceGauge({
  value, label = "Confidence", size = 140,
}: { value: number; label?: string; size?: number }) {
  const data = [{ value, fill: "oklch(0.72 0.19 245)" }];
  const color =
    value >= 80 ? "oklch(0.75 0.18 155)" :
    value >= 60 ? "oklch(0.72 0.19 245)" :
    value >= 40 ? "oklch(0.78 0.16 75)" : "oklch(0.65 0.24 25)";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size * 0.6 }}>
        {/* Background arc */}
        <svg viewBox="0 0 100 55" className="absolute inset-0 w-full h-full overflow-visible">
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none" stroke="oklch(1 0 0 / 0.06)" strokeWidth="8" strokeLinecap="round"
          />
          {/* Value arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(value / 100) * 125.7} 125.7`}
            style={{ transition: "stroke-dasharray 0.8s ease" }}
          />
          {/* Needle */}
          {(() => {
            const angle = -180 + (value / 100) * 180;
            const rad = (angle * Math.PI) / 180;
            const x2 = 50 + 32 * Math.cos(rad);
            const y2 = 50 + 32 * Math.sin(rad);
            return (
              <line x1="50" y1="50" x2={x2} y2={y2}
                stroke={color} strokeWidth="2" strokeLinecap="round"
                style={{ transition: "all 0.8s ease" }}
              />
            );
          })()}
          <circle cx="50" cy="50" r="3" fill={color} />
        </svg>
        {/* Center value */}
        <div className="absolute bottom-0 inset-x-0 text-center">
          <span className="font-display text-lg font-bold" style={{ color }}>{value}</span>
          <span className="text-[10px] text-muted-foreground">%</span>
        </div>
      </div>
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

/* ─────────────── ProbabilityRing ─────────────── */
export function ProbabilityRing({
  value, label, sublabel, size = 80,
}: { value: number; label?: string; sublabel?: string; size?: number }) {
  const color =
    value >= 75 ? "oklch(0.75 0.18 155)" :
    value >= 50 ? "oklch(0.72 0.19 245)" :
    value >= 25 ? "oklch(0.78 0.16 75)" : "oklch(0.65 0.24 25)";

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="72%"
            outerRadius="100%"
            data={[{ value, fill: color }]}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              background={{ fill: "oklch(1 0 0 / 0.05)" }}
              dataKey="value"
              cornerRadius={10}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-base font-bold leading-none" style={{ color }}>{value}%</span>
          {sublabel && <span className="text-[8px] uppercase tracking-wider text-muted-foreground mt-0.5">{sublabel}</span>}
        </div>
      </div>
      {label && <div className="text-[11px] text-muted-foreground text-center">{label}</div>}
    </div>
  );
}

/* ─────────────── RiskMeter ─────────────── */
export function RiskMeter({ value, label = "Risk Level" }: { value: number; label?: string }) {
  const level =
    value <= 25 ? { text: "Low", color: "bg-emerald", textColor: "text-emerald" } :
    value <= 50 ? { text: "Moderate", color: "bg-primary", textColor: "text-primary" } :
    value <= 75 ? { text: "High", color: "bg-warning", textColor: "text-warning" } :
    { text: "Critical", color: "bg-destructive", textColor: "text-destructive" };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={`font-semibold ${level.textColor}`}>{level.text}</span>
      </div>
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-white/5">
        {/* Gradient track */}
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
          style={{
            width: `${value}%`,
            background: value <= 25
              ? "oklch(0.75 0.18 155)"
              : value <= 50
              ? "oklch(0.72 0.19 245)"
              : value <= 75
              ? "linear-gradient(90deg, oklch(0.72 0.19 245), oklch(0.78 0.16 75))"
              : "linear-gradient(90deg, oklch(0.78 0.16 75), oklch(0.65 0.24 25))",
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>Low</span>
        <span className="font-mono">{value}%</span>
        <span>Critical</span>
      </div>
    </div>
  );
}

/* ─────────────── SignalStrength ─────────────── */
export function SignalStrength({ value, label }: { value: 0 | 1 | 2 | 3 | 4 | 5; label?: string }) {
  const bars = [1, 2, 3, 4, 5] as const;
  const color =
    value >= 4 ? "bg-emerald" :
    value >= 3 ? "bg-primary" :
    value >= 2 ? "bg-warning" : "bg-destructive";

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="flex items-end gap-0.5 h-6">
        {bars.map((b) => (
          <div
            key={b}
            className={`w-2 rounded-sm transition-colors ${b <= value ? color : "bg-white/10"}`}
            style={{ height: `${b * 20}%` }}
          />
        ))}
      </div>
      {label && <span className="text-[10px] text-muted-foreground">{label}</span>}
    </div>
  );
}

/* ─────────────── MarketStrength ─────────────── */
export function MarketStrength({ value, max = 10, label }: { value: number; max?: number; label?: string }) {
  const filled = Math.round((value / max) * 10);
  const strength =
    filled >= 8 ? "Strong" :
    filled >= 6 ? "Moderate" :
    filled >= 4 ? "Neutral" : "Weak";
  const color =
    filled >= 8 ? "bg-emerald" :
    filled >= 6 ? "bg-primary" :
    filled >= 4 ? "bg-warning" : "bg-destructive/60";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[11px]">
        {label && <span className="text-muted-foreground">{label}</span>}
        <span className="font-medium">{strength}</span>
      </div>
      <div className="flex gap-1">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className={`h-2 flex-1 rounded-sm transition-colors ${i < filled ? color : "bg-white/5"}`}
          />
        ))}
      </div>
    </div>
  );
}

/* ─────────────── HealthIndicator ─────────────── */
export function HealthIndicator({
  status, label, detail,
}: {
  status: "healthy" | "degraded" | "critical" | "offline" | "unknown";
  label: string;
  detail?: string;
}) {
  const cfg = {
    healthy:  { dot: "bg-emerald", ring: "shadow-[0_0_8px] shadow-emerald", text: "text-emerald",     label: "Healthy" },
    degraded: { dot: "bg-warning",  ring: "shadow-[0_0_8px] shadow-warning",  text: "text-warning",     label: "Degraded" },
    critical: { dot: "bg-destructive", ring: "shadow-[0_0_8px] shadow-destructive", text: "text-destructive", label: "Critical" },
    offline:  { dot: "bg-muted-foreground", ring: "", text: "text-muted-foreground", label: "Offline" },
    unknown:  { dot: "bg-white/20",  ring: "", text: "text-muted-foreground",  label: "Unknown" },
  }[status];

  return (
    <div className="flex items-center gap-2.5">
      <div className="relative flex h-2.5 w-2.5 shrink-0">
        {status === "healthy" && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-60" />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${cfg.dot} ${cfg.ring}`} />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium">{label}</div>
        {detail && <div className="text-[10px] text-muted-foreground">{detail}</div>}
      </div>
      <div className={`ml-auto text-[10px] font-semibold uppercase tracking-wider ${cfg.text}`}>
        {cfg.label}
      </div>
    </div>
  );
}

/* ─────────────── AccuracyWidget ─────────────── */
export function AccuracyWidget({
  value, delta, label, period,
}: { value: number; delta?: number; label?: string; period?: string }) {
  const isPositive = (delta ?? 0) >= 0;
  return (
    <div className="space-y-1">
      {label && <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>}
      <div className="flex items-end gap-2">
        <span className="font-display text-2xl font-bold">{value.toFixed(1)}%</span>
        {delta !== undefined && (
          <div className={`mb-0.5 flex items-center gap-0.5 text-xs font-medium ${isPositive ? "text-emerald" : "text-destructive"}`}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {Math.abs(delta).toFixed(1)}%
          </div>
        )}
      </div>
      {period && <div className="text-[10px] text-muted-foreground">{period}</div>}
    </div>
  );
}

/* ─────────────── TrendIndicator ─────────────── */
export function TrendIndicator({
  direction, value, label, magnitude,
}: {
  direction: "up" | "down" | "flat";
  value: string;
  label?: string;
  magnitude?: "strong" | "moderate" | "weak";
}) {
  const cfg = {
    up:   { icon: TrendingUp,  color: "text-emerald", bg: "bg-emerald/10" },
    down: { icon: TrendingDown, color: "text-destructive", bg: "bg-destructive/10" },
    flat: { icon: Minus,        color: "text-muted-foreground", bg: "bg-white/5" },
  }[direction];
  const Icon = cfg.icon;

  return (
    <div className="flex items-center gap-2">
      <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${cfg.bg} ${cfg.color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <div className={`text-sm font-semibold ${cfg.color}`}>{value}</div>
        {label && <div className="text-[10px] text-muted-foreground">{label}</div>}
      </div>
      {magnitude && (
        <div className={`ml-auto text-[10px] uppercase tracking-wider font-semibold ${cfg.color}`}>
          {magnitude}
        </div>
      )}
    </div>
  );
}

/* ─────────────── ConfidenceWidgetGrid ─────────────── */
export function ConfidenceWidgetGrid({ children }: { children: ReactNode }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {children}
    </div>
  );
}

export function WidgetCard({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <div className={`glass rounded-xl p-4 ${className}`}>
      <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
        {title}
      </div>
      {children}
    </div>
  );
}
