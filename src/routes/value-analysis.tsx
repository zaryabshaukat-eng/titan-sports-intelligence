import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard } from "../components/titan/primitives";

export const Route = createFileRoute("/value-analysis")({ component: VA });

const rows = [
  { match: "Man City vs Arsenal", market: "Over 2.5", fair: 1.72, best: 1.85, ev: 6.8 },
  { match: "Real Madrid vs Barça", market: "BTTS Yes", fair: 1.68, best: 1.79, ev: 5.2 },
  { match: "Bayern vs Dortmund", market: "AH -0.5", fair: 1.75, best: 1.86, ev: 4.9 },
  { match: "Inter vs Juventus", market: "Under 2.5", fair: 2.05, best: 2.16, ev: 4.1 },
  { match: "PSG vs Marseille", market: "Home ML", fair: 1.42, best: 1.49, ev: 3.8 },
];

function VA() {
  return (
    <PlaceholderPage eyebrow="Edge Discovery" title="Value Analysis" description="Fair-line modelling vs best available market price.">
      <GlassCard className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Match</th>
              <th className="px-4 py-3 font-medium">Market</th>
              <th className="px-4 py-3 font-medium text-right">Fair</th>
              <th className="px-4 py-3 font-medium text-right">Best</th>
              <th className="px-4 py-3 font-medium text-right">EV</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((r) => (
              <tr key={r.match} className="hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium">{r.match}</td>
                <td className="px-4 py-3 text-muted-foreground">{r.market}</td>
                <td className="px-4 py-3 text-right font-mono">{r.fair.toFixed(2)}</td>
                <td className="px-4 py-3 text-right font-mono">{r.best.toFixed(2)}</td>
                <td className="px-4 py-3 text-right font-mono text-emerald">+{r.ev.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
    </PlaceholderPage>
  );
}
