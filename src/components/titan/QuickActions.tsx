/**
 * TITAN Global Quick Actions
 * A floating action button (FAB) in the bottom-right corner.
 * Expands into a stacked action menu on click.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  Plus, X, FlaskConical, Trophy, Users,
  FileText, Download, Bookmark, Zap,
} from "lucide-react";

interface Action {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  to?: string;
  soon?: boolean;
}

const ACTIONS: Action[] = [
  {
    id: "research",
    icon: FlaskConical,
    label: "Start Research",
    description: "Open research workspace",
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/20",
    to: "/research",
  },
  {
    id: "match",
    icon: Trophy,
    label: "Open Match",
    description: "Browse today's fixtures",
    color: "text-emerald",
    bgColor: "bg-emerald/10",
    borderColor: "border-emerald/20",
    to: "/matches",
  },
  {
    id: "teams",
    icon: Users,
    label: "Compare Teams",
    description: "Team intelligence surface",
    color: "text-warning",
    bgColor: "bg-warning/10",
    borderColor: "border-warning/20",
    to: "/teams",
  },
  {
    id: "report",
    icon: FileText,
    label: "Create Report",
    description: "Generate intelligence report",
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/20",
    to: "/reports",
  },
  {
    id: "export",
    icon: Download,
    label: "Export Data",
    description: "Download reports & data",
    color: "text-foreground",
    bgColor: "bg-white/5",
    borderColor: "border-white/10",
    to: "/reports",
  },
  {
    id: "watchlist",
    icon: Bookmark,
    label: "Open Watchlist",
    description: "Saved matches & markets",
    color: "text-muted-foreground",
    bgColor: "bg-white/5",
    borderColor: "border-white/10",
    soon: true,
  },
];

export function QuickActions() {
  const [open, setOpen] = useState(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open]);

  function handleAction(action: Action) {
    if (action.soon) {
      // Show a subtle "coming soon" — just close menu for now
      setOpen(false);
      return;
    }
    if (action.to) {
      navigate({ to: action.to } as Parameters<typeof navigate>[0]);
    }
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="fixed bottom-6 right-6 z-[150] flex flex-col items-end gap-2">
      {/* Action list — slides in from bottom */}
      {open && (
        <div className="flex flex-col items-end gap-1.5 animate-fade-in mb-1">
          {/* Label hint */}
          <div className="mb-1 mr-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Quick Actions
          </div>

          {ACTIONS.map((action, idx) => {
            const Icon = action.icon;
            const isHovered = hovered === action.id;
            return (
              <button
                key={action.id}
                onClick={() => handleAction(action)}
                onMouseEnter={() => setHovered(action.id)}
                onMouseLeave={() => setHovered(null)}
                style={{ transitionDelay: `${idx * 20}ms` }}
                className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 shadow-xl shadow-black/30 transition-all duration-150 btn-press ${
                  action.soon
                    ? "cursor-default opacity-50 border-white/5 bg-[oklch(0.17_0.025_260)]"
                    : `border-white/10 bg-[oklch(0.17_0.025_260)] hover:border-white/20 hover:bg-[oklch(0.19_0.025_260)]`
                }`}
              >
                {/* Label — slides in on hover */}
                <div
                  className={`text-right transition-all duration-150 overflow-hidden ${
                    isHovered && !action.soon ? "max-w-40 opacity-100" : "max-w-0 opacity-0"
                  }`}
                >
                  <div className="whitespace-nowrap text-xs font-semibold">{action.label}</div>
                  <div className="whitespace-nowrap text-[10px] text-muted-foreground">{action.description}</div>
                </div>

                {/* Always-visible label (compact) */}
                {!isHovered && (
                  <span className="whitespace-nowrap text-xs font-medium text-muted-foreground">
                    {action.label}
                    {action.soon && <span className="ml-1.5 rounded-full bg-white/5 px-1.5 py-0.5 text-[9px] uppercase tracking-wider">soon</span>}
                  </span>
                )}

                {/* Icon */}
                <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${action.bgColor} ${action.borderColor}`}>
                  <Icon className={`h-4 w-4 ${action.color}`} />
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close quick actions" : "Open quick actions"}
        aria-expanded={open}
        className={`grid h-12 w-12 place-items-center rounded-full shadow-2xl shadow-black/50 transition-all duration-200 btn-press ${
          open
            ? "bg-white/10 border border-white/20 text-foreground rotate-45"
            : "bg-gradient-to-br from-primary to-emerald border border-primary/40 text-[oklch(0.14_0.02_260)]"
        }`}
      >
        {open ? (
          <X className="h-5 w-5" />
        ) : (
          <Plus className="h-5 w-5" strokeWidth={2.5} />
        )}
      </button>

      {/* Tooltip when closed */}
      {!open && (
        <div className="pointer-events-none mr-0.5 text-[10px] text-muted-foreground/70 text-center">
          <Zap className="h-2.5 w-2.5 inline mr-0.5 text-primary" />
          Quick
        </div>
      )}
    </div>
  );
}
