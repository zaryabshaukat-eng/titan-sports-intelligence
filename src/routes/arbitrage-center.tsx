import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard } from "../components/titan/primitives";

export const Route = createFileRoute("/arbitrage-center")({ component: Arb });

const arbs = [
  { match: "Napoli vs Milan", legs: 3, roi: 2.4, books: "Pinnacle · Bet365 · Betfair", ttl: "3m" },
  { match: "Ajax vs PSV", legs: 2, roi: 1.7, books: "Pinnacle · Betfair", ttl: "8m" },
  { match: "Porto vs Benfica", legs: 3, roi: 4.8, books: "Bet365 · Betway · Pinnacle", ttl: "1m" },
  { match: "Liverpool vs Leverkusen", legs: 2, roi: 1.2, books: "William Hill · Pinnacle", ttl: "12m" },
];

function Arb() {
  return (
    <PlaceholderPage eyebrow="Risk-Free" title="Arbitrage Center" description="Cross-book mispricings surfaced in real time.">
      <div className="grid gap-3 md:grid-cols-2">
        {arbs.map((a) => (
          <GlassCard key={a.match} className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{a.legs}-way · TTL {a.ttl}</div>
                <div className="mt-1 font-display font-semibold">{a.match}</div>
                <div className="mt-1 text-xs text-muted-foreground">{a.books}</div>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">ROI</div>
                <div className="font-display text-2xl font-bold text-emerald">+{a.roi.toFixed(1)}%</div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </PlaceholderPage>
  );
}
