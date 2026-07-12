import type { ReactNode } from "react";
import { PageHeader } from "./AppShell";
import { GlassCard } from "./primitives";
import { Sparkles } from "lucide-react";

export function PlaceholderPage({
  eyebrow, title, description, children,
}: {
  eyebrow: string; title: string; description: string; children?: ReactNode;
}) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      {children ?? (
        <GlassCard className="grid place-items-center p-16 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-primary/30 to-emerald/20">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <h3 className="mt-4 font-display text-lg font-semibold">Module ready for intelligence integration</h3>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            This surface is wired into Titan's architecture and awaiting connection to its analytics engine.
            Placeholder telemetry active.
          </p>
        </GlassCard>
      )}
    </>
  );
}
