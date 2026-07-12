import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard } from "../components/titan/primitives";

export const Route = createFileRoute("/leagues")({ component: LeaguesPage });

const leagues = [
  { name: "Premier League", country: "England", matches: 20, teams: 20, coverage: 100 },
  { name: "La Liga", country: "Spain", matches: 18, teams: 20, coverage: 100 },
  { name: "Serie A", country: "Italy", matches: 16, teams: 20, coverage: 100 },
  { name: "Bundesliga", country: "Germany", matches: 14, teams: 18, coverage: 100 },
  { name: "Ligue 1", country: "France", matches: 12, teams: 18, coverage: 98 },
  { name: "Champions League", country: "UEFA", matches: 32, teams: 32, coverage: 100 },
  { name: "Europa League", country: "UEFA", matches: 24, teams: 32, coverage: 100 },
  { name: "Eredivisie", country: "Netherlands", matches: 10, teams: 18, coverage: 96 },
  { name: "Primeira Liga", country: "Portugal", matches: 10, teams: 18, coverage: 94 },
  { name: "MLS", country: "USA", matches: 14, teams: 29, coverage: 92 },
  { name: "Brasileirão", country: "Brazil", matches: 16, teams: 20, coverage: 90 },
  { name: "J1 League", country: "Japan", matches: 8, teams: 18, coverage: 88 },
];

function LeaguesPage() {
  return (
    <>
      <PageHeader eyebrow="Competitions" title="Leagues" description="42 competitions monitored across 6 continents." />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {leagues.map((l) => (
          <GlassCard key={l.name} className="p-4 transition-all hover:border-white/15">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{l.country}</div>
            <div className="mt-1 font-display font-semibold">{l.name}</div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div><div className="text-muted-foreground">Live</div><div className="font-mono">{l.matches}</div></div>
              <div><div className="text-muted-foreground">Teams</div><div className="font-mono">{l.teams}</div></div>
              <div><div className="text-muted-foreground">Coverage</div><div className="font-mono text-emerald">{l.coverage}%</div></div>
            </div>
          </GlassCard>
        ))}
      </div>
    </>
  );
}
