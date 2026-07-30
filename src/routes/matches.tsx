import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard } from "../components/titan/primitives";
import { useMatches } from "@/hooks/useMatches";

export const Route = createFileRoute("/matches")({ component: MatchesPage });

function MatchesPage() {
  const { data: fixtures, isError, isPending } = useMatches();

  return (
    <>
      <PageHeader eyebrow="Fixtures" title="Matches" description="Canonical fixture catalog." />

      <GlassCard className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Fixture ID</th>
                <th className="px-4 py-3 font-medium">Home Team ID</th>
                <th className="px-4 py-3 font-medium">Away Team ID</th>
                <th className="px-4 py-3 font-medium">Scheduled Start</th>
                <th className="px-4 py-3 font-medium">Fixture Status ID</th>
                <th className="px-4 py-3 font-medium">Round</th>
                <th className="px-4 py-3 font-medium">Stage</th>
                <th className="px-4 py-3 font-medium">Venue ID</th>
                <th className="px-4 py-3 font-medium">Timezone ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isPending ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-muted-foreground" colSpan={9}>
                    Loading fixtures...
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-muted-foreground" colSpan={9}>
                    Fixtures are currently unavailable.
                  </td>
                </tr>
              ) : fixtures?.items.length ? (
                fixtures.items.map((fixture) => (
                  <tr key={fixture.id} className="hover:bg-white/[0.02]">
                    <td className="px-4 py-3 font-mono text-xs">{fixture.id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.home_team_id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.away_team_id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.scheduled_start_at}</td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.fixture_status_id}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {fixture.round_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {fixture.stage_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.venue_id ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs">{fixture.timezone_id ?? "—"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-6 text-sm text-muted-foreground" colSpan={9}>
                    No fixtures available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </>
  );
}
