import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatusPill } from "../components/titan/primitives";

export const Route = createFileRoute("/live-odds")({ component: LiveOddsPage });

const rows = [
  { match: "Bayern vs Dortmund", min: "62'", home: 1.82, draw: 3.70, away: 4.20, mv: "-0.04" },
  { match: "Tottenham vs Chelsea", min: "34'", home: 2.15, draw: 3.30, away: 3.10, mv: "+0.02" },
  { match: "Ajax vs PSV", min: "78'", home: 1.55, draw: 4.20, away: 5.60, mv: "-0.08" },
  { match: "Napoli vs Milan", min: "12'", home: 2.05, draw: 3.40, away: 3.55, mv: "+0.01" },
  { match: "Porto vs Benfica", min: "44'", home: 2.90, draw: 3.10, away: 2.45, mv: "-0.03" },
];

function LiveOddsPage() {
  return (
    <>
      <PageHeader eyebrow="Order Book" title="Live Odds" description="Real-time cross-bookmaker price feed." actions={<StatusPill status="online" label="Streaming" />} />
      <GlassCard className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Match</th>
              <th className="px-4 py-3 font-medium">Clock</th>
              <th className="px-4 py-3 font-medium text-right">Home</th>
              <th className="px-4 py-3 font-medium text-right">Draw</th>
              <th className="px-4 py-3 font-medium text-right">Away</th>
              <th className="px-4 py-3 font-medium text-right">Movement</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((r) => (
              <tr key={r.match} className="hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium">{r.match}</td>
                <td className="px-4 py-3 font-mono text-emerald">{r.min}</td>
                <td className="px-4 py-3 text-right font-mono">{r.home.toFixed(2)}</td>
                <td className="px-4 py-3 text-right font-mono">{r.draw.toFixed(2)}</td>
                <td className="px-4 py-3 text-right font-mono">{r.away.toFixed(2)}</td>
                <td className={`px-4 py-3 text-right font-mono ${r.mv.startsWith("+") ? "text-emerald" : "text-destructive"}`}>{r.mv}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
    </>
  );
}
