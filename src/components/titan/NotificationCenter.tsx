import { useState, useMemo } from "react";
import {
  X, Bell, Search, CheckCheck, Archive, Info, CheckCircle2,
  AlertTriangle, AlertOctagon, Monitor, Brain, TrendingUp, FlaskConical, Filter,
} from "lucide-react";

export type NotifCategory =
  | "information" | "success" | "warning" | "critical"
  | "system" | "ai" | "market" | "research" | "alert";

export interface Notification {
  id: string;
  category: NotifCategory;
  title: string;
  message: string;
  time: string;
  read: boolean;
  archived: boolean;
}

const SAMPLE_NOTIFICATIONS: Notification[] = [
  { id: "n1",  category: "alert",       title: "Value Spike Detected",          message: "EV +6.8% on Man City vs Arsenal — Over 2.5 (Pinnacle)",                   time: "2m ago",  read: false, archived: false },
  { id: "n2",  category: "market",      title: "Arbitrage Opportunity",          message: "3-way arb across Pinnacle / Bet365 / Betfair — ROI 3.2%",                  time: "8m ago",  read: false, archived: false },
  { id: "n3",  category: "ai",          title: "Model Confidence Updated",       message: "Statistical Engine recalibrated — Serie A slate +2.1 pts",                 time: "14m ago", read: false, archived: false },
  { id: "n4",  category: "warning",     title: "Sharp Movement Detected",        message: "Significant line movement on Bayern -0.5 across 6 books",                  time: "26m ago", read: false, archived: false },
  { id: "n5",  category: "system",      title: "Data Feed Restored",             message: "SkyBet feed reconnected after 3m interruption — all markets synced",        time: "41m ago", read: true,  archived: false },
  { id: "n6",  category: "success",     title: "Backtesting Complete",           message: "Q2 2024 Champions League simulation finished — 847 fixtures, +11.4% ROI",   time: "1h ago",  read: true,  archived: false },
  { id: "n7",  category: "research",    title: "Report Generated",               message: "Weekly value report for Premier League Week 32 is ready to view",          time: "2h ago",  read: true,  archived: false },
  { id: "n8",  category: "ai",          title: "Tactical Engine Training",       message: "Tactical Engine v2.1 training on 2024-25 formation dataset (71%)",          time: "3h ago",  read: true,  archived: false },
  { id: "n9",  category: "critical",    title: "API Rate Limit Warning",         message: "Betfair API at 89% of rate limit — throttling may occur in 6 minutes",     time: "3h ago",  read: true,  archived: false },
  { id: "n10", category: "information", title: "New League Added",               message: "Scottish Premiership data now live — 12 teams, full market coverage",       time: "5h ago",  read: true,  archived: false },
  { id: "n11", category: "market",      title: "Closing Line Value Alert",       message: "CLV exceeds +4% threshold for 3 recent bets — model confirmation strong",  time: "6h ago",  read: true,  archived: false },
  { id: "n12", category: "success",     title: "Prediction Engine Online",       message: "Prediction Engine v1.3 deployed successfully — 94% calibration accuracy",  time: "8h ago",  read: true,  archived: false },
];

const CATEGORY_CONFIG: Record<NotifCategory, { icon: React.ComponentType<{ className?: string }>; color: string; bg: string; label: string }> = {
  information: { icon: Info,          color: "text-primary",     bg: "bg-primary/10",     label: "Info" },
  success:     { icon: CheckCircle2,  color: "text-emerald",     bg: "bg-emerald/10",     label: "Success" },
  warning:     { icon: AlertTriangle, color: "text-warning",     bg: "bg-warning/10",     label: "Warning" },
  critical:    { icon: AlertOctagon,  color: "text-destructive", bg: "bg-destructive/10", label: "Critical" },
  system:      { icon: Monitor,       color: "text-muted-foreground", bg: "bg-white/5",   label: "System" },
  ai:          { icon: Brain,         color: "text-primary",     bg: "bg-primary/10",     label: "AI" },
  market:      { icon: TrendingUp,    color: "text-emerald",     bg: "bg-emerald/10",     label: "Market" },
  research:    { icon: FlaskConical,  color: "text-warning",     bg: "bg-warning/10",     label: "Research" },
  alert:       { icon: Bell,          color: "text-primary",     bg: "bg-primary/10",     label: "Alert" },
};

const FILTER_TABS = ["All", "Unread", "AI", "Market", "Alerts", "System"] as const;
type FilterTab = (typeof FILTER_TABS)[number];

interface NotificationCenterProps {
  open: boolean;
  onClose: () => void;
}

export function NotificationCenter({ open, onClose }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>(SAMPLE_NOTIFICATIONS);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterTab>("All");

  const unreadCount = notifications.filter((n) => !n.read && !n.archived).length;

  const filtered = useMemo(() => {
    return notifications.filter((n) => {
      if (n.archived) return false;
      if (search && !n.title.toLowerCase().includes(search.toLowerCase()) && !n.message.toLowerCase().includes(search.toLowerCase())) return false;
      if (activeFilter === "Unread" && n.read) return false;
      if (activeFilter === "AI" && n.category !== "ai") return false;
      if (activeFilter === "Market" && n.category !== "market") return false;
      if (activeFilter === "Alerts" && !["alert", "warning", "critical"].includes(n.category)) return false;
      if (activeFilter === "System" && n.category !== "system") return false;
      return true;
    });
  }, [notifications, search, activeFilter]);

  const markRead = (id: string) =>
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));

  const archiveOne = (id: string) =>
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, archived: true } : n)));

  const markAllRead = () =>
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));

  const clearAll = () =>
    setNotifications((prev) => prev.map((n) => ({ ...n, archived: true })));

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-[150] bg-black/40 backdrop-blur-[2px]"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 z-[160] h-full w-full max-w-md flex flex-col bg-[oklch(0.15_0.025_260)] border-l border-white/5 shadow-2xl transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
              <Bell className="h-4 w-4" />
            </div>
            <div>
              <div className="font-display text-sm font-semibold">Notifications</div>
              {unreadCount > 0 && (
                <div className="text-[11px] text-muted-foreground">{unreadCount} unread</div>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Search */}
        <div className="px-4 py-3 border-b border-white/5">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search notifications…"
              className="h-8 w-full rounded-md border border-white/5 bg-white/5 pl-8 pr-3 text-xs placeholder:text-muted-foreground focus:border-primary/30 focus:outline-none focus:ring-1 focus:ring-primary/20"
            />
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1 overflow-x-auto border-b border-white/5 px-3 py-2 scrollbar-none">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveFilter(tab)}
              className={`shrink-0 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                activeFilter === tab
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              {tab}
              {tab === "Unread" && unreadCount > 0 && (
                <span className="ml-1 rounded-full bg-primary px-1 py-0 text-[9px] font-bold text-primary-foreground">
                  {unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notification list */}
        <div className="flex-1 overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2 text-center px-6">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-white/5">
                <Bell className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">No notifications</p>
            </div>
          ) : (
            filtered.map((notif) => {
              const cfg = CATEGORY_CONFIG[notif.category];
              const Icon = cfg.icon;
              return (
                <div
                  key={notif.id}
                  onClick={() => markRead(notif.id)}
                  className={`group relative flex gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-white/[0.03] ${
                    !notif.read ? "bg-primary/[0.03]" : ""
                  }`}
                >
                  {!notif.read && (
                    <div className="absolute left-1.5 top-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-primary" />
                  )}
                  <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${cfg.bg} ${cfg.color}`}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className={`text-xs font-semibold ${!notif.read ? "text-foreground" : "text-foreground/80"}`}>
                        {notif.title}
                      </div>
                      <span className="shrink-0 text-[10px] text-muted-foreground">{notif.time}</span>
                    </div>
                    <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground line-clamp-2">
                      {notif.message}
                    </p>
                    <div className="mt-1.5 flex items-center gap-1">
                      <span className={`text-[9px] font-semibold uppercase tracking-wider ${cfg.color}`}>
                        {cfg.label}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); archiveOne(notif.id); }}
                    className="shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-white/10 transition-all"
                    title="Archive"
                  >
                    <Archive className="h-3 w-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/5 px-4 py-3">
          <button
            onClick={markAllRead}
            className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark all read
          </button>
          <button
            onClick={clearAll}
            className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors"
          >
            <Archive className="h-3.5 w-3.5" />
            Clear all
          </button>
        </div>
      </div>
    </>
  );
}
