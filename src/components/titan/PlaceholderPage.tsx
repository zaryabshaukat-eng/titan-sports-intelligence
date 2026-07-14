import type { ReactNode } from "react";
import { PageHeader } from "./AppShell";
import { GlassCard } from "./primitives";
import { Sparkles } from "lucide-react";

interface PlaceholderPageProps {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
  /**
   * Override the empty-state icon shown when no children are provided.
   * Defaults to Sparkles.
   */
  emptyIcon?: React.ComponentType<{ className?: string }>;
  /**
   * Override the empty-state headline shown when no children are provided.
   */
  emptyTitle?: string;
  /**
   * Override the empty-state body text shown when no children are provided.
   */
  emptyDescription?: string;
  /**
   * Optional call-to-action rendered under the empty-state body.
   */
  emptyAction?: ReactNode;
}

export function PlaceholderPage({
  eyebrow,
  title,
  description,
  children,
  emptyIcon: EmptyIcon = Sparkles,
  emptyTitle,
  emptyDescription,
  emptyAction,
}: PlaceholderPageProps) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      {children ?? (
        <GlassCard className="flex flex-col items-center justify-center gap-5 px-8 py-20 text-center">
          {/* Icon ring */}
          <div className="relative">
            <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-primary/25 to-emerald/15 ring-1 ring-white/10">
              <EmptyIcon className="h-7 w-7 text-primary" />
            </div>
            {/* Ambient glow */}
            <div className="absolute inset-0 rounded-2xl bg-primary/10 blur-xl" />
          </div>

          {/* Text */}
          <div className="max-w-sm space-y-1.5">
            <h3 className="font-display text-base font-semibold">
              {emptyTitle ?? `${title} — coming online`}
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {emptyDescription ??
                "This module is wired into TITAN's architecture and awaiting its live intelligence feed. Placeholder telemetry is active."}
            </p>
          </div>

          {/* Optional action */}
          {emptyAction && <div>{emptyAction}</div>}

          {/* Status pill */}
          <div className="flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            Module Indexed
          </div>
        </GlassCard>
      )}
    </>
  );
}
