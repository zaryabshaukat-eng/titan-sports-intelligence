import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Search, X, Trophy, Users, FileText, FlaskConical, Bell, Settings, Brain, Command } from "lucide-react";

/* ─── Search data ─── */
type SearchResult = {
  id: string;
  label: string;
  sub?: string;
  href: string;
  group: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
};

const ALL_RESULTS: SearchResult[] = [
  // Matches
  { id: "m1", label: "Man City vs Arsenal",    sub: "Premier League · Today 17:30 · EV +6.8%",    href: "/matches", group: "Matches",  icon: Trophy,     badge: "87" },
  { id: "m2", label: "Real Madrid vs Barcelona",sub: "La Liga · Today 20:00 · EV +5.2%",           href: "/matches", group: "Matches",  icon: Trophy,     badge: "91" },
  { id: "m3", label: "Bayern vs Dortmund",     sub: "Bundesliga · LIVE 62' · EV +4.1%",            href: "/matches", group: "Matches",  icon: Trophy,     badge: "82" },
  { id: "m4", label: "Inter vs Juventus",      sub: "Serie A · Today 19:45 · EV +3.9%",            href: "/matches", group: "Matches",  icon: Trophy,     badge: "78" },
  // Teams
  { id: "t1", label: "Manchester City",        sub: "Premier League · Rating 94",                   href: "/teams",   group: "Teams",    icon: Users },
  { id: "t2", label: "Real Madrid",            sub: "La Liga · Rating 97",                          href: "/teams",   group: "Teams",    icon: Users },
  { id: "t3", label: "Arsenal",                sub: "Premier League · Rating 89",                   href: "/teams",   group: "Teams",    icon: Users },
  { id: "t4", label: "Bayern Munich",          sub: "Bundesliga · Rating 93",                       href: "/teams",   group: "Teams",    icon: Users },
  { id: "t5", label: "Barcelona",              sub: "La Liga · Rating 91",                          href: "/teams",   group: "Teams",    icon: Users },
  // Players (placeholder)
  { id: "p1", label: "Erling Haaland",         sub: "Man City · Forward",                           href: "/teams",   group: "Players",  icon: Users },
  { id: "p2", label: "Jude Bellingham",        sub: "Real Madrid · Midfielder",                     href: "/teams",   group: "Players",  icon: Users },
  // Leagues
  { id: "l1", label: "Premier League",         sub: "England · 20 teams · Matchweek 32",            href: "/leagues", group: "Leagues",  icon: Trophy },
  { id: "l2", label: "La Liga",                sub: "Spain · 20 teams · Matchweek 30",              href: "/leagues", group: "Leagues",  icon: Trophy },
  { id: "l3", label: "Champions League",       sub: "Europe · Quarter-finals",                      href: "/leagues", group: "Leagues",  icon: Trophy },
  // Reports
  { id: "r1", label: "UCL R16 Pattern Summary", sub: "Champions League · Yesterday",                href: "/reports", group: "Reports",  icon: FileText },
  { id: "r2", label: "Bundesliga Q3 Analysis",  sub: "Backtesting Report · 2 days ago",             href: "/reports", group: "Reports",  icon: FileText },
  { id: "r3", label: "Man City vs Arsenal — Pre-match", sub: "Research Note · 2m ago",             href: "/research",group: "Research", icon: FlaskConical },
  // Research
  { id: "rs1", label: "Man City vs Arsenal — Research", sub: "Research Workspace · Active",        href: "/research",group: "Research", icon: FlaskConical },
  { id: "rs2", label: "Bayern vs Dortmund — Live Notes", sub: "Research Workspace · Live",         href: "/research",group: "Research", icon: FlaskConical },
  // Alerts
  { id: "a1", label: "EV ≥ 5% alert — Man City Over 2.5", sub: "Alert · 14m ago",                href: "/alerts",  group: "Alerts",   icon: Bell,       badge: "!" },
  { id: "a2", label: "Arbitrage: Inter vs Juventus",       sub: "Alert · 2.4% ROI · 8m remaining", href: "/alerts",  group: "Alerts",   icon: Bell,       badge: "!" },
  // Settings
  { id: "s1", label: "Settings",        sub: "Preferences, API keys, notifications",                href: "/settings",group: "Settings", icon: Settings },
  { id: "s2", label: "Account",         sub: "Profile, billing, team management",                   href: "/account", group: "Settings", icon: Settings },
  { id: "s3", label: "AI Engine Monitor", sub: "Engine status and performance telemetry",           href: "/ai-engines", group: "Settings", icon: Brain },
];

const GROUP_ORDER = ["Matches", "Teams", "Players", "Leagues", "Reports", "Research", "Alerts", "Settings"];

function score(result: SearchResult, q: string): number {
  const lq = q.toLowerCase();
  const ll = result.label.toLowerCase();
  const ls = (result.sub ?? "").toLowerCase();
  if (ll.startsWith(lq)) return 100;
  if (ll.includes(lq)) return 80;
  if (ls.includes(lq)) return 50;
  return 0;
}

interface UniversalSearchProps {
  onOpenCommandPalette: () => void;
}

export function UniversalSearch({ onOpenCommandPalette }: UniversalSearchProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  /* Filter + sort results */
  const results = useMemo<SearchResult[]>(() => {
    const q = query.trim();
    if (!q) return [];
    return ALL_RESULTS
      .map((r) => ({ r, s: score(r, q) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 14)
      .map((x) => x.r);
  }, [query]);

  /* Grouped view */
  const grouped = useMemo(() => {
    const map = new Map<string, SearchResult[]>();
    for (const r of results) {
      if (!map.has(r.group)) map.set(r.group, []);
      map.get(r.group)!.push(r);
    }
    return GROUP_ORDER.filter((g) => map.has(g)).map((g) => ({ group: g, items: map.get(g)! }));
  }, [results]);

  /* Flat list for keyboard nav */
  const flatList = useMemo(() => results, [results]);

  const close = useCallback(() => { setOpen(false); setActiveIdx(-1); }, []);

  const navigate_to = useCallback((href: string) => {
    close();
    setQuery("");
    navigate({ to: href as any });
  }, [close, navigate]);

  /* Click outside */
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) close();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, close]);

  /* Keyboard: ↑↓ Enter Esc */
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, flatList.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIdx >= 0 && flatList[activeIdx]) {
      e.preventDefault();
      navigate_to(flatList[activeIdx].href);
    } else if (e.key === "Escape") {
      e.preventDefault();
      close();
    }
  };

  const showDropdown = open && query.trim().length > 0;

  return (
    <div ref={containerRef} className="relative hidden max-w-md flex-1 md:block">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" aria-hidden="true" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); setActiveIdx(-1); }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search matches, teams, markets…"
          aria-label="Universal search"
          aria-autocomplete="list"
          aria-expanded={showDropdown}
          aria-haspopup="listbox"
          role="combobox"
          className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-10 pr-20 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/30 focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {query && (
            <button onClick={() => { setQuery(""); inputRef.current?.focus(); }} aria-label="Clear search"
              className="grid h-5 w-5 place-items-center rounded text-muted-foreground hover:text-foreground transition-colors">
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          )}
          <button onClick={onOpenCommandPalette} aria-label="Open command palette (Ctrl+K)"
            className="hidden sm:flex items-center gap-0.5 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground transition-colors">
            <Command className="h-2.5 w-2.5" aria-hidden="true" />K
          </button>
        </div>
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div
          role="listbox"
          aria-label="Search results"
          className="absolute top-full left-0 right-0 mt-1.5 max-h-[440px] overflow-y-auto rounded-xl border border-white/10 bg-[oklch(0.16_0.02_260)] shadow-2xl animate-fade-in z-50"
        >
          {grouped.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <Search className="h-5 w-5 text-muted-foreground/40" aria-hidden="true" />
              <p className="text-xs text-muted-foreground">No results for <strong>"{query}"</strong></p>
            </div>
          ) : (
            <div className="p-1.5">
              {grouped.map(({ group, items }) => {
                return (
                  <div key={group} className="mb-1">
                    <div className="px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/60">{group}</div>
                    {items.map((item) => {
                      const globalIdx = flatList.indexOf(item);
                      const isActive = globalIdx === activeIdx;
                      const Icon = item.icon;
                      return (
                        <button
                          key={item.id}
                          role="option"
                          aria-selected={isActive}
                          onMouseEnter={() => setActiveIdx(globalIdx)}
                          onClick={() => navigate_to(item.href)}
                          className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors btn-press ${isActive ? "bg-primary/10 text-foreground" : "text-muted-foreground hover:bg-white/[0.04] hover:text-foreground"}`}
                        >
                          <Icon className={`h-3.5 w-3.5 shrink-0 ${isActive ? "text-primary" : ""}`} aria-hidden="true" />
                          <div className="min-w-0 flex-1">
                            <div className="text-xs font-medium leading-tight truncate">{item.label}</div>
                            {item.sub && <div className="text-[10px] text-muted-foreground/70 truncate">{item.sub}</div>}
                          </div>
                          {item.badge && (
                            <span className={`shrink-0 rounded-md border px-1.5 py-0.5 font-mono text-[9px] font-bold ${item.badge === "!" ? "border-amber-400/30 bg-amber-400/10 text-amber-400" : "border-primary/30 bg-primary/10 text-primary"}`}>
                              {item.badge}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                );
              })}
              <div className="border-t border-white/5 px-2 pt-1.5 pb-1 flex items-center justify-between">
                <span className="text-[9px] text-muted-foreground/50">{results.length} result{results.length !== 1 ? "s" : ""}</span>
                <span className="text-[9px] text-muted-foreground/50">↑↓ navigate · Enter select · Esc close</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
