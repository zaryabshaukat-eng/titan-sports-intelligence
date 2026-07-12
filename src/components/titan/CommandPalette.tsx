import { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  LayoutDashboard, Trophy, Users, Radio, LineChart, Database, Brain,
  Target, Shuffle, History, BarChart3, Bell, FileText, Settings, UserCircle,
  Search, Zap, FlaskConical, MonitorCheck, X, ArrowRight, Command,
  BookOpen, Activity,
} from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  category: string;
  action: () => void;
  keywords?: string[];
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const navAction = useCallback((to: string) => () => {
    navigate({ to } as Parameters<typeof navigate>[0]);
    onClose();
  }, [navigate, onClose]);

  const commands: CommandItem[] = [
    // Navigate
    { id: "nav-dashboard", label: "Dashboard", description: "Intelligence overview", icon: LayoutDashboard, category: "Navigate", action: navAction("/"), keywords: ["home", "overview"] },
    { id: "nav-matches", label: "Matches", description: "Global fixture surface", icon: Trophy, category: "Navigate", action: navAction("/matches") },
    { id: "nav-leagues", label: "Leagues", description: "Competition monitor", icon: Trophy, category: "Navigate", action: navAction("/leagues") },
    { id: "nav-teams", label: "Teams", description: "Team intelligence", icon: Users, category: "Navigate", action: navAction("/teams") },
    { id: "nav-live-odds", label: "Live Odds", description: "Real-time price streams", icon: Radio, category: "Navigate", action: navAction("/live-odds") },
    { id: "nav-market-intelligence", label: "Market Intelligence", description: "Cross-book line movement", icon: LineChart, category: "Navigate", action: navAction("/market-intelligence") },
    { id: "nav-historical-database", label: "Historical Database", description: "30+ seasons of data", icon: Database, category: "Navigate", action: navAction("/historical-database") },
    { id: "nav-ai-intelligence", label: "AI Intelligence", description: "Nine-engine neural fabric", icon: Brain, category: "Navigate", action: navAction("/ai-intelligence") },
    { id: "nav-value-analysis", label: "Value Analysis", description: "EV & fair-line modelling", icon: Target, category: "Navigate", action: navAction("/value-analysis") },
    { id: "nav-arbitrage-center", label: "Arbitrage Center", description: "Cross-book opportunities", icon: Shuffle, category: "Navigate", action: navAction("/arbitrage-center") },
    { id: "nav-backtesting", label: "Backtesting", description: "Historical simulations", icon: History, category: "Navigate", action: navAction("/backtesting") },
    { id: "nav-performance-analytics", label: "Performance Analytics", description: "ROI, accuracy, calibration", icon: BarChart3, category: "Navigate", action: navAction("/performance-analytics") },
    { id: "nav-alerts", label: "Alerts", description: "Alert center", icon: Bell, category: "Navigate", action: navAction("/alerts") },
    { id: "nav-reports", label: "Reports", description: "Research reports", icon: FileText, category: "Navigate", action: navAction("/reports") },
    { id: "nav-research", label: "Research Workspace", description: "Three-column research environment", icon: FlaskConical, category: "Navigate", action: navAction("/research") },
    { id: "nav-system-status", label: "System Status", description: "Infrastructure health", icon: MonitorCheck, category: "Navigate", action: navAction("/system-status") },
    { id: "nav-settings", label: "Settings", description: "Platform configuration", icon: Settings, category: "Navigate", action: navAction("/settings") },
    { id: "nav-account", label: "Account", description: "User profile & preferences", icon: UserCircle, category: "Navigate", action: navAction("/account") },
    // Leagues (search items)
    { id: "search-pl", label: "Premier League", description: "English top flight", icon: Trophy, category: "Leagues", action: navAction("/leagues"), keywords: ["epl", "england"] },
    { id: "search-laliga", label: "La Liga", description: "Spanish top flight", icon: Trophy, category: "Leagues", action: navAction("/leagues"), keywords: ["spain", "primera"] },
    { id: "search-ucl", label: "Champions League", description: "UEFA competition", icon: Trophy, category: "Leagues", action: navAction("/leagues"), keywords: ["ucl", "europe"] },
    { id: "search-bundesliga", label: "Bundesliga", description: "German top flight", icon: Trophy, category: "Leagues", action: navAction("/leagues"), keywords: ["germany"] },
    // Teams
    { id: "team-mancity", label: "Manchester City", description: "Premier League", icon: Users, category: "Teams", action: navAction("/teams"), keywords: ["cityzens", "mancity"] },
    { id: "team-realmadrid", label: "Real Madrid", description: "La Liga", icon: Users, category: "Teams", action: navAction("/teams"), keywords: ["madrid", "los blancos"] },
    { id: "team-barcelona", label: "Barcelona", description: "La Liga", icon: Users, category: "Teams", action: navAction("/teams"), keywords: ["barca", "fcb"] },
    { id: "team-arsenal", label: "Arsenal", description: "Premier League", icon: Users, category: "Teams", action: navAction("/teams"), keywords: ["gunners"] },
    { id: "team-bayern", label: "Bayern Munich", description: "Bundesliga", icon: Users, category: "Teams", action: navAction("/teams"), keywords: ["bavaria", "fcb"] },
    // Actions
    { id: "action-refresh", label: "Refresh Data Feed", description: "Sync all market sources", icon: Activity, category: "Actions", action: onClose, keywords: ["sync", "update"] },
    { id: "action-ai", label: "Open AI Intelligence", description: "View all engine statuses", icon: Brain, category: "Actions", action: navAction("/ai-intelligence") },
    { id: "action-docs", label: "Documentation", description: "Platform reference", icon: BookOpen, category: "Actions", action: onClose },
  ];

  const filtered = query.trim() === ""
    ? commands
    : commands.filter((c) => {
        const q = query.toLowerCase();
        return (
          c.label.toLowerCase().includes(q) ||
          c.description?.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q) ||
          c.keywords?.some((k) => k.includes(q))
        );
      });

  const categories = Array.from(new Set(filtered.map((c) => c.category)));

  useEffect(() => {
    setSelected(0);
  }, [query, open]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === "Escape") { onClose(); return; }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelected((s) => Math.min(s + 1, filtered.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelected((s) => Math.max(s - 1, 0));
      }
      if (e.key === "Enter") {
        e.preventDefault();
        filtered[selected]?.action();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, filtered, selected, onClose]);

  if (!open) return null;

  let globalIndex = 0;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-start justify-center pt-[15vh]"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full max-w-2xl mx-4 glass-strong rounded-2xl overflow-hidden shadow-2xl shadow-black/60 border border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5">
          <Search className="h-4 w-4 text-primary shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pages, teams, leagues, actions…"
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
            <kbd className="flex items-center gap-0.5 rounded border border-white/10 bg-white/5 px-1.5 py-0.5">
              <Command className="h-2.5 w-2.5" />K
            </kbd>
            <span>or</span>
            <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5">Esc</kbd>
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-white/5">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No results for <span className="font-mono text-foreground">"{query}"</span>
            </div>
          ) : (
            categories.map((cat) => {
              const items = filtered.filter((c) => c.category === cat);
              return (
                <div key={cat}>
                  <div className="px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/60">
                    {cat}
                  </div>
                  {items.map((item) => {
                    const idx = globalIndex++;
                    const isSelected = selected === idx;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={item.action}
                        onMouseEnter={() => setSelected(idx)}
                        className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          isSelected ? "bg-primary/10 text-foreground" : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${
                          isSelected ? "border-primary/40 bg-primary/10 text-primary" : "border-white/5 bg-white/[0.03] text-muted-foreground"
                        }`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className={`text-sm font-medium ${isSelected ? "text-foreground" : ""}`}>{item.label}</div>
                          {item.description && (
                            <div className="text-[11px] text-muted-foreground">{item.description}</div>
                          )}
                        </div>
                        {isSelected && <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/5 px-4 py-2 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1"><kbd className="rounded border border-white/10 bg-white/5 px-1 py-0.5">↑↓</kbd> Navigate</span>
            <span className="flex items-center gap-1"><kbd className="rounded border border-white/10 bg-white/5 px-1 py-0.5">↵</kbd> Select</span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3 text-primary" />
            <span>Titan Intelligence</span>
          </div>
        </div>
      </div>
    </div>
  );
}
