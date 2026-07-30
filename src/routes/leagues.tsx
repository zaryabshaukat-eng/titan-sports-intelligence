import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard } from "../components/titan/primitives";
import { useLeagues } from "@/hooks/useLeagues";

export const Route = createFileRoute("/leagues")({ component: LeaguesPage });

function LeaguesPage() {
  const { data: leagues, isError, isPending } = useLeagues();

  return (
    <>
      <PageHeader eyebrow="Competitions" title="Leagues" description="Canonical league catalog." />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {isPending ? (
          <GlassCard className="p-4 sm:col-span-2 lg:col-span-3 xl:col-span-4">
            <div className="text-sm text-muted-foreground">Loading leagues...</div>
          </GlassCard>
        ) : isError ? (
          <GlassCard className="p-4 sm:col-span-2 lg:col-span-3 xl:col-span-4">
            <div className="text-sm text-muted-foreground">Leagues are currently unavailable.</div>
          </GlassCard>
        ) : leagues?.items.length ? (
          leagues.items.map((league) => (
            <GlassCard key={league.id} className="p-4 transition-all hover:border-white/15">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                {league.sport}
              </div>
              <div className="mt-1 font-display font-semibold">{league.name}</div>
              {league.short_name ? (
                <div className="mt-1 text-xs text-muted-foreground">{league.short_name}</div>
              ) : null}
              {league.country_id ? (
                <div className="mt-3 text-xs">
                  <div className="text-muted-foreground">Country ID</div>
                  <div className="mt-1 break-all font-mono text-[10px]">{league.country_id}</div>
                </div>
              ) : null}
            </GlassCard>
          ))
        ) : (
          <GlassCard className="p-4 sm:col-span-2 lg:col-span-3 xl:col-span-4">
            <div className="text-sm text-muted-foreground">No leagues available.</div>
          </GlassCard>
        )}
      </div>
    </>
  );
}
