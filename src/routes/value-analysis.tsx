import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard } from "../components/titan/primitives";
import { useRowNav } from "../hooks/useRowNav";

export const Route = createFileRoute("/value-analysis")({ component: VA });

const rows = [
  { match: "Man City vs Arsenal", market: "Over 2.5", fair: 1.72, best: 1.85, ev: 6.8 },
  { match: "Real Madrid vs Barça", market: "BTTS Yes", fair: 1.68, best: 1.79, ev: 5.2 },
  { match: "Bayern vs Dortmund", market: "AH -0.5", fair: 1.75, best: 1.86, ev: 4.9 },
  { match: "Inter vs Juventus", market: "Under 2.5", fair: 2.05, best: 2.16, ev: 4.1 },
  { match: "PSG vs Marseille", market: "Home ML", fair: 1.42, best: 1.49, ev: 3.8 },
];

const EV_BUCKETS = [
  { label: "All", min: 0 },
  { label: "≥ 3%", min: 3 },
  { label: "≥ 5%", min: 5 },
] as const;

function VA() {
  const [query, setQuery] = useState("");
  const [minEv, setMinEv] = useState(0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter(
      (r) =>
        r.ev >= minEv &&
        (!q || r.match.toLowerCase().includes(q) || r.market.toLowerCase().includes(q))
    );
  }, [query, minEv]);

  const { focused, setFocused, setRowRef, onKeyDown } = useRowNav(filtered);

  return (
    <PlaceholderPage eyebrow="Edge Discovery" title="Value Analysis" description="Fair-line modelling vs best available market price.">
      <GlassCard className="mb-4 flex flex-wrap items-center gap-3 p-3">
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by match or market…"
            aria-label="Filter value plays"
            className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        {EV_BUCKETS.map((b) => (
          <button
            key={b.label}
            onClick={() => setMinEv(b.min)}
            aria-pressed={minEv === b.min}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              minEv === b.min
                ? "border-emerald/40 bg-emerald/10 text-emerald"
                : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"
            }`}
          >
            {b.label}
          </button>
        ))}
      </GlassCard>

      <GlassCard className="overflow-hidden">
        <table className="w-full text-sm" role="grid" aria-rowcount={filtered.length}>
          <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Match</th>
              <th className="px-4 py-3 font-medium">Market</th>
              <th className="px-4 py-3 font-medium text-right">Fair</th>
              <th className="px-4 py-3 font-medium text-right">Best</th>
              <th className="px-4 py-3 font-medium text-right">EV</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5" onKeyDown={onKeyDown}>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-sm text-muted-foreground">
                  No value plays match your filters.
                </td>
              </tr>
            ) : (
              filtered.map((r, i) => (
                <tr
                  key={`${r.match}-${r.market}`}
                  ref={setRowRef(i)}
                  tabIndex={focused === i ? 0 : -1}
                  role="row"
                  aria-selected={focused === i}
                  onFocus={() => setFocused(i)}
                  className={`cursor-pointer outline-none transition-colors focus:bg-primary/10 focus:ring-1 focus:ring-inset focus:ring-primary/30 ${focused === i ? "bg-white/[0.03]" : "hover:bg-white/[0.02]"}`}
                >
                  <td className="px-4 py-3 font-medium">{r.match}</td>
                  <td className="px-4 py-3 text-muted-foreground">{r.market}</td>
                  <td className="px-4 py-3 text-right font-mono">{r.fair.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-mono">{r.best.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-mono text-emerald">+{r.ev.toFixed(1)}%</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="border-t border-white/5 px-4 py-2 text-[10px] text-muted-foreground">
          {filtered.length} of {rows.length} plays · use ↑↓ to navigate rows
        </div>
      </GlassCard>
    </PlaceholderPage>
  );
}
