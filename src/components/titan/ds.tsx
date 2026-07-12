/**
 * TITAN Design System — reusable enterprise primitives
 *
 * Exports:
 *   Badge, StatusChip, ProgressBar, MiniProgress
 *   Skeleton, SkeletonCard, SkeletonTable, SkeletonText
 *   EmptyState
 *   Dialog, Drawer
 *   MetricCard, MetricGrid
 *   Panel, PanelHeader
 *   ChartTooltip
 */

import { type ReactNode, useEffect } from "react";
import { X, AlertTriangle, Info, CheckCircle2, AlertOctagon } from "lucide-react";

/* ════════════════════════════════════════════════
   BADGE
   ════════════════════════════════════════════════ */
export type BadgeVariant = "default" | "primary" | "emerald" | "warning" | "destructive" | "outline" | "muted";

const BADGE_STYLES: Record<BadgeVariant, string> = {
  default:     "border-white/10 bg-white/[0.06] text-foreground",
  primary:     "border-primary/20 bg-primary/10 text-primary",
  emerald:     "border-emerald/20 bg-emerald/10 text-emerald",
  warning:     "border-warning/20 bg-warning/10 text-warning",
  destructive: "border-destructive/20 bg-destructive/10 text-destructive",
  outline:     "border-white/20 bg-transparent text-muted-foreground",
  muted:       "border-transparent bg-white/5 text-muted-foreground",
};

export function Badge({
  children, variant = "default", size = "md", dot, className = "",
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md" | "lg";
  dot?: boolean;
  className?: string;
}) {
  const sizeClass = size === "sm" ? "px-1.5 py-0 text-[9px]" : size === "lg" ? "px-3 py-1 text-xs" : "px-2 py-0.5 text-[10px]";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-semibold uppercase tracking-wider ${sizeClass} ${BADGE_STYLES[variant]} ${className}`}>
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${
        variant === "primary" ? "bg-primary" : variant === "emerald" ? "bg-emerald" :
        variant === "warning" ? "bg-warning" : variant === "destructive" ? "bg-destructive" : "bg-current"
      }`} />}
      {children}
    </span>
  );
}

/* ════════════════════════════════════════════════
   STATUS CHIP
   ════════════════════════════════════════════════ */
export type ChipStatus = "online" | "offline" | "degraded" | "training" | "beta" | "pending" | "error";

const CHIP_MAP: Record<ChipStatus, { label: string; dot: string; text: string; bg: string; border: string }> = {
  online:   { label: "Online",   dot: "bg-emerald animate-pulse",  text: "text-emerald",     bg: "bg-emerald/10",     border: "border-emerald/20" },
  offline:  { label: "Offline",  dot: "bg-muted-foreground",       text: "text-muted-foreground", bg: "bg-white/5",   border: "border-white/10" },
  degraded: { label: "Degraded", dot: "bg-warning animate-pulse",  text: "text-warning",     bg: "bg-warning/10",     border: "border-warning/20" },
  training: { label: "Training", dot: "bg-primary",                text: "text-primary",     bg: "bg-primary/10",     border: "border-primary/20" },
  beta:     { label: "Beta",     dot: "bg-warning",                text: "text-warning",     bg: "bg-warning/10",     border: "border-warning/20" },
  pending:  { label: "Pending",  dot: "bg-muted-foreground",       text: "text-muted-foreground", bg: "bg-white/5",   border: "border-white/10" },
  error:    { label: "Error",    dot: "bg-destructive animate-pulse", text: "text-destructive", bg: "bg-destructive/10", border: "border-destructive/20" },
};

export function StatusChip({ status, label }: { status: ChipStatus; label?: string }) {
  const c = CHIP_MAP[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${c.text} ${c.bg} ${c.border}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {label ?? c.label}
    </span>
  );
}

/* ════════════════════════════════════════════════
   PROGRESS BAR
   ════════════════════════════════════════════════ */
export function ProgressBar({
  value, max = 100, label, showValue = true, variant = "primary", size = "md", className = "",
}: {
  value: number; max?: number;
  label?: string; showValue?: boolean;
  variant?: "primary" | "emerald" | "warning" | "destructive" | "gradient";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const pct = Math.min(100, (value / max) * 100);
  const barColor =
    variant === "emerald"     ? "bg-emerald" :
    variant === "warning"     ? "bg-warning" :
    variant === "destructive" ? "bg-destructive" :
    variant === "gradient"    ? "bg-gradient-to-r from-primary to-emerald" :
    "bg-primary";
  const sizeH = size === "sm" ? "h-1" : size === "lg" ? "h-3 rounded-md" : "h-1.5";

  return (
    <div className={`space-y-1 ${className}`}>
      {(label || showValue) && (
        <div className="flex items-center justify-between text-xs">
          {label && <span className="text-muted-foreground">{label}</span>}
          {showValue && <span className="font-mono text-xs">{value}{max === 100 ? "%" : `/${max}`}</span>}
        </div>
      )}
      <div className={`w-full overflow-hidden rounded-full bg-white/5 ${sizeH}`}>
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function MiniProgress({ value, max = 100, color = "bg-primary" }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
      <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/* ════════════════════════════════════════════════
   SKELETON LOADERS
   ════════════════════════════════════════════════ */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded ${className}`} />;
}

export function SkeletonText({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-3 ${i === lines - 1 ? "w-3/5" : "w-full"}`} />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`glass rounded-xl p-5 space-y-4 ${className}`}>
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-2.5 w-1/2" />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="glass rounded-xl overflow-hidden">
      <div className="border-b border-white/5 bg-white/[0.02] px-4 py-3 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-2.5 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="border-b border-white/[0.04] px-4 py-3.5 flex gap-4 items-center">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className={`h-3 ${c === 0 ? "w-24" : "flex-1"}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════
   EMPTY STATE
   ════════════════════════════════════════════════ */
export function EmptyState({
  icon: Icon, title, description, action, className = "",
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center gap-4 py-16 text-center ${className}`}>
      {Icon && (
        <div className="grid h-14 w-14 place-items-center rounded-full bg-white/5">
          <Icon className="h-6 w-6 text-muted-foreground" />
        </div>
      )}
      <div>
        <div className="font-display text-base font-semibold">{title}</div>
        {description && <div className="mt-1 text-sm text-muted-foreground max-w-xs">{description}</div>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

/* ════════════════════════════════════════════════
   DIALOG
   ════════════════════════════════════════════════ */
export type DialogVariant = "default" | "info" | "success" | "warning" | "danger";

const DIALOG_ICONS: Partial<Record<DialogVariant, React.ComponentType<{ className?: string }>>> = {
  info:    Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger:  AlertOctagon,
};
const DIALOG_COLORS: Partial<Record<DialogVariant, string>> = {
  info:    "text-primary bg-primary/10",
  success: "text-emerald bg-emerald/10",
  warning: "text-warning bg-warning/10",
  danger:  "text-destructive bg-destructive/10",
};

export function Dialog({
  open, onClose, title, description, variant = "default", children, footer, maxWidth = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  variant?: DialogVariant;
  children?: ReactNode;
  footer?: ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl";
}) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);

  if (!open) return null;
  const maxW = { sm: "max-w-sm", md: "max-w-md", lg: "max-w-lg", xl: "max-w-xl" }[maxWidth];
  const IconComp = variant !== "default" ? DIALOG_ICONS[variant] : undefined;
  const iconColor = variant !== "default" ? DIALOG_COLORS[variant] : "";

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className={`relative w-full ${maxW} glass-strong rounded-2xl border border-white/10 shadow-2xl shadow-black/60 overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start gap-3 px-5 py-5 border-b border-white/5">
          {IconComp && (
            <div className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg ${iconColor}`}>
              <IconComp className="h-4.5 w-4.5" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="font-display text-base font-semibold">{title}</div>
            {description && <div className="mt-1 text-sm text-muted-foreground">{description}</div>}
          </div>
          <button onClick={onClose} className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground hover:bg-white/5 hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        {children && <div className="px-5 py-4">{children}</div>}

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2 border-t border-white/5 px-5 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════
   DRAWER
   ════════════════════════════════════════════════ */
export function Drawer({
  open, onClose, title, description, side = "right", width = "md", children, footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  side?: "left" | "right" | "bottom";
  width?: "sm" | "md" | "lg";
  children?: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);

  const widthClass = { sm: "max-w-xs", md: "max-w-sm", lg: "max-w-md" }[width];
  const translate = side === "right" ? (open ? "translate-x-0" : "translate-x-full") :
                    side === "left"  ? (open ? "translate-x-0" : "-translate-x-full") :
                    (open ? "translate-y-0" : "translate-y-full");
  const posClass = side === "right" ? "right-0 top-0 h-full" :
                   side === "left"  ? "left-0 top-0 h-full" : "bottom-0 left-0 w-full";

  return (
    <>
      {open && <div className="fixed inset-0 z-[200] bg-black/40 backdrop-blur-[2px]" onClick={onClose} />}
      <div className={`fixed ${posClass} z-[210] ${side !== "bottom" ? `${widthClass} w-full` : "max-h-[80vh]"} flex flex-col bg-[oklch(0.15_0.025_260)] border-l border-white/5 shadow-2xl transition-transform duration-300 ease-in-out ${translate}`}>
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
          <div>
            <div className="font-display text-sm font-semibold">{title}</div>
            {description && <div className="text-[11px] text-muted-foreground mt-0.5">{description}</div>}
          </div>
          <button onClick={onClose} className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && (
          <div className="flex items-center justify-end gap-2 border-t border-white/5 px-5 py-4">{footer}</div>
        )}
      </div>
    </>
  );
}

/* ════════════════════════════════════════════════
   METRIC CARD
   ════════════════════════════════════════════════ */
export function MetricCard({
  label, value, sub, trend, trendValue, icon: Icon, variant = "default", className = "",
}: {
  label: string; value: string | number; sub?: string;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: "default" | "primary" | "emerald" | "warning";
  className?: string;
}) {
  const variantColors = {
    default: "text-foreground from-white/5",
    primary: "text-primary from-primary/20",
    emerald: "text-emerald from-emerald/20",
    warning: "text-warning from-warning/20",
  };
  const trendColor = trend === "up" ? "text-emerald" : trend === "down" ? "text-destructive" : "text-muted-foreground";

  return (
    <div className={`glass group relative overflow-hidden rounded-xl p-5 transition-all hover:border-white/15 ${className}`}>
      <div className={`absolute -right-8 -top-8 h-28 w-28 rounded-full bg-gradient-to-br ${variantColors[variant]} to-transparent opacity-40 blur-2xl`} />
      <div className="relative">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
            <div className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">{value}</div>
            {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
          </div>
          {Icon && (
            <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 ${variantColors[variant].split(" ")[0]}`}>
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>
        {trend && trendValue && (
          <div className={`mt-3 inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium ${
            trend === "up" ? "bg-emerald/10 text-emerald" : trend === "down" ? "bg-destructive/10 text-destructive" : "bg-white/5 text-muted-foreground"
          }`}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </div>
        )}
      </div>
    </div>
  );
}

export function MetricGrid({ children, cols = 4, className = "" }: { children: ReactNode; cols?: 2|3|4|5; className?: string }) {
  const colClass = { 2: "sm:grid-cols-2", 3: "sm:grid-cols-3", 4: "sm:grid-cols-2 xl:grid-cols-4", 5: "sm:grid-cols-2 xl:grid-cols-5" }[cols];
  return <div className={`grid gap-3 ${colClass} ${className}`}>{children}</div>;
}

/* ════════════════════════════════════════════════
   PANEL + PANEL HEADER
   ════════════════════════════════════════════════ */
export function Panel({ children, className = "", padding = true }: { children: ReactNode; className?: string; padding?: boolean }) {
  return (
    <div className={`glass rounded-xl ${padding ? "p-5" : "overflow-hidden"} ${className}`}>
      {children}
    </div>
  );
}

export function PanelHeader({
  title, description, action, eyebrow,
}: { title: string; description?: string; action?: ReactNode; eyebrow?: string }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && (
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-primary">{eyebrow}</div>
        )}
        <h2 className="font-display text-base font-semibold tracking-tight">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/* ════════════════════════════════════════════════
   CHART TOOLTIP
   ════════════════════════════════════════════════ */
export function ChartTooltip({
  active, payload, label, formatter,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  formatter?: (v: number, name: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/10 bg-[oklch(0.18_0.025_260)] p-3 text-xs shadow-xl">
      {label && <div className="mb-2 font-medium text-muted-foreground">{label}</div>}
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground">{p.name}:</span>
          <span className="font-mono font-semibold">{formatter ? formatter(p.value, p.name) : p.value}</span>
        </div>
      ))}
    </div>
  );
}
