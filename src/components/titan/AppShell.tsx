import { Link, useRouterState } from "@tanstack/react-router";
import { type ReactNode, useEffect, useState, useCallback, useRef } from "react";
import {
  LayoutDashboard, Trophy, Users, Radio, LineChart, Database, Brain,
  Target, Shuffle, History, BarChart3, Bell, FileText, Settings, UserCircle,
  Command, Zap, ChevronRight, FlaskConical, MonitorCheck,
  Activity, Menu, X, Clock, Palette, PanelLeftClose, PanelLeftOpen, Keyboard, Check, Cpu,
} from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { NotificationCenter } from "./NotificationCenter";
import { LiveActivityCenter } from "./LiveActivityCenter";
import { KeyboardShortcutsModal, useKeyboardShortcuts } from "./KeyboardShortcuts";
import { useTheme, THEMES } from "./ThemeProvider";
import { UniversalSearch } from "./UniversalSearch";

const nav = [
  { group: "Overview", items: [
    { to: "/",                   label: "Dashboard",          icon: LayoutDashboard },
    { to: "/matches",            label: "Matches",            icon: Trophy },
    { to: "/leagues",            label: "Leagues",            icon: Trophy },
    { to: "/teams",              label: "Teams",              icon: Users },
  ]},
  { group: "Markets", items: [
    { to: "/live-odds",          label: "Live Odds",          icon: Radio },
    { to: "/market-intelligence",label: "Market Intelligence",icon: LineChart },
    { to: "/historical-database",label: "Historical Database",icon: Database },
  ]},
  { group: "Intelligence", items: [
    { to: "/ai-intelligence",    label: "AI Intelligence",    icon: Brain },
    { to: "/ai-engines",         label: "Engine Monitor",     icon: Cpu },
    { to: "/value-analysis",     label: "Value Analysis",     icon: Target },
    { to: "/arbitrage-center",   label: "Arbitrage Center",   icon: Shuffle },
    { to: "/backtesting",        label: "Backtesting",        icon: History },
    { to: "/performance-analytics", label: "Performance",    icon: BarChart3 },
  ]},
  { group: "Workspace", items: [
    { to: "/research",           label: "Research Workspace", icon: FlaskConical },
    { to: "/timeline",           label: "Timeline",           icon: Clock },
    { to: "/reports",            label: "Reports",            icon: FileText },
    { to: "/alerts",             label: "Alerts",             icon: Bell },
  ]},
  { group: "Platform", items: [
    { to: "/system-status",      label: "System Status",      icon: MonitorCheck },
    { to: "/design-system",      label: "Design System",      icon: Palette },
    { to: "/settings",           label: "Settings",           icon: Settings },
    { to: "/account",            label: "Account",            icon: UserCircle },
  ]},
];

const SIDEBAR_STORAGE_KEY = "titan_sidebar_collapsed";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  // Persistent sidebar state via localStorage
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(SIDEBAR_STORAGE_KEY) === "true";
  });

  const [cmdOpen,          setCmdOpen]          = useState(false);
  const [notifOpen,        setNotifOpen]        = useState(false);
  const [activityOpen,     setActivityOpen]     = useState(false);
  const [shortcutsOpen,    setShortcutsOpen]    = useState(false);
  const [mobileNavOpen,    setMobileNavOpen]    = useState(false);
  const [themePickerOpen,  setThemePickerOpen]  = useState(false);
  const [notifCount] = useState(4);
  const themePickerRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useTheme();

  // Persist sidebar collapse
  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((v) => {
      const next = !v;
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      return next;
    });
  }, []);

  // Wire up the global keyboard shortcut system
  const { gPressed } = useKeyboardShortcuts({
    onOpenCommandPalette: () => setCmdOpen(true),
    onToggleShortcuts: () => setShortcutsOpen((v) => !v),
  });

  // Close mobile nav on route change
  useEffect(() => { setMobileNavOpen(false); }, [pathname]);

  // Close theme picker on outside click
  useEffect(() => {
    if (!themePickerOpen) return;
    const handler = (e: MouseEvent) => {
      if (themePickerRef.current && !themePickerRef.current.contains(e.target as Node)) {
        setThemePickerOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [themePickerOpen]);

  const SidebarContent = ({ collapsed = false }: { collapsed?: boolean }) => (
    <>
      {/* Logo */}
      <div className={`flex items-center gap-2.5 px-4 py-5 ${collapsed ? "justify-center" : ""}`}>
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-primary to-emerald shadow-lg shadow-primary/30">
          <Zap className="h-5 w-5 text-[oklch(0.14_0.02_260)]" strokeWidth={2.5} />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="font-display text-sm font-bold tracking-tight">TITAN</div>
            <div className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground">Sports Intelligence OS</div>
          </div>
        )}
      </div>

      {/* Command palette search (only when expanded) */}
      {!collapsed && (
        <div className="mx-3 mb-3">
          <button
            onClick={() => setCmdOpen(true)}
            className="flex w-full items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-white/10 hover:bg-white/5 hover:text-foreground"
          >
            <Search className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1">Search anything…</span>
            <kbd className="flex items-center gap-0.5 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[9px]">
              <Command className="h-2.5 w-2.5" />K
            </kbd>
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav
        role="navigation"
        aria-label="Main navigation"
        className="flex-1 space-y-4 overflow-y-auto px-2 pb-4"
      >
        {nav.map((section) => (
          <div key={section.group} role="group" aria-label={section.group}>
            {!collapsed && (
              <div className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/60" aria-hidden="true">
                {section.group}
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.to;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    aria-label={collapsed ? item.label : undefined}
                    aria-current={active ? "page" : undefined}
                    title={collapsed ? item.label : undefined}
                    className={`group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-all nav-item-hover ${
                      collapsed ? "justify-center" : ""
                    } ${
                      active
                        ? "bg-primary/10 text-foreground shadow-[inset_0_0_0_1px_oklch(0.72_0.19_245/0.25)]"
                        : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${active ? "text-primary" : ""}`} aria-hidden="true" />
                    {!collapsed && (
                      <>
                        <span className="flex-1 truncate">{item.label}</span>
                        {active && <ChevronRight className="h-3.5 w-3.5 text-primary" aria-hidden="true" />}
                      </>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/5 p-2">
        {/* Shortcuts hint */}
        {!collapsed && (
          <button
            onClick={() => setShortcutsOpen(true)}
            aria-label="Open keyboard shortcuts (?)"
            className="mb-2 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors btn-press"
          >
            <Keyboard className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Keyboard shortcuts</span>
            <kbd className="ml-auto rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px]" aria-hidden="true">?</kbd>
          </button>
        )}
        <div className={`glass rounded-lg p-3 ${collapsed ? "hidden" : ""}`} role="status" aria-live="polite">
          <div className="mb-1 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-emerald">
            <span className="relative flex h-1.5 w-1.5" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald" />
            </span>
            System Nominal
          </div>
          <div className="text-xs text-muted-foreground">All engines online · v2.4.1</div>
        </div>
      </div>
    </>
  );

  return (
    <div className="dark min-h-screen text-foreground">
      {/* Skip navigation for keyboard / screen-reader users */}
      <a href="#main-content" className="skip-nav">Skip to main content</a>

      {/* Global overlays */}
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
      <NotificationCenter open={notifOpen} onClose={() => setNotifOpen(false)} />
      <LiveActivityCenter open={activityOpen} onClose={() => setActivityOpen(false)} />
      <KeyboardShortcutsModal open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />

      {/* G-chord indicator */}
      {gPressed && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-4 right-4 z-[500] flex items-center gap-2 rounded-lg border border-primary/30 bg-[oklch(0.15_0.025_260)] px-3 py-2 text-xs shadow-xl animate-fade-in"
        >
          <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-primary">G</kbd>
          <span className="text-muted-foreground">→ press D M L A V T R S W E</span>
        </div>
      )}

      {/* Mobile nav overlay */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-[90] bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="flex min-h-screen w-full">
        {/* Desktop Sidebar */}
        <aside
          aria-label="Sidebar"
          className={`sticky top-0 hidden h-screen shrink-0 flex-col border-r border-white/5 bg-[oklch(0.13_0.02_260)]/80 backdrop-blur-xl transition-all duration-300 lg:flex ${
            sidebarCollapsed ? "w-16" : "w-64"
          }`}
        >
          <SidebarContent collapsed={sidebarCollapsed} />

          {/* Collapse toggle */}
          <button
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!sidebarCollapsed}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="absolute -right-3 top-20 z-10 grid h-6 w-6 place-items-center rounded-full border border-white/10 bg-[oklch(0.18_0.025_260)] text-muted-foreground shadow-md hover:text-foreground transition-colors btn-press"
          >
            {sidebarCollapsed
              ? <PanelLeftOpen className="h-3 w-3" aria-hidden="true" />
              : <PanelLeftClose className="h-3 w-3" aria-hidden="true" />}
          </button>
        </aside>

        {/* Mobile Sidebar */}
        <aside
          aria-label="Mobile navigation"
          aria-hidden={!mobileNavOpen}
          className={`fixed top-0 left-0 z-[100] h-full w-72 shrink-0 flex-col border-r border-white/5 bg-[oklch(0.13_0.02_260)] transition-transform duration-300 lg:hidden flex ${
            mobileNavOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <SidebarContent collapsed={false} />
        </aside>

        {/* Main */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Topbar */}
          <header
            role="banner"
            className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-white/5 bg-[oklch(0.13_0.02_260)]/70 px-4 backdrop-blur-xl md:px-6"
          >
            {/* Mobile menu toggle */}
            <button
              aria-label={mobileNavOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={mobileNavOpen}
              aria-controls="mobile-sidebar"
              className="grid h-8 w-8 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground transition-colors btn-press lg:hidden"
              onClick={() => setMobileNavOpen((v) => !v)}
            >
              {mobileNavOpen
                ? <X className="h-4 w-4" aria-hidden="true" />
                : <Menu className="h-4 w-4" aria-hidden="true" />}
            </button>

            {/* Mobile logo */}
            <div className="flex items-center gap-2 lg:hidden" aria-hidden="true">
              <div className="grid h-8 w-8 place-items-center rounded-md bg-gradient-to-br from-primary to-emerald">
                <Zap className="h-4 w-4 text-[oklch(0.14_0.02_260)]" strokeWidth={2.5} />
              </div>
              <span className="font-display text-sm font-bold">TITAN</span>
            </div>

            {/* Search → command palette */}
            <button
              aria-label="Search matches, teams, markets (Ctrl+K)"
              aria-haspopup="dialog"
              className="relative hidden max-w-md flex-1 md:block btn-press"
              onClick={() => setCmdOpen(true)}
            >
              <div className="flex h-9 w-full items-center gap-2 rounded-md border border-white/5 bg-white/5 px-3 text-sm text-muted-foreground transition-colors hover:border-white/10 hover:bg-white/[0.07]">
                <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="flex-1 text-left">Search matches, teams, markets…</span>
                <kbd className="flex items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px]" aria-hidden="true">
                  <Command className="h-3 w-3" />K
                </kbd>
              </div>
            </button>

            <div className="ml-auto flex items-center gap-2">
              {/* Live feed indicator */}
              <div
                role="status"
                aria-label="Live data feed active"
                className="hidden items-center gap-1.5 rounded-md border border-emerald/20 bg-emerald/10 px-2.5 py-1 text-xs font-medium text-emerald md:flex"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-emerald shadow-[0_0_8px] shadow-emerald animate-pulse" aria-hidden="true" />
                LIVE FEED
              </div>

              {/* Theme switcher */}
              <div className="relative" ref={themePickerRef}>
                <button
                  onClick={() => setThemePickerOpen((v) => !v)}
                  aria-label="Switch theme"
                  aria-expanded={themePickerOpen}
                  aria-haspopup="listbox"
                  title="Switch theme"
                  className="hidden sm:grid h-9 w-9 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground transition-colors btn-press"
                >
                  <Palette className="h-4 w-4" aria-hidden="true" />
                </button>

                {themePickerOpen && (
                  <div
                    role="listbox"
                    aria-label="Select theme"
                    className="absolute right-0 top-full mt-2 w-54 rounded-xl border border-white/10 bg-[oklch(0.18_0.025_260)] p-1.5 shadow-2xl animate-fade-in z-50"
                  >
                    <div className="px-2 pb-1.5 pt-0.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Appearance
                    </div>
                    {THEMES.map((t) => (
                      <button
                        key={t.value}
                        role="option"
                        aria-selected={theme === t.value}
                        onClick={() => { setTheme(t.value); setThemePickerOpen(false); }}
                        className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs transition-colors btn-press ${
                          theme === t.value
                            ? "bg-primary/10 text-foreground"
                            : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                        }`}
                      >
                        <span
                          className="h-3.5 w-3.5 shrink-0 rounded-full shadow-sm ring-1 ring-white/10"
                          style={{ background: t.primary }}
                          aria-hidden="true"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="font-medium leading-tight">{t.label}</div>
                          <div className="truncate text-[10px] text-muted-foreground/70">{t.description}</div>
                        </div>
                        {theme === t.value && (
                          <Check className="h-3.5 w-3.5 shrink-0 text-primary" aria-hidden="true" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Keyboard shortcuts button */}
              <button
                onClick={() => setShortcutsOpen((v) => !v)}
                aria-label="Open keyboard shortcuts (?)"
                aria-expanded={shortcutsOpen}
                aria-haspopup="dialog"
                title="Keyboard shortcuts (?)"
                className="hidden sm:grid h-9 w-9 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground transition-colors btn-press"
              >
                <Keyboard className="h-4 w-4" aria-hidden="true" />
              </button>

              {/* Live Activity */}
              <button
                onClick={() => setActivityOpen((v) => !v)}
                aria-label="Open live activity center"
                aria-expanded={activityOpen}
                aria-haspopup="dialog"
                title="Live Activity Center"
                className={`relative grid h-9 w-9 place-items-center rounded-md border text-muted-foreground hover:text-foreground transition-colors btn-press ${
                  activityOpen ? "border-emerald/30 bg-emerald/10 text-emerald" : "border-white/5 bg-white/5"
                }`}
              >
                <Activity className="h-4 w-4" aria-hidden="true" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-emerald shadow-[0_0_6px] shadow-emerald animate-pulse" aria-hidden="true" />
              </button>

              {/* Notifications */}
              <button
                onClick={() => setNotifOpen((v) => !v)}
                aria-label={`Notifications — ${notifCount} unread`}
                aria-expanded={notifOpen}
                aria-haspopup="dialog"
                title={`Notifications (${notifCount} unread)`}
                className={`relative grid h-9 w-9 place-items-center rounded-md border text-muted-foreground hover:text-foreground transition-colors btn-press ${
                  notifOpen ? "border-primary/30 bg-primary/10 text-primary" : "border-white/5 bg-white/5"
                }`}
              >
                <Bell className="h-4 w-4" aria-hidden="true" />
                {notifCount > 0 && (
                  <span
                    aria-hidden="true"
                    className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-primary-foreground badge-pulse"
                  >
                    {notifCount}
                  </span>
                )}
              </button>

              {/* User avatar */}
              <div
                className="flex items-center gap-2 rounded-md border border-white/5 bg-white/5 px-2 py-1"
                role="img"
                aria-label="Signed in as Titan Analyst"
              >
                <div className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-primary to-emerald text-[10px] font-bold text-[oklch(0.14_0.02_260)]" aria-hidden="true">TN</div>
                <span className="hidden text-xs font-medium sm:inline">Titan Analyst</span>
              </div>
            </div>
          </header>

          <main
            id="main-content"
            tabIndex={-1}
            className="min-w-0 flex-1 p-4 md:p-6 lg:p-8 transition-all duration-200 page-enter outline-none"
          >
            {children}
          </main>
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
