import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatusPill } from "../components/titan/primitives";
import { Filter, Search } from "lucide-react";
import { useRowNav } from "../hooks/useRowNav";

export const Route = createFileRoute("/matches")({ component: MatchesPage });

type MatchStatus = "Scheduled" | "Live" | "Final";
type Filter = "All" | "Today" | "Live" | "Upcoming" | "Finals";

const matches: Array<{
  comp: string; home: string; away: string; ko: string;
  status: MatchStatus; market: string; ai: string; conf: number;
}> = [
  { comp: "Premier League", home: "Manchester City", away: "Arsenal", ko: "17:30", status: "Scheduled", market: "Open", ai: "Ready", conf: 87 },
  { comp: "La Liga", home: "Real Madrid", away: "Barcelona", ko: "20:00", status: "Scheduled", market: "Open", ai: "Ready", conf: 91 },
  { comp: "Serie A", home: "Inter", away: "Juventus", ko: "19:45", status: "Scheduled", market: "Open", ai: "Ready", conf: 78 },
  { comp: "Bundesliga", home: "Bayern", away: "Dortmund", ko: "LIVE 62'", status: "Live", market: "Live", ai: "Streaming", conf: 82 },
  { comp: "Ligue 1", home: "PSG", away: "Marseille", ko: "21:00", status: "Scheduled", market: "Open", ai: "Ready", conf: 74 },
  { comp: "Champions League", home: "Liverpool", away: "Bayer Leverkusen", ko: "Tomorrow 20:00", status: "Scheduled", market: "Pre-Open", ai: "Warming", conf: 69 },
  { comp: "Eredivisie", home: "Ajax", away: "PSV", ko: "16:45", status: "Scheduled", market: "Open", ai: "Ready", conf: 71 },
  { comp: "Premier League", home: "Tottenham", away: "Chelsea", ko: "LIVE 34'", status: "Live", market: "Live", ai: "Streaming", conf: 76 },
  { comp: "Serie A", home: "Napoli", away: "Milan", ko: "18:00", status: "Scheduled", market: "Open", ai: "Ready", conf: 83 },
  { comp: "La Liga", home: "Atlético", away: "Sevilla", ko: "Final", status: "Final", market: "Closed", ai: "Archived", conf: 80 },
];

const FILTERS: Filter[] = ["All", "Today", "Live", "Upcoming", "Finals"];

function MatchesPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("All");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return matches.filter((m) => {
      if (filter === "Live" && m.status !== "Live") return false;
      if (filter === "Finals" && m.status !== "Final") return false;
      if (filter === "Upcoming" && m.status !== "Scheduled") return false;
      if (filter === "Today" && m.ko.toLowerCase().includes("tomorrow")) return false;
      if (!q) return true;
      return (
        m.home.toLowerCase().includes(q) ||
        m.away.toLowerCase().includes(q) ||
        m.comp.toLowerCase().includes(q)
      );
    });
  }, [query, filter]);

  const { focused, setFocused, setRowRef, onKeyDown } = useRowNav(filtered);

  return (
    <>
      <PageHeader eyebrow="Fixtures" title="Matches" description="Global fixture surface across all monitored competitions." />

      <GlassCard className="mb-4 flex flex-wrap items-center gap-3 p-3">
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter fixtures by team or competition…"
            aria-label="Filter fixtures"
            className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        {FILTERS.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            aria-pressed={filter === t}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === t
                ? "border-primary/40 bg-primary/10 text-primary"
                : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
        <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground">
          <Filter className="h-3.5 w-3.5" /> Filters
        </button>
      </GlassCard>

      <GlassCard className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="grid" aria-rowcount={filtered.length}>
            <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Competition</th>
                <th className="px-4 py-3 font-medium">Teams</th>
                <th className="px-4 py-3 font-medium">Kickoff</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Market</th>
                <th className="px-4 py-3 font-medium">AI</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5" onKeyDown={onKeyDown}>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-sm text-muted-foreground">
                    No matches for “{query}”.
                  </td>
                </tr>
              ) : (
                filtered.map((m, i) => (
                  <tr
                    key={`${m.home}-${m.away}`}
                    ref={setRowRef(i)}
                    tabIndex={focused === i ? 0 : -1}
                    role="row"
                    aria-selected={focused === i}
                    onFocus={() => setFocused(i)}
                    className={`cursor-pointer outline-none transition-colors focus:bg-primary/10 focus:ring-1 focus:ring-inset focus:ring-primary/30 ${focused === i ? "bg-white/[0.03]" : "hover:bg-white/[0.02]"}`}
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">{m.comp}</td>
                    <td className="px-4 py-3 font-medium">{m.home} <span className="text-muted-foreground">vs</span> {m.away}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs">
                      {m.status === "Live" ? <span className="text-emerald">{m.ko}</span> : m.ko}
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={m.status === "Live" ? "online" : m.status === "Final" ? "idle" : "training"} label={m.status} />
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{m.market}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{m.ai}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1 w-20 overflow-hidden rounded-full bg-white/5">
                          <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${m.conf}%` }} />
                        </div>
                        <span className="font-mono text-xs">{m.conf}</span>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      <button className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-medium text-foreground hover:border-primary/40 hover:text-primary">Open</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="border-t border-white/5 px-4 py-2 text-[10px] text-muted-foreground">
          {filtered.length} of {matches.length} fixtures · use ↑↓ to navigate, Enter to open
        </div>
      </GlassCard>
    </>
  );
}
