import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard } from "../components/titan/primitives";
import { useRowNav } from "../hooks/useRowNav";

export const Route = createFileRoute("/arbitrage-center")({ component: Arb });

const arbs = [
  { match: "Napoli vs Milan", legs: 3, roi: 2.4, books: "Pinnacle · Bet365 · Betfair", ttl: "3m" },
  { match: "Ajax vs PSV", legs: 2, roi: 1.7, books: "Pinnacle · Betfair", ttl: "8m" },
  { match: "Porto vs Benfica", legs: 3, roi: 4.8, books: "Bet365 · Betway · Pinnacle", ttl: "1m" },
  { match: "Liverpool vs Leverkusen", legs: 2, roi: 1.2, books: "William Hill · Pinnacle", ttl: "12m" },
];

const LEG_FILTERS = [
  { label: "All legs", value: 0 },
  { label: "2-way", value: 2 },
  { label: "3-way", value: 3 },
] as const;

function Arb() {
  const [query, setQuery] = useState("");
  const [legs, setLegs] = useState<number>(0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return arbs.filter(
      (a) =>
        (legs === 0 || a.legs === legs) &&
        (!q || a.match.toLowerCase().includes(q) || a.books.toLowerCase().includes(q))
    );
  }, [query, legs]);

  const { focused, setFocused, setRowRef, onKeyDown } = useRowNav(filtered);

  return (
    <PlaceholderPage eyebrow="Risk-Free" title="Arbitrage Center" description="Cross-book mispricings surfaced in real time.">
      <GlassCard className="mb-4 flex flex-wrap items-center gap-3 p-3">
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by match or bookmaker…"
            aria-label="Filter arbitrage opportunities"
            className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        {LEG_FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => setLegs(f.value)}
            aria-pressed={legs === f.value}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              legs === f.value
                ? "border-emerald/40 bg-emerald/10 text-emerald"
                : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </GlassCard>

      <div
        role="grid"
        aria-rowcount={filtered.length}
        onKeyDown={onKeyDown}
        className="grid gap-3 md:grid-cols-2"
      >
        {filtered.length === 0 ? (
          <GlassCard className="col-span-full p-8 text-center text-sm text-muted-foreground">
            No arbitrage opportunities match your filters.
          </GlassCard>
        ) : (
          filtered.map((a, i) => (
            <div
              key={a.match}
              ref={setRowRef(i)}
              tabIndex={focused === i ? 0 : -1}
              role="row"
              aria-selected={focused === i}
              onFocus={() => setFocused(i)}
              className={`glass rounded-xl p-5 outline-none transition-all focus:ring-2 focus:ring-primary/40 ${focused === i ? "ring-1 ring-primary/30" : ""}`}
            >
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
            </div>
          ))
        )}
      </div>
      <div className="mt-3 text-[10px] text-muted-foreground">
        {filtered.length} of {arbs.length} opportunities · use ↑↓ to navigate cards, Enter to open
      </div>
    </PlaceholderPage>
  );
}
