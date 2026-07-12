import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";
import { X, Keyboard, Command } from "lucide-react";

export interface ShortcutDef {
  keys: string[];
  description: string;
  category: string;
}

export const ALL_SHORTCUTS: ShortcutDef[] = [
  // Navigation
  { keys: ["G", "D"],    description: "Go to Dashboard",          category: "Navigation" },
  { keys: ["G", "M"],    description: "Go to Matches",            category: "Navigation" },
  { keys: ["G", "L"],    description: "Go to Live Odds",          category: "Navigation" },
  { keys: ["G", "A"],    description: "Go to AI Intelligence",    category: "Navigation" },
  { keys: ["G", "V"],    description: "Go to Value Analysis",     category: "Navigation" },
  { keys: ["G", "T"],    description: "Go to Timeline",           category: "Navigation" },
  { keys: ["G", "R"],    description: "Go to Reports",            category: "Navigation" },
  { keys: ["G", "S"],    description: "Go to System Status",      category: "Navigation" },
  { keys: ["G", "W"],    description: "Go to Research Workspace", category: "Navigation" },
  { keys: ["G", "E"],    description: "Go to Settings",           category: "Navigation" },
  // Global
  { keys: ["Ctrl","K"],  description: "Open Command Palette",     category: "Global" },
  { keys: ["/"],         description: "Focus Search",             category: "Global" },
  { keys: ["?"],         description: "Show Keyboard Shortcuts",  category: "Global" },
  { keys: ["Esc"],       description: "Close panel / dialog",     category: "Global" },
  // Workspace
  { keys: ["Ctrl","P"],  description: "Print / Export",           category: "Workspace" },
  { keys: ["Ctrl","F"],  description: "Fullscreen",               category: "Workspace" },
  { keys: ["Ctrl","S"],  description: "Save Research Note",       category: "Workspace" },
  { keys: ["Ctrl","Z"],  description: "Undo",                     category: "Workspace" },
];

const CHORD_MAP: Record<string, string> = {
  D: "/",
  M: "/matches",
  L: "/live-odds",
  A: "/ai-intelligence",
  V: "/value-analysis",
  T: "/timeline",
  R: "/reports",
  S: "/system-status",
  W: "/research",
  E: "/settings",
};

/* ─────────── Shortcut badge ─────────── */
function Key({ children }: { children: string }) {
  return (
    <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-white/10 bg-white/[0.06] px-1.5 font-mono text-[10px] text-muted-foreground shadow-[0_1px_0_oklch(1_0_0/0.06)]">
      {children}
    </kbd>
  );
}

/* ─────────── Modal ─────────── */
interface KeyboardShortcutsProps {
  open: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsModal({ open, onClose }: KeyboardShortcutsProps) {
  const categories = Array.from(new Set(ALL_SHORTCUTS.map((s) => s.category)));

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-2xl mx-4 glass-strong rounded-2xl overflow-hidden border border-white/10 shadow-2xl shadow-black/60 max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-white/5 px-5 py-4">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
            <Keyboard className="h-4 w-4" />
          </div>
          <div>
            <div className="font-display text-sm font-semibold">Keyboard Shortcuts</div>
            <div className="text-[11px] text-muted-foreground">Professional shortcut reference</div>
          </div>
          <button
            onClick={onClose}
            className="ml-auto rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-5">
          <div className="grid gap-6 sm:grid-cols-2">
            {categories.map((cat) => (
              <div key={cat}>
                <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">
                  {cat}
                </div>
                <div className="space-y-2">
                  {ALL_SHORTCUTS.filter((s) => s.category === cat).map((s) => (
                    <div key={s.description} className="flex items-center justify-between gap-4 rounded-lg border border-white/[0.04] bg-white/[0.02] px-3 py-2">
                      <span className="text-xs text-muted-foreground">{s.description}</span>
                      <div className="flex items-center gap-1 shrink-0">
                        {s.keys.map((k, i) => (
                          <span key={k} className="flex items-center gap-1">
                            {i > 0 && <span className="text-[10px] text-muted-foreground/40">then</span>}
                            <Key>{k}</Key>
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/5 px-5 py-3 text-[11px] text-muted-foreground">
          <span>Press <Key>?</Key> to toggle · <Key>Esc</Key> to close</span>
          <div className="flex items-center gap-1">
            <Command className="h-3 w-3" />
            <span>Titan Intelligence</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────── useKeyboardShortcuts hook ─────────── */
export function useKeyboardShortcuts({
  onOpenCommandPalette,
  onToggleShortcuts,
}: {
  onOpenCommandPalette: () => void;
  onToggleShortcuts: () => void;
}) {
  const navigate = useNavigate();
  const [gPressed, setGPressed] = useState(false);
  const [gTimer, setGTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handler = useCallback((e: KeyboardEvent) => {
    const tag = (e.target as HTMLElement).tagName;
    const inInput = tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement).isContentEditable;

    // Ctrl+K — command palette
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      onOpenCommandPalette();
      return;
    }

    // Escape — handled individually by panels
    if (e.key === "Escape") return;

    if (inInput) return;

    // ? — show shortcuts
    if (e.key === "?" && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      onToggleShortcuts();
      return;
    }

    // / — focus search (command palette)
    if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      onOpenCommandPalette();
      return;
    }

    // G chord — wait for second key
    if (e.key === "g" || e.key === "G") {
      e.preventDefault();
      setGPressed(true);
      if (gTimer) clearTimeout(gTimer);
      const timer = setTimeout(() => setGPressed(false), 1500);
      setGTimer(timer);
      return;
    }

    // Second key of G chord
    if (gPressed) {
      const route = CHORD_MAP[e.key.toUpperCase()];
      if (route) {
        e.preventDefault();
        navigate({ to: route } as Parameters<typeof navigate>[0]);
      }
      setGPressed(false);
      if (gTimer) clearTimeout(gTimer);
      setGTimer(null);
    }
  }, [gPressed, gTimer, onOpenCommandPalette, onToggleShortcuts, navigate]);

  useEffect(() => {
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handler]);

  return { gPressed };
}

/* ─────────── Mini shortcut hint (for contextual display) ─────────── */
export function ShortcutHint({ keys, label }: { keys: string[]; label?: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
      {label && <span>{label}</span>}
      {keys.map((k, i) => (
        <span key={k} className="flex items-center gap-0.5">
          {i > 0 && <span className="opacity-50">·</span>}
          <Key>{k}</Key>
        </span>
      ))}
    </span>
  );
}
