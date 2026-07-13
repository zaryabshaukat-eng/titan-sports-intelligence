import { createFileRoute } from "@tanstack/react-router";
import { memo, useCallback, useMemo, useRef, useState } from "react";
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from "react-resizable-panels";
import {
  Search, Brain, Plus, Save, Bold, Italic, List, Code, Maximize2, StickyNote,
  RefreshCw, MessageSquare, FileText, Bookmark, BookmarkPlus, Clock, Download,
  Check, ChevronDown, Trash2, Copy, Sparkles, FlaskConical, BarChart2,
  PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen,
  LayoutTemplate, RotateCcw, TrendingUp, TrendingDown, AlertCircle, Loader2, Minus,
  SendHorizonal, Bot,
} from "lucide-react";
import { StatusPill } from "../components/titan/primitives";
import { ConfidenceGauge, RiskMeter, TrendIndicator } from "../components/titan/ConfidenceWidgets";
import { Timeline } from "../components/titan/Timeline";
import { useLocalStorage } from "../hooks/useLocalStorage";

export const Route = createFileRoute("/research")({ component: ResearchPage });

/* ─── Data ─── */
const MATCHES = [
  { id: "m1", comp: "Premier League", home: "Man City",    away: "Arsenal",      ko: "17:30",      conf: 87, ev: "+6.8%", risk: 28, status: "online" as const, fair: "1.72", market: "1.85" },
  { id: "m2", comp: "La Liga",        home: "Real Madrid", away: "Barcelona",    ko: "20:00",      conf: 91, ev: "+5.2%", risk: 21, status: "online" as const, fair: "1.63", market: "1.74" },
  { id: "m3", comp: "Bundesliga",     home: "Bayern",      away: "Dortmund",     ko: "LIVE 62'",   conf: 82, ev: "+4.1%", risk: 35, status: "training" as const, fair: "1.91", market: "2.00" },
  { id: "m4", comp: "Serie A",        home: "Inter",       away: "Juventus",     ko: "19:45",      conf: 78, ev: "+3.9%", risk: 42, status: "online" as const, fair: "2.05", market: "2.14" },
  { id: "m5", comp: "Ligue 1",        home: "PSG",         away: "Marseille",    ko: "21:00",      conf: 74, ev: "+3.2%", risk: 19, status: "online" as const, fair: "1.48", market: "1.55" },
  { id: "m6", comp: "UCL",            home: "Liverpool",   away: "Leverkusen",   ko: "Tomorrow",   conf: 69, ev: "+2.8%", risk: 55, status: "idle" as const, fair: "2.10", market: "2.18" },
];

type MatchType = typeof MATCHES[number];

const AI_ENGINES = [
  { name: "Statistical Engine",  weight: 34, signal: "Over 2.5 — 74% probability", direction: "up"   as const, color: "bg-primary" },
  { name: "Market Intelligence", weight: 28, signal: "Sharp money confirmed on Over", direction: "up"   as const, color: "bg-emerald" },
  { name: "Historical Engine",   weight: 20, signal: "O2.5 hit in 7/9 H2H fixtures", direction: "up"   as const, color: "bg-amber-500" },
  { name: "Tactical Engine",     weight: 12, signal: "High-press setup favours goals", direction: "up"   as const, color: "bg-violet-500" },
  { name: "Consensus Engine",    weight:  6, signal: "87% cross-engine agreement",    direction: "flat" as const, color: "bg-sky-500" },
];

const AI_ACTIVITY = [
  { engine: "Statistical Engine",  action: "Recomputed xG/xGA — Man City home average: 2.4",        time: "12s ago",  status: "online"   as const },
  { engine: "Market Intelligence", action: "Sharp movement detected — Man City -1 AH",               time: "34s ago",  status: "online"   as const },
  { engine: "Historical Engine",   action: "Pattern matched 847 analogous fixtures",                  time: "1m ago",   status: "online"   as const },
  { engine: "Consensus Engine",    action: "Updated ensemble weights across 9 engines",               time: "2m ago",   status: "online"   as const },
  { engine: "Explainability",      action: "Generated SHAP attribution for Over 2.5",                time: "3m ago",   status: "beta"     as const },
];

const DEFAULT_NOTES: Record<string, string> = {
  m1: `# Man City vs Arsenal — Research Notes\n\n**Match:** Manchester City vs Arsenal\n**Competition:** Premier League — Matchweek 32\n**Kickoff:** Today, 17:30 GMT\n\n---\n\n## Model Signals\n\nThe Statistical Engine reports a **fair line of 1.72** for Over 2.5, against Pinnacle's best available of **1.85** — representing a **+6.8% EV** edge. Confidence sits at **82/100** with cross-engine consensus of **87%**.\n\n### Key Factors\n\n1. **xG Trajectory** — Man City averaging 2.4 xG over last 6 PL home fixtures\n2. **Arsenal Press Intensity** — PPDA of 8.2, highest in division\n3. **Historical H2H** — Over 2.5 hit in 7 of last 9 meetings at Etihad\n4. **Line Movement** — Over 2.5 opened at 1.90, now 1.85 (sharp money confirmed)\n\n---\n\n## Risk Assessment\n\n- **Market Risk:** High liquidity, unlikely to move further before kickoff\n- **Model Risk:** Tactical Engine still training; formation data weighted at 60%\n- **Bankroll Note:** Kelly fraction 2.8% — moderate position sizing recommended\n\n---\n\n## Conclusion\n\nStrong value bet at current price. Execute before kickoff tightens line further.\n`,
  m2: `# Real Madrid vs Barcelona — Research Notes\n\nEl Clásico. High-confidence play.\n\n## Key Signals\n\n1. Real Madrid -0.5 AH — fair line 1.63, market 1.74 (+5.2% EV)\n2. Bellingham returns from suspension — significant uplift to xG\n3. Barcelona away record: W3 D2 L4 this season`,
  m3: `# Bayern vs Dortmund — Live Research Notes\n\nTracking in-play xG divergence. Update every 5'.\n\n## Live Updates\n\n- 62': Bayern xG: 1.8 | Dortmund xG: 0.7\n- Model probability for Bayern win: 71%`,
};

type Bookmark = { id: string; match: string; label: string; value: string; note: string; ts: string };
const DEFAULT_BOOKMARKS: Bookmark[] = [
  { id: "b1", match: "Man City vs Arsenal",   label: "Over 2.5 EV",         value: "+6.8%", note: "Pinnacle best available 1.85 vs fair 1.72", ts: "2m ago" },
  { id: "b2", match: "Man City vs Arsenal",   label: "Confidence Score",     value: "87",    note: "Cross-engine consensus on O2.5", ts: "5m ago" },
  { id: "b3", match: "Real Madrid vs Barça",  label: "Handicap EV",          value: "+5.2%", note: "RM -0.5 AH value confirmed by sharp action", ts: "14m ago" },
];

const DISCUSSION_MESSAGES = [
  { role: "user",      text: "What's the primary driver for the Over 2.5 signal on Man City vs Arsenal?" },
  { role: "assistant", text: "The primary driver is xG trajectory. Man City are averaging 2.4 xG at home over the last 6 Premier League fixtures, while Arsenal's high-press system (PPDA 8.2) tends to concede transition opportunities. Historical H2H also strongly supports — Over 2.5 has hit in 7 of 9 recent Etihad meetings.", ts: "Statistical Engine + Historical Engine" },
  { role: "user",      text: "Is the line movement significant?" },
  { role: "assistant", text: "Yes — the Over opened at 1.90 on Pinnacle and has moved to 1.85, indicating sustained sharp action. Our Market Intelligence Engine flagged this as 'confirmed sharp money' with 3-book consensus. This is a positive signal, though it reduces the EV slightly from our initial +8.1% to +6.8%.", ts: "Market Intelligence Engine" },
];

/* ─── Toolbar button ─── */
function ToolbarBtn({ icon: Icon, label, active, onClick }: { icon: React.ComponentType<{ className?: string }>; label: string; active?: boolean; onClick?: () => void }) {
  return (
    <button title={label} aria-label={label} onClick={onClick}
      className={`grid h-7 w-7 place-items-center rounded transition-colors btn-press ${active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-foreground"}`}>
      <Icon className="h-3.5 w-3.5" />
    </button>
  );
}

/* ─── Progress checklist ─── */
const PROGRESS_STEPS = [
  { key: "match",    label: "Match selected" },
  { key: "stats",    label: "Statistical analysis" },
  { key: "market",   label: "Market data reviewed" },
  { key: "notes",    label: "Research notes written" },
  { key: "ai",       label: "AI discussion reviewed" },
  { key: "report",   label: "Final report generated" },
];

function ResearchProgress({ match, notesLen, discussionSeen, reportSeen }: {
  match: MatchType; notesLen: number; discussionSeen: boolean; reportSeen: boolean;
}) {
  const steps = [
    { key: "match",  done: true },
    { key: "stats",  done: true },
    { key: "market", done: match.conf > 70 },
    { key: "notes",  done: notesLen > 80 },
    { key: "ai",     done: discussionSeen },
    { key: "report", done: reportSeen },
  ];
  const doneCount = steps.filter((s) => s.done).length;
  const pct = Math.round((doneCount / steps.length) * 100);
  return (
    <div className="border-t border-white/5 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">Research Progress</span>
        <span className="font-mono text-[10px] text-primary">{pct}%</span>
      </div>
      <div className="mb-3 h-1 overflow-hidden rounded-full bg-white/5">
        <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <div className="space-y-1.5">
        {PROGRESS_STEPS.map((s, i) => {
          const done = steps[i].done;
          return (
            <div key={s.key} className="flex items-center gap-2">
              <div className={`grid h-4 w-4 shrink-0 place-items-center rounded-full border text-[8px] ${done ? "border-emerald/40 bg-emerald/10 text-emerald" : "border-white/10 bg-white/5 text-muted-foreground/30"}`}>
                {done ? <Check className="h-2.5 w-2.5" /> : <Minus className="h-2.5 w-2.5" />}
              </div>
              <span className={`text-[11px] ${done ? "text-foreground/80" : "text-muted-foreground/50"}`}>{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── AI Evidence panel ─── */
function AIEvidence({ match }: { match: MatchType }) {
  const totalWeight = AI_ENGINES.reduce((s, e) => s + e.weight, 0);
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-white/5 px-3 py-2.5">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">AI Evidence</div>
        <div className="mt-0.5 text-[11px] text-muted-foreground">{match.home} vs {match.away}</div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {/* Context card */}
        <div className="p-3 border-b border-white/5">
          <div className="rounded-lg border border-primary/20 bg-primary/[0.04] p-2.5">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground">{match.comp}</div>
                <div className="text-sm font-semibold">{match.home} vs {match.away}</div>
              </div>
              <StatusPill status={match.status} />
            </div>
            <div className="mt-2.5 flex items-center gap-4">
              <div className="text-center">
                <div className="text-[9px] text-muted-foreground">Fair</div>
                <div className="font-mono text-sm font-bold">{match.fair}</div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-muted-foreground">Market</div>
                <div className="font-mono text-sm font-bold">{match.market}</div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-muted-foreground">EV</div>
                <div className="font-mono text-sm font-bold text-emerald">{match.ev}</div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-muted-foreground">Conf</div>
                <div className="font-mono text-sm font-bold text-primary">{match.conf}</div>
              </div>
            </div>
          </div>
        </div>
        {/* Confidence gauge */}
        <div className="border-b border-white/5 p-3">
          <div className="flex items-center justify-center mb-2">
            <ConfidenceGauge value={match.conf} size={100} />
          </div>
          <RiskMeter value={match.risk} label="Market Risk" />
        </div>
        {/* Engine contributions */}
        <div className="border-b border-white/5 p-3">
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">Engine Weights</div>
          <div className="space-y-2.5">
            {AI_ENGINES.map((e) => (
              <div key={e.name}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-[10px] font-medium text-muted-foreground">{e.name}</span>
                  <span className="font-mono text-[10px] text-foreground">{e.weight}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div className={`h-full rounded-full ${e.color}`} style={{ width: `${(e.weight / totalWeight) * 100}%` }} />
                </div>
                <div className="mt-0.5 flex items-center gap-1">
                  {e.direction === "up"   && <TrendingUp   className="h-2.5 w-2.5 text-emerald" />}
                  {e.direction === "down" && <TrendingDown  className="h-2.5 w-2.5 text-destructive" />}
                  {e.direction === "flat" && <Minus         className="h-2.5 w-2.5 text-muted-foreground" />}
                  <span className="text-[9px] text-muted-foreground">{e.signal}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* AI Activity feed */}
        <div className="p-3">
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">Engine Activity</div>
          <div className="space-y-1.5">
            {AI_ACTIVITY.map((item, i) => (
              <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Brain className="h-2.5 w-2.5 text-primary" aria-hidden="true" />
                  <span className="text-[9px] font-semibold text-primary">{item.engine}</span>
                  <span className="ml-auto text-[8px] text-muted-foreground">{item.time}</span>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">{item.action}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── AI Discussion panel ─── */
const AIDiscussion = memo(function AIDiscussion({ match }: { match: MatchType }) {
  const [msgs, setMsgs] = useState(DISCUSSION_MESSAGES);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const AI_REPLIES: Record<string, string> = {
    default: `Based on the current model signals for ${match.home} vs ${match.away}: confidence is ${match.conf}/100 with ${match.ev} EV. The Statistical Engine is the primary driver at 34% weight. All engines agree directionally — cross-engine consensus is 87%.`,
  };

  const send = useCallback(() => {
    if (!draft.trim() || loading) return;
    const userMsg = draft.trim();
    setDraft("");
    setMsgs((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);
    window.setTimeout(() => {
      setMsgs((prev) => [...prev, {
        role: "assistant",
        text: AI_REPLIES.default,
        ts: "Consensus Engine",
      }]);
      setLoading(false);
      window.setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }, 1200);
  }, [draft, loading, match]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-white/5 px-3 py-2 flex items-center gap-2">
        <Bot className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">AI Discussion</span>
        <span className="ml-auto rounded-full border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold text-primary">BETA</span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {msgs.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && (
              <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                <Brain className="h-3.5 w-3.5" aria-hidden="true" />
              </div>
            )}
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
              m.role === "user"
                ? "bg-primary/10 text-foreground"
                : "bg-white/[0.03] border border-white/5 text-foreground/80"
            }`}>
              {m.text}
              {m.role === "assistant" && "ts" in m && (
                <div className="mt-1 flex items-center gap-1 text-[9px] text-muted-foreground">
                  <Sparkles className="h-2.5 w-2.5" aria-hidden="true" />
                  {m.ts as string}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
              <Brain className="h-3.5 w-3.5" aria-hidden="true" />
            </div>
            <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" aria-label="AI is responding" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-white/5 p-2">
        <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask the AI about this match…"
            aria-label="Ask AI a question about this match"
            className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          <button onClick={send} disabled={!draft.trim() || loading} aria-label="Send message"
            className="grid h-6 w-6 place-items-center rounded-md bg-primary text-primary-foreground disabled:opacity-40 hover:bg-primary/90 transition-colors btn-press">
            <SendHorizonal className="h-3 w-3" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
});

/* ─── Final Report panel ─── */
function FinalReport({ match, notes }: { match: MatchType; notes: string }) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-white/5 px-3 py-2 flex items-center gap-2">
        <FileText className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">Final Report</span>
        <span className="ml-auto text-[9px] text-muted-foreground">Auto-generated · v1</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
        <div>
          <div className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">{match.comp}</div>
          <h2 className="font-display text-lg font-bold">{match.home} vs {match.away}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Generated {new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })} · Research Workspace</p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: "Confidence", value: `${match.conf}/100`, color: "text-primary" },
            { label: "EV Edge",    value: match.ev,             color: "text-emerald" },
            { label: "Market Risk",value: `${match.risk}%`,     color: match.risk > 40 ? "text-amber-400" : "text-foreground" },
          ].map((m) => (
            <div key={m.label} className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-center">
              <div className="text-[9px] text-muted-foreground uppercase tracking-wider">{m.label}</div>
              <div className={`font-mono text-base font-bold ${m.color}`}>{m.value}</div>
            </div>
          ))}
        </div>
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3 space-y-2">
          <div className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground">Engine Consensus</div>
          {AI_ENGINES.map((e) => (
            <div key={e.name} className="flex items-center gap-2">
              <div className={`h-2 rounded-full ${e.color}`} style={{ width: `${e.weight * 2}px` }} />
              <span className="text-xs text-muted-foreground">{e.name}</span>
              <span className="ml-auto font-mono text-xs font-bold">{e.weight}%</span>
            </div>
          ))}
        </div>
        {notes.length > 20 && (
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
            <div className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground mb-2">Research Notes Summary</div>
            <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap line-clamp-8">{notes.slice(0, 600)}{notes.length > 600 ? "…" : ""}</p>
          </div>
        )}
        <div className="rounded-lg border border-emerald/20 bg-emerald/[0.04] p-3">
          <div className="font-semibold text-[11px] uppercase tracking-wider text-emerald mb-1">Recommendation</div>
          <p className="text-xs text-foreground/80">Strong value identified at current market price. Kelly fraction: 2.8%. Execute before line tightens further. Monitor for late team news.</p>
        </div>
      </div>
    </div>
  );
}

/* ─── Bookmarks panel ─── */
function BookmarksPanel({ bookmarks, onRemove, onAdd, match }: {
  bookmarks: Bookmark[];
  onRemove: (id: string) => void;
  onAdd: (b: Omit<Bookmark, "id" | "ts">) => void;
  match: MatchType;
}) {
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ label: "", value: "", note: "" });
  const matchBookmarks = bookmarks.filter((b) => b.match === `${match.home} vs ${match.away}`);
  const otherBookmarks = bookmarks.filter((b) => b.match !== `${match.home} vs ${match.away}`);

  const save = () => {
    if (!form.label) return;
    onAdd({ match: `${match.home} vs ${match.away}`, ...form });
    setForm({ label: "", value: "", note: "" });
    setAdding(false);
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2">
        <Bookmark className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70">Bookmarks</span>
        <button onClick={() => setAdding((v) => !v)} aria-label="Add bookmark"
          className="ml-auto grid h-5 w-5 place-items-center rounded-md hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors">
          <BookmarkPlus className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {adding && (
          <div className="border-b border-white/5 p-3 space-y-2 bg-white/[0.02]">
            <input value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} placeholder="Label (e.g. Over 2.5 EV)" aria-label="Bookmark label"
              className="w-full rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/20" />
            <div className="flex gap-2">
              <input value={form.value} onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))} placeholder="Value (e.g. +6.8%)" aria-label="Bookmark value"
                className="w-1/3 rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none" />
              <input value={form.note} onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} placeholder="Note…" aria-label="Bookmark note"
                className="flex-1 rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none" />
            </div>
            <div className="flex gap-2">
              <button onClick={save} className="flex-1 rounded-md bg-primary/10 border border-primary/20 py-1 text-xs text-primary hover:bg-primary/20 transition-colors btn-press">Save</button>
              <button onClick={() => setAdding(false)} className="flex-1 rounded-md border border-white/5 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors">Cancel</button>
            </div>
          </div>
        )}
        {matchBookmarks.length > 0 && (
          <div className="p-2">
            <div className="px-1 pb-1 text-[9px] uppercase tracking-widest text-muted-foreground/50">{match.home} vs {match.away}</div>
            {matchBookmarks.map((b) => (
              <div key={b.id} className="group flex items-start gap-2 rounded-lg p-2 hover:bg-white/[0.03] transition-colors">
                <Bookmark className="h-3 w-3 mt-0.5 shrink-0 text-primary" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-medium">{b.label}</span>
                    {b.value && <span className="font-mono text-[10px] text-emerald">{b.value}</span>}
                  </div>
                  <p className="text-[10px] text-muted-foreground">{b.note}</p>
                  <span className="text-[9px] text-muted-foreground/50">{b.ts}</span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => navigator.clipboard.writeText(`${b.label}: ${b.value} — ${b.note}`)} aria-label="Copy bookmark" title="Copy"
                    className="grid h-5 w-5 place-items-center rounded text-muted-foreground hover:text-foreground"><Copy className="h-3 w-3" /></button>
                  <button onClick={() => onRemove(b.id)} aria-label="Remove bookmark" title="Remove"
                    className="grid h-5 w-5 place-items-center rounded text-muted-foreground hover:text-destructive"><Trash2 className="h-3 w-3" /></button>
                </div>
              </div>
            ))}
          </div>
        )}
        {otherBookmarks.length > 0 && (
          <div className="p-2 border-t border-white/5">
            <div className="px-1 pb-1 text-[9px] uppercase tracking-widest text-muted-foreground/50">Other Matches</div>
            {otherBookmarks.map((b) => (
              <div key={b.id} className="group flex items-start gap-2 rounded-lg p-2 hover:bg-white/[0.03] transition-colors opacity-60">
                <Bookmark className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="text-[9px] text-muted-foreground/70 mb-0.5">{b.match}</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-medium">{b.label}</span>
                    {b.value && <span className="font-mono text-[10px] text-emerald">{b.value}</span>}
                  </div>
                </div>
                <button onClick={() => onRemove(b.id)} aria-label="Remove bookmark"
                  className="grid h-5 w-5 place-items-center rounded text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive"><Trash2 className="h-3 w-3" /></button>
              </div>
            ))}
          </div>
        )}
        {bookmarks.length === 0 && !adding && (
          <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
            <Bookmark className="h-6 w-6 text-muted-foreground/30" />
            <p className="text-xs text-muted-foreground">No bookmarks yet</p>
            <p className="text-[10px] text-muted-foreground/50">Pin key data points to revisit later</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Main page ─── */
function ResearchPage() {
  const [selectedMatch, setSelectedMatch] = useState<MatchType>(MATCHES[0]);
  const [matchSearch, setMatchSearch] = useState("");
  const [centerTab, setCenterTab] = useState<"notes" | "discussion" | "report">("notes");
  const [rightTab, setRightTab] = useState<"evidence" | "bookmarks" | "timeline">("evidence");
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [discussionSeen, setDiscussionSeen] = useState(false);
  const [reportSeen, setReportSeen] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const [exported, setExported] = useState(false);
  const [bookmarks, setBookmarks] = useLocalStorage<Bookmark[]>("titan.research.bookmarks.v1", DEFAULT_BOOKMARKS);
  const [noteStore, setNoteStore] = useLocalStorage<Record<string, string>>("titan.research.notes.v2", DEFAULT_NOTES);

  const noteContent = noteStore[selectedMatch.id] ?? DEFAULT_NOTES[selectedMatch.id] ?? "";

  const updateNote = (val: string) => setNoteStore((p) => ({ ...p, [selectedMatch.id]: val }));
  const flashSaved = () => { setSavedFlash(true); window.setTimeout(() => setSavedFlash(false), 1300); };

  const wordCount = useMemo(() => noteContent.trim().split(/\s+/).filter(Boolean).length, [noteContent]);

  const filteredMatches = useMemo(() =>
    MATCHES.filter((m) => !matchSearch || [m.home, m.away, m.comp].some((s) => s.toLowerCase().includes(matchSearch.toLowerCase()))),
    [matchSearch]
  );

  const handleCenterTab = (tab: typeof centerTab) => {
    setCenterTab(tab);
    if (tab === "discussion") setDiscussionSeen(true);
    if (tab === "report") setReportSeen(true);
  };

  const addBookmark = useCallback((b: Omit<Bookmark, "id" | "ts">) => {
    setBookmarks((prev) => [...prev, { ...b, id: `b${Date.now()}`, ts: "just now" }]);
  }, [setBookmarks]);
  const removeBookmark = useCallback((id: string) => {
    setBookmarks((prev) => prev.filter((b) => b.id !== id));
  }, [setBookmarks]);

  const exportReport = () => {
    const content = `# Research Report — ${selectedMatch.home} vs ${selectedMatch.away}\n\n**Competition:** ${selectedMatch.comp}\n**Confidence:** ${selectedMatch.conf}/100\n**EV:** ${selectedMatch.ev}\n**Market Risk:** ${selectedMatch.risk}%\n\n---\n\n## Research Notes\n\n${noteContent}\n\n---\n\n*Generated by TITAN Sports Intelligence OS*\n`;
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedMatch.home.replace(/\s/g, "-")}-vs-${selectedMatch.away.replace(/\s/g, "-")}-research.md`;
    a.click();
    URL.revokeObjectURL(url);
    setExported(true);
    window.setTimeout(() => setExported(false), 1500);
  };

  return (
    <div className="-m-4 md:-m-6 lg:-m-8 h-[calc(100vh-56px)] flex flex-col">
      {/* Workspace toolbar */}
      <div className="flex items-center gap-2 border-b border-white/5 bg-[oklch(0.13_0.02_260)]/60 px-4 py-2.5 backdrop-blur-sm">
        <FlaskConical className="h-4 w-4 text-primary shrink-0" aria-hidden="true" />
        <div>
          <div className="text-[9px] font-semibold uppercase tracking-[0.2em] text-primary">Workspace</div>
          <h1 className="font-display text-sm font-bold leading-tight tracking-tight">Research Workspace</h1>
        </div>

        {/* Panel toggles */}
        <div className="ml-4 flex items-center gap-1 rounded-lg border border-white/5 bg-white/[0.03] p-0.5">
          <button onClick={() => setLeftOpen((v) => !v)} aria-label={leftOpen ? "Collapse match explorer" : "Expand match explorer"} title="Toggle match explorer"
            className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium transition-colors btn-press ${leftOpen ? "bg-white/10 text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            {leftOpen ? <PanelLeftClose className="h-3 w-3" aria-hidden="true" /> : <PanelLeftOpen className="h-3 w-3" aria-hidden="true" />}
            <span className="hidden sm:inline">Explorer</span>
          </button>
          <button onClick={() => setRightOpen((v) => !v)} aria-label={rightOpen ? "Collapse intelligence panel" : "Expand intelligence panel"} title="Toggle intelligence"
            className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium transition-colors btn-press ${rightOpen ? "bg-white/10 text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            {rightOpen ? <PanelRightClose className="h-3 w-3" aria-hidden="true" /> : <PanelRightOpen className="h-3 w-3" aria-hidden="true" />}
            <span className="hidden sm:inline">Intel</span>
          </button>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => { setLeftOpen(true); setRightOpen(true); }} aria-label="Reset layout"
            title="Reset layout" className="grid h-7 w-7 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground transition-colors btn-press">
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
          <button onClick={flashSaved} aria-label="Save notes"
            className="inline-flex items-center gap-1.5 rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors btn-press">
            {savedFlash ? <Check className="h-3.5 w-3.5 text-emerald" aria-hidden="true" /> : <Save className="h-3.5 w-3.5" aria-hidden="true" />}
            <span>{savedFlash ? "Saved" : "Save"}</span>
          </button>
          <button onClick={exportReport} aria-label="Export research report"
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors btn-press">
            {exported ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Download className="h-3.5 w-3.5" aria-hidden="true" />}
            <span>{exported ? "Exported" : "Export"}</span>
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup orientation="horizontal" autoSaveId="research-workspace-v2" className="h-full">

          {/* LEFT — Match Explorer + Research Progress */}
          {leftOpen && (
            <>
              <Panel defaultSize={20} minSize={15} maxSize={30}>
                <div className="flex h-full flex-col border-r border-white/5 overflow-hidden bg-[oklch(0.13_0.02_260)]/40">
                  <div className="border-b border-white/5 p-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-2">Match Explorer</div>
                    <div className="relative">
                      <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
                      <input value={matchSearch} onChange={(e) => setMatchSearch(e.target.value)}
                        placeholder="Filter matches…" aria-label="Filter matches"
                        className="h-7 w-full rounded-md border border-white/5 bg-white/5 pl-7 pr-2 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/20" />
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto py-1 min-h-0">
                    {filteredMatches.map((m) => {
                      const active = selectedMatch.id === m.id;
                      return (
                        <button key={m.id} onClick={() => setSelectedMatch(m)} aria-current={active ? "true" : undefined}
                          className={`w-full text-left px-3 py-2.5 transition-colors ${active ? "bg-primary/10 border-l-2 border-primary" : "border-l-2 border-transparent hover:bg-white/[0.03]"}`}>
                          <div className="flex items-center justify-between gap-1 mb-0.5">
                            <span className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">{m.comp}</span>
                            <span className={`text-[9px] font-mono ${m.ko.includes("LIVE") ? "text-emerald animate-pulse" : "text-muted-foreground"}`}>{m.ko}</span>
                          </div>
                          <div className="text-xs font-medium leading-tight">{m.home} <span className="text-muted-foreground">vs</span> {m.away}</div>
                          <div className="mt-1 flex items-center gap-2">
                            <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                              <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${m.conf}%` }} />
                            </div>
                            <span className="font-mono text-[9px] text-primary">{m.conf}</span>
                            <span className="text-[9px] font-mono text-emerald">{m.ev}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                  <ResearchProgress match={selectedMatch} notesLen={noteContent.length} discussionSeen={discussionSeen} reportSeen={reportSeen} />
                </div>
              </Panel>
              <PanelResizeHandle className="w-px bg-white/5 hover:bg-primary/30 transition-colors cursor-col-resize" />
            </>
          )}

          {/* CENTER — Notes / Discussion / Final Report */}
          <Panel defaultSize={leftOpen ? (rightOpen ? 52 : 72) : (rightOpen ? 70 : 100)} minSize={30}>
            <div className="flex h-full flex-col overflow-hidden">
              {/* Tab bar */}
              <div className="flex items-center border-b border-white/5 bg-[oklch(0.13_0.02_260)]/30">
                {([
                  { key: "notes"     as const, label: "Notes",        icon: StickyNote    },
                  { key: "discussion"as const, label: "AI Discussion", icon: MessageSquare },
                  { key: "report"    as const, label: "Final Report",  icon: FileText      },
                ]).map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button key={tab.key} onClick={() => handleCenterTab(tab.key)}
                      aria-current={centerTab === tab.key ? "true" : undefined}
                      className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors ${centerTab === tab.key ? "border-b-2 border-primary text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                      <Icon className="h-3 w-3" aria-hidden="true" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Center content */}
              {centerTab === "notes" && (
                <div className="flex flex-col flex-1 overflow-hidden">
                  {/* Editor toolbar */}
                  <div className="flex items-center gap-0.5 border-b border-white/5 px-3 py-1.5">
                    <ToolbarBtn icon={Bold}      label="Bold"       onClick={() => updateNote(noteContent + "**bold**")} />
                    <ToolbarBtn icon={Italic}    label="Italic"     onClick={() => updateNote(noteContent + "*italic*")} />
                    <div className="mx-1.5 h-4 w-px bg-white/10" />
                    <ToolbarBtn icon={List}      label="List"       onClick={() => updateNote(noteContent + "\n- ")} />
                    <ToolbarBtn icon={Code}      label="Code"       onClick={() => updateNote(noteContent + "`code`")} />
                    <div className="mx-1.5 h-4 w-px bg-white/10" />
                    <ToolbarBtn icon={RefreshCw} label="Sync with AI" />
                    <div className="ml-auto flex items-center gap-1">
                      <ToolbarBtn icon={Maximize2} label="Fullscreen" />
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-5 min-h-0">
                    <textarea
                      key={selectedMatch.id}
                      value={noteContent}
                      onChange={(e) => updateNote(e.target.value)}
                      className="h-full w-full resize-none bg-transparent font-mono text-sm leading-relaxed text-foreground/90 focus:outline-none placeholder:text-muted-foreground"
                      spellCheck={false}
                      aria-label={`Research notes for ${selectedMatch.home} vs ${selectedMatch.away}`}
                      placeholder={`# ${selectedMatch.home} vs ${selectedMatch.away}\n\nStart your research notes here…`}
                    />
                  </div>
                  <div className="flex items-center justify-between border-t border-white/5 px-4 py-2 text-[10px] text-muted-foreground">
                    <div className="flex items-center gap-3">
                      <span>Markdown</span>
                      <span>·</span>
                      <span className={savedFlash ? "text-emerald" : ""} aria-live="polite">{savedFlash ? "Saved" : "Auto-saved to this device"}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span>{wordCount} words</span>
                      <button onClick={flashSaved} aria-label="Save notes"
                        className="inline-flex items-center gap-1 rounded border border-white/5 bg-white/5 px-1.5 py-0.5 hover:text-foreground btn-press">
                        <Save className="h-3 w-3" aria-hidden="true" /> Save
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {centerTab === "discussion" && <AIDiscussion match={selectedMatch} />}

              {centerTab === "report" && <FinalReport match={selectedMatch} notes={noteContent} />}
            </div>
          </Panel>

          {/* RIGHT — AI Evidence top + Bookmarks/Timeline bottom */}
          {rightOpen && (
            <>
              <PanelResizeHandle className="w-px bg-white/5 hover:bg-primary/30 transition-colors cursor-col-resize" />
              <Panel defaultSize={28} minSize={20} maxSize={40}>
                <PanelGroup orientation="vertical" autoSaveId="research-right-v2" className="h-full">
                  {/* TOP — AI Evidence */}
                  <Panel defaultSize={58} minSize={30}>
                    <div className="h-full border-l border-white/5 overflow-hidden">
                      <AIEvidence match={selectedMatch} />
                    </div>
                  </Panel>

                  <PanelResizeHandle className="h-px bg-white/5 hover:bg-primary/30 transition-colors cursor-row-resize" />

                  {/* BOTTOM — Bookmarks / Timeline */}
                  <Panel defaultSize={42} minSize={20}>
                    <div className="flex h-full flex-col border-l border-white/5 overflow-hidden">
                      {/* Sub-tab bar */}
                      <div className="flex border-b border-white/5 shrink-0">
                        {([
                          { key: "bookmarks"as const, label: "Bookmarks", icon: Bookmark },
                          { key: "timeline" as const, label: "Timeline",  icon: Clock    },
                        ]).map((tab) => {
                          const Icon = tab.icon;
                          return (
                            <button key={tab.key} onClick={() => setRightTab(tab.key)}
                              aria-current={rightTab === tab.key ? "true" : undefined}
                              className={`flex flex-1 items-center justify-center gap-1.5 py-2 text-[10px] font-medium transition-colors ${rightTab === tab.key ? "border-b-2 border-primary text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                              <Icon className="h-3 w-3" aria-hidden="true" />
                              {tab.label}
                            </button>
                          );
                        })}
                      </div>
                      <div className="flex-1 overflow-hidden min-h-0">
                        {rightTab === "bookmarks" && (
                          <BookmarksPanel bookmarks={bookmarks} onRemove={removeBookmark} onAdd={addBookmark} match={selectedMatch} />
                        )}
                        {rightTab === "timeline" && (
                          <div className="h-full overflow-y-auto">
                            <Timeline showFilters={false} showGrouping={false} />
                          </div>
                        )}
                      </div>
                    </div>
                  </Panel>
                </PanelGroup>
              </Panel>
            </>
          )}
        </PanelGroup>
      </div>
    </div>
  );
}
