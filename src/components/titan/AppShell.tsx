import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";
import {
  LayoutDashboard, Trophy, Users, Radio, LineChart, Database, Brain,
  Target, Shuffle, History, BarChart3, Bell, FileText, Settings, UserCircle,
  Command, Search, Zap, ChevronRight,
} from "lucide-react";

const nav = [
  { group: "Overview", items: [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/matches", label: "Matches", icon: Trophy },
    { to: "/leagues", label: "Leagues", icon: Trophy },
    { to: "/teams", label: "Teams", icon: Users },
  ]},
  { group: "Markets", items: [
    { to: "/live-odds", label: "Live Odds", icon: Radio },
    { to: "/market-intelligence", label: "Market Intelligence", icon: LineChart },
    { to: "/historical-database", label: "Historical Database", icon: Database },
  ]},
  { group: "Intelligence", items: [
    { to: "/ai-intelligence", label: "AI Intelligence", icon: Brain },
    { to: "/value-analysis", label: "Value Analysis", icon: Target },
    { to: "/arbitrage-center", label: "Arbitrage Center", icon: Shuffle },
    { to: "/backtesting", label: "Backtesting", icon: History },
    { to: "/performance-analytics", label: "Performance", icon: BarChart3 },
  ]},
  { group: "Operations", items: [
    { to: "/alerts", label: "Alerts", icon: Bell },
    { to: "/reports", label: "Reports", icon: FileText },
    { to: "/settings", label: "Settings", icon: Settings },
    { to: "/account", label: "Account", icon: UserCircle },
  ]},
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="dark min-h-screen text-foreground">
      <div className="flex min-h-screen w-full">
        {/* Sidebar */}
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-white/5 bg-[oklch(0.13_0.02_260)]/80 backdrop-blur-xl lg:flex">
          <div className="flex items-center gap-2.5 px-5 py-5">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-primary to-emerald shadow-lg shadow-primary/30">
              <Zap className="h-5 w-5 text-[oklch(0.14_0.02_260)]" strokeWidth={2.5} />
            </div>
            <div className="min-w-0">
              <div className="font-display text-sm font-bold tracking-tight">TITAN</div>
              <div className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground">Sports Intelligence OS</div>
            </div>
          </div>

          <nav className="flex-1 space-y-6 overflow-y-auto px-3 pb-6">
            {nav.map((section) => (
              <div key={section.group}>
                <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">
                  {section.group}
                </div>
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const active = pathname === item.to;
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.to}
                        to={item.to}
                        className={`group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-all ${
                          active
                            ? "bg-primary/10 text-foreground shadow-[inset_0_0_0_1px_oklch(0.72_0.19_245/0.25)]"
                            : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                        }`}
                      >
                        <Icon className={`h-4 w-4 ${active ? "text-primary" : ""}`} />
                        <span className="flex-1 truncate">{item.label}</span>
                        {active && <ChevronRight className="h-3.5 w-3.5 text-primary" />}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>

          <div className="border-t border-white/5 p-3">
            <div className="glass rounded-lg p-3">
              <div className="mb-1 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-emerald">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-75"></span>
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald"></span>
                </span>
                System Nominal
              </div>
              <div className="text-xs text-muted-foreground">All engines online · v2.4.1</div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Topbar */}
          <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-white/5 bg-[oklch(0.13_0.02_260)]/70 px-4 backdrop-blur-xl md:px-6">
            <div className="flex items-center gap-2 lg:hidden">
              <div className="grid h-8 w-8 place-items-center rounded-md bg-gradient-to-br from-primary to-emerald">
                <Zap className="h-4 w-4 text-[oklch(0.14_0.02_260)]" strokeWidth={2.5} />
              </div>
              <span className="font-display text-sm font-bold">TITAN</span>
            </div>

            <div className="relative hidden max-w-md flex-1 md:block">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                placeholder="Search matches, teams, markets…"
                className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-9 pr-16 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
              <kbd className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                <Command className="h-3 w-3" />K
              </kbd>
            </div>

            <div className="ml-auto flex items-center gap-2">
              <div className="hidden items-center gap-1.5 rounded-md border border-emerald/20 bg-emerald/10 px-2.5 py-1 text-xs font-medium text-emerald md:flex">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald shadow-[0_0_8px] shadow-emerald"></span>
                LIVE FEED
              </div>
              <button className="relative grid h-9 w-9 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground">
                <Bell className="h-4 w-4" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_6px] shadow-primary" />
              </button>
              <div className="flex items-center gap-2 rounded-md border border-white/5 bg-white/5 px-2 py-1">
                <div className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-primary to-emerald text-[10px] font-bold text-[oklch(0.14_0.02_260)]">TN</div>
                <span className="hidden text-xs font-medium sm:inline">Titan Analyst</span>
              </div>
            </div>
          </header>

          <main className="min-w-0 flex-1 p-4 md:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  );
}

export function PageHeader({
  eyebrow, title, description, actions,
}: {
  eyebrow?: string; title: string; description?: string; actions?: ReactNode;
}) {
  return (
    <div className="mb-6 grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4 sm:flex sm:justify-between">
      <div className="min-w-0">
        {eyebrow && (
          <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
            {eyebrow}
          </div>
        )}
        <h1 className="truncate font-display text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
