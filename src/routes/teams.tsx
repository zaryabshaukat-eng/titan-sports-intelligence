import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard } from "../components/titan/primitives";

export const Route = createFileRoute("/teams")({ component: TeamsPage });

const teams = [
  { name: "Manchester City", league: "Premier League", form: "WWDWW", elo: 2041, xg: 2.31 },
  { name: "Real Madrid", league: "La Liga", form: "WWWDW", elo: 2038, xg: 2.24 },
  { name: "Bayern Munich", league: "Bundesliga", form: "WLWWW", elo: 1998, xg: 2.19 },
  { name: "Arsenal", league: "Premier League", form: "WWWWL", elo: 1974, xg: 2.03 },
  { name: "Inter", league: "Serie A", form: "WDWWW", elo: 1961, xg: 1.94 },
  { name: "PSG", league: "Ligue 1", form: "WWWWW", elo: 1958, xg: 2.11 },
  { name: "Liverpool", league: "Premier League", form: "DWWLW", elo: 1949, xg: 1.98 },
  { name: "Barcelona", league: "La Liga", form: "WLWDW", elo: 1932, xg: 1.86 },
];

function TeamsPage() {
  return (
    <>
      <PageHeader eyebrow="Rosters" title="Teams" description="4,200+ teams profiled across monitored competitions." />
      <GlassCard className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Team</th>
              <th className="px-4 py-3 font-medium">League</th>
              <th className="px-4 py-3 font-medium">Form</th>
              <th className="px-4 py-3 font-medium">ELO</th>
              <th className="px-4 py-3 font-medium">xG (avg)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {teams.map((t) => (
              <tr key={t.name} className="hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium">{t.name}</td>
                <td className="px-4 py-3 text-muted-foreground">{t.league}</td>
                <td className="px-4 py-3 font-mono">
                  {t.form.split("").map((c, i) => (
                    <span key={i} className={`mr-0.5 inline-block h-5 w-5 rounded text-center text-[10px] leading-5 ${c === "W" ? "bg-emerald/20 text-emerald" : c === "D" ? "bg-white/10 text-muted-foreground" : "bg-destructive/20 text-destructive"}`}>{c}</span>
                  ))}
                </td>
                <td className="px-4 py-3 font-mono">{t.elo}</td>
                <td className="px-4 py-3 font-mono">{t.xg}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
    </>
  );
}
