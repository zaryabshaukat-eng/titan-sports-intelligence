/**
 * TITAN Guided Tour
 * 6-step onboarding walkthrough shown on first visit.
 * Persisted to localStorage key "titan_onboarding_v1".
 * Replayed via onReplay callback from parent.
 */

import { useEffect, useState } from "react";
import {
  Zap, LayoutDashboard, FlaskConical, LineChart,
  FileText, CheckCircle2, ChevronRight, ChevronLeft, X,
} from "lucide-react";

const STORAGE_KEY = "titan_onboarding_v1";

interface Step {
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconText: string;
  eyebrow: string;
  title: string;
  description: string;
  highlight: string | null;
  tip?: string;
}

const STEPS: Step[] = [
  {
    icon: Zap,
    iconBg: "bg-gradient-to-br from-primary/30 to-emerald/20",
    iconText: "text-primary",
    eyebrow: "Welcome",
    title: "Welcome to TITAN",
    description:
      "Your sports intelligence command center. Nine AI engines, real-time markets, and deep research tools — all in one place. Let's walk through the key surfaces.",
    highlight: null,
    tip: "This tour takes about 30 seconds.",
  },
  {
    icon: LayoutDashboard,
    iconBg: "bg-emerald/15",
    iconText: "text-emerald",
    eyebrow: "Step 1 of 4",
    title: "Dashboard",
    description:
      "Your mission overview. Engine health, top value picks, live line movement, and key market signals — all visible at a glance without opening a single other page.",
    highlight: "/",
    tip: "Check the dashboard first every session.",
  },
  {
    icon: FlaskConical,
    iconBg: "bg-primary/15",
    iconText: "text-primary",
    eyebrow: "Step 2 of 4",
    title: "Research Workspace",
    description:
      "A three-column environment built for deep match analysis. Browse fixtures on the left, write notes in the center, and consult AI signals or historical cohorts on the right.",
    highlight: "/research",
    tip: "Panels are resizable — save your layout.",
  },
  {
    icon: LineChart,
    iconBg: "bg-warning/15",
    iconText: "text-warning",
    eyebrow: "Step 3 of 4",
    title: "Market Intelligence",
    description:
      "Track cross-book line movement and sharp money in real time. Spot steam moves before they close out, and filter by league, bookmaker, or edge threshold.",
    highlight: "/market-intelligence",
    tip: "Sharp action shows up here first.",
  },
  {
    icon: FileText,
    iconBg: "bg-primary/15",
    iconText: "text-primary",
    eyebrow: "Step 4 of 4",
    title: "Reports",
    description:
      "Every analysis you produce is saved as a signed, versioned intelligence report. Export to PDF, share with your team, or review your historical reasoning.",
    highlight: "/reports",
    tip: "Generate a report from the Research Workspace.",
  },
  {
    icon: CheckCircle2,
    iconBg: "bg-emerald/15",
    iconText: "text-emerald",
    eyebrow: "Done",
    title: "You're ready.",
    description:
      "TITAN is fully operational. Use ⌘K to search anything, or explore any section from the sidebar. Your session is saved automatically.",
    highlight: null,
    tip: "Press ? anytime to see all keyboard shortcuts.",
  },
];

interface GuidedTourProps {
  open: boolean;
  onClose: () => void;
  onHighlight: (route: string | null) => void;
}

export function GuidedTour({ open, onClose, onHighlight }: GuidedTourProps) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  // Sync highlight with current step
  useEffect(() => {
    if (open) onHighlight(current.highlight);
    else onHighlight(null);
  }, [step, open, current.highlight, onHighlight]);

  // Reset step when reopened
  useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  // Escape closes
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") handleClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open]);

  function handleClose() {
    try { localStorage.setItem(STORAGE_KEY, "done"); } catch { /* ignore */ }
    onHighlight(null);
    onClose();
  }

  function next() {
    if (isLast) { handleClose(); return; }
    setStep((s) => s + 1);
  }

  function prev() {
    if (!isFirst) setStep((s) => s - 1);
  }

  if (!open) return null;

  const Icon = current.icon;

  return (
    <div className="fixed inset-0 z-[400] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/75 backdrop-blur-md" onClick={handleClose} />

      {/* Card */}
      <div
        className="relative w-full max-w-md glass-strong rounded-2xl border border-white/10 shadow-2xl shadow-black/70 overflow-hidden animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top accent line */}
        <div className="h-0.5 w-full bg-gradient-to-r from-primary via-emerald to-primary/40" />

        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-4 pb-0">
          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">
            {current.eyebrow}
          </span>
          <button
            onClick={handleClose}
            className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
            aria-label="Skip tour"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5">
          {/* Icon */}
          <div className={`mb-4 grid h-14 w-14 place-items-center rounded-xl ${current.iconBg}`}>
            <Icon className={`h-7 w-7 ${current.iconText}`} />
          </div>

          <h2 className="font-display text-xl font-bold tracking-tight">{current.title}</h2>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{current.description}</p>

          {current.tip && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2.5">
              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              <span className="text-xs text-muted-foreground">{current.tip}</span>
            </div>
          )}
        </div>

        {/* Progress dots */}
        <div className="flex items-center justify-center gap-1.5 pb-4">
          {STEPS.map((_, i) => (
            <button
              key={i}
              onClick={() => setStep(i)}
              aria-label={`Go to step ${i + 1}`}
              className={`rounded-full transition-all duration-200 ${
                i === step
                  ? "h-1.5 w-5 bg-primary"
                  : i < step
                  ? "h-1.5 w-1.5 bg-primary/40"
                  : "h-1.5 w-1.5 bg-white/10"
              }`}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/5 px-5 py-4">
          <button
            onClick={prev}
            disabled={isFirst}
            className="flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-white/5 hover:text-foreground disabled:opacity-0 transition-all"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back
          </button>

          <button
            onClick={next}
            className={`flex items-center gap-1.5 rounded-md px-4 py-1.5 text-sm font-semibold transition-all btn-press ${
              isLast
                ? "bg-emerald/90 text-[oklch(0.14_0.02_260)] hover:bg-emerald"
                : "bg-primary/90 text-[oklch(0.14_0.02_260)] hover:bg-primary"
            }`}
          >
            {isLast ? "Start using TITAN" : "Next"}
            {!isLast && <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}

/** Returns true if the tour has not been completed yet. */
export function shouldShowTour(): boolean {
  if (typeof window === "undefined") return false;
  try { return localStorage.getItem(STORAGE_KEY) !== "done"; } catch { return false; }
}

/** Resets tour state so it shows again on next load. */
export function resetTour(): void {
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
}
