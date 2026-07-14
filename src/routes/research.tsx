import { createFileRoute } from "@tanstack/react-router";
import { useState, useCallback, useRef } from "react";
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from "react-resizable-panels";
import type { ImperativePanelGroupHandle } from "react-resizable-panels";
import { PageHeader } from "../components/titan/AppShell";
import {
  Trophy, Search, Brain, ChevronRight,
  Plus, Save, Bold, Italic, List, Code, AlignLeft, Maximize2,
  Activity, Target, Zap, StickyNote,
  MessageSquare, RefreshCw, PanelLeftClose, PanelLeftOpen,
  PanelRightClose, PanelRightOpen, RotateCcw, History,
  CheckCircle2, Clock, TrendingUp, TrendingDown, Minus,
} from "lucide-react";
import { GlassCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import { ConfidenceGauge, RiskMeter, TrendIndicator } from "../components/titan/ConfidenceWidgets";
import { AiDiscussionPanel } from "../components/titan/AiDiscussionPanel";

export const Route = createFileRoute("/research")({ component: ResearchPage });

const matches = [
  { comp: "Premier League", home: "Man City", away: "Arsenal",     ko: "17:30",    conf: 87, ev: "+6.8%", status: "online"   as const },
  { comp: "La Liga",        home: "Real Madrid", away: "Barcelona", ko: "20:00",   conf: 91, ev: "+5.2%", status: "online"   as const },
  { comp: "Bundesliga",     home: "Bayern",  away: "Dortmund",     ko: "LIVE 62'", conf: 82, ev: "+4.1%", status: "training" as const },
  { comp: "Serie A",        home: "Inter",   away: "Juventus",     ko: "19:45",    conf: 78, ev: "+3.9%", status: "online"   as const },
  { comp: "Ligue 1",        home: "PSG",     away: "Marseille",    ko: "21:00",    conf: 74, ev: "+3.2%", status: "online"   as const },
  { comp: "UCL",            home: "Liverpool",away:"Leverkusen",   ko: "Tomorrow", conf: 69, ev: "+2.8%", status: "idle"     as const },
];

const aiActivity = [
  { engine: "Statistical Engine",   action: "Recomputed xG/xGA for Arsenal vs Man City",       time: "12s ago", status: "online" as const },
  { engine: "Market Intelligence",  action: "Detected sharp movement — Man City -1 AH",         time: "34s ago", status: "online" as const },
  { engine: "Historical Engine",    action: "Pattern matched 847 analogous fixtures",            time: "1m ago",  status: "online" as const },
  { engine: "Consensus Engine",     action: "Updated ensemble weights across 9 engines",         time: "2m ago",  status: "online" as const },
  { engine: "Explainability",       action: "Generated SHAP attribution for Over 2.5",          time: "3m ago",  status: "beta"   as const },
];

const notes = [
  { id: "n1", title: "Man City vs Arsenal — Pre-match Analysis", tags: ["Premier League", "Value"], updated: "2m ago" },
  { id: "n2", title: "Bayern Dortmund — Live Model Notes",        tags: ["Bundesliga", "Live"],     updated: "8m ago" },
  { id: "n3", title: "UCL R16 — Historical Pattern Summary",      tags: ["Champions League"],       updated: "1h ago" },
];

/* Similar matches for the Similar Match Explorer */
const similarMatches = [
  { date: "Mar 12, 2025", home: "Man City", away: "Arsenal", comp: "Premier League", similarity: 94, result: "3-1",  ou: "Over",  conf: 89, note: "Same xG profile, similar line movement" },
  { date: "Oct 5, 2024",  home: "Man City", away: "Arsenal", comp: "Premier League", similarity: 91, result: "2-2",  ou: "Over",  conf: 84, note: "Sharp money confirmed pre-match"          },
  { date: "Feb 11, 2024", home: "Man City", away: "Chelsea", comp: "Premier League", similarity: 83, result: "1-0",  ou: "Under", conf: 71, note: "Similar xG ratio, different opponent"     },
  { date: "Apr 26, 2023", home: "Man City", away: "Arsenal", comp: "Premier League", similarity: 88, result: "4-1",  ou: "Over",  conf: 92, note: "Highest confidence match in cohort"       },
  { date: "Jan 1, 2023",  home: "Man City", away: "Everton", comp: "Premier League", similarity: 76, result: "3-1",  ou: "Over",  conf: 78, note: "Weaker opponent, different shape"         },
];

const PLACEHOLDER_CONTENT = `# Man City vs Arsenal — Research Notes

**Match:** Manchester City vs Arsenal  
**Competition:** Premier League — Matchweek 32  
**Kickoff:** Today, 17:30 GMT

---

## Model Signals

The Statistical Engine reports a **fair line of 1.72** for Over 2.5, against Pinnacle's best available of **1.85** — representing a **+6.8% EV** edge. Confidence sits at **82/100** with cross-engine consensus of **87%**.

### Key Factors

1. **xG Trajectory** — Man City averaging 2.4 xG over last 6 PL home fixtures
2. **Arsenal Press Intensity** — PPDA of 8.2, highest in division (creates transition chances)
3. **Historical Head-to-Head** — Over 2.5 hit in 7 of last 9 meetings at Etihad
4. **Line Movement** — Over 2.5 opened at 1.90, now 1.85 (sharp money confirmed)

---

## Risk Assessment

- **Market Risk:** High liquidity, unlikely to move further before kickoff
- **Model Risk:** Tactical Engine still training; formation data weighted at 60%
- **Bankroll Note:** Kelly fraction 2.8% — moderate position sizing recommended

---

## Conclusion

Strong value bet at current price. Execute before kickoff tightens line further.
`;

const LAYOUT_STORAGE_KEY = "titan_research_layout";

function ToolbarButton({
  icon: Icon, label, active,
}: { icon: React.ComponentType<{ className?: string }>; label: string; active?: boolean }) {
  return (
    <button
      title={label}
      className={`grid h-7 w-7 place-items-center rounded transition-colors ${
        active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
      }`}
    >
      <Icon className="h-3.5 w-3.5" />
    </button>
  );
}

/* ── Similar Match Explorer ── */
function SimilarMatchExplorer({ match }: { match: typeof matches[0] }) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b border-white/5 px-3 py-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-1">
          Similar Matches
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
          <History className="h-3 w-3" />
          <span>Historical similarity engine · {match.home} profile</span>
        </div>
      </div>

      {/* Placeholder notice */}
      <div className="mx-3 mt-3 mb-1 flex items-start gap-1.5 rounded-md border border-primary/20 bg-primary/5 px-2.5 py-2">
        <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
        <p className="text-[9px] leading-relaxed text-primary/80">
          Historical similarity engine not yet connected — displaying example data to illustrate future functionality.
        </p>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-2 px-3 py-2">
        {[
          { label: "Matched", value: "847" },
          { label: "Over rate", value: "73%" },
          { label: "Avg EV", value: "+2.9%" },
        ].map((s) => (
          <div key={s.label} className="rounded-lg border border-white/5 bg-white/[0.02] py-2 text-center">
            <div className="font-display text-sm font-bold">{s.value}</div>
            <div className="text-[9px] text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Match list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
        {similarMatches.map((m, i) => {
          const overUnder = m.ou === "Over";
          return (
            <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
              {/* Top row */}
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div>
                  <div className="text-[10px] font-semibold text-muted-foreground">{m.comp} · {m.date}</div>
                  <div className="text-xs font-medium">{m.home} vs {m.away}</div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="font-mono text-sm font-bold">{m.result}</div>
                  <div className={`flex items-center gap-0.5 text-[9px] font-semibold ${overUnder ? "text-emerald" : "text-warning"}`}>
                    {overUnder ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
                    {m.ou}
                  </div>
                </div>
              </div>

              {/* Similarity bar */}
              <div className="mb-1.5 flex items-center gap-2">
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-emerald"
                    style={{ width: `${m.similarity}%` }}
                  />
                </div>
                <span className="font-mono text-[9px] text-muted-foreground">{m.similarity}% match</span>
              </div>

              {/* Note */}
              <div className="text-[9px] text-muted-foreground">{m.note}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Signals panel ── */
function SignalsPanel({ match }: { match: typeof matches[0] }) {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Match context */}
      <div className="border-b border-white/5 p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-2">
          Active Context
        </div>
        <div className="rounded-lg border border-primary/20 bg-primary/[0.04] p-2.5">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{match.comp}</div>
          <div className="text-sm font-semibold mt-0.5">{match.home} vs {match.away}</div>
          <div className="mt-2 flex items-center gap-3">
            <div>
              <div className="text-[9px] text-muted-foreground">Confidence</div>
              <div className="font-mono text-sm font-bold text-primary">{match.conf}</div>
            </div>
            <div>
              <div className="text-[9px] text-muted-foreground">EV</div>
              <div className="font-mono text-sm font-bold text-emerald">{match.ev}</div>
            </div>
            <StatusPill status={match.status} />
          </div>
        </div>
      </div>

      {/* Confidence widgets */}
      <div className="border-b border-white/5 p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-3">
          Intelligence Signals
        </div>
        <div className="flex justify-center mb-3">
          <ConfidenceGauge value={match.conf} size={120} />
        </div>
        <RiskMeter value={28} label="Market Risk" />
        <div className="mt-3 space-y-2">
          <TrendIndicator direction="up"   value="+6.8% EV"  label="Expected value edge"  magnitude="strong"   />
          <TrendIndicator direction="up"   value="+2.4 xG"   label="Man City home xG"     magnitude="moderate" />
          <TrendIndicator direction="down" value="1.85 odds"  label="Tightening line"     magnitude="weak"     />
        </div>
      </div>

      {/* AI Activity feed */}
      <div className="p-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-2">
          AI Activity
        </div>
        <div className="space-y-2">
          {aiActivity.map((item, i) => (
            <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
              <div className="flex items-center gap-1.5 mb-1">
                <Brain className="h-3 w-3 text-primary" />
                <span className="text-[10px] font-semibold text-primary">{item.engine}</span>
                <span className="ml-auto text-[9px] text-muted-foreground">{item.time}</span>
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">{item.action}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Save/reset layout helpers ── */
function getSavedLayout(): [number, number, number] | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LAYOUT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as [number, number, number];
  } catch { return null; }
}

function saveLayout(sizes: number[]) {
  try { localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(sizes)); } catch { /* ignore */ }
}

function clearLayout() {
  try { localStorage.removeItem(LAYOUT_STORAGE_KEY); } catch { /* ignore */ }
}

/* ── Main page ── */
function ResearchPage() {
  const panelGroupRef = useRef<ImperativePanelGroupHandle>(null);

  const [selectedMatch, setSelectedMatch] = useState(matches[0]);
  const [matchSearch,  setMatchSearch]  = useState("");
  const [noteContent]                   = useState(PLACEHOLDER_CONTENT);
  const [activeNote,   setActiveNote]   = useState(notes[0].id);
  const [leftCollapsed,  setLeftCollapsed]  = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [rightTab, setRightTab] = useState<"signals" | "discussion" | "similar">("signals");
  const [savedNotice, setSavedNotice] = useState(false);

  const filteredMatches = matches.filter(
    (m) =>
      !matchSearch ||
      m.home.toLowerCase().includes(matchSearch.toLowerCase()) ||
      m.away.toLowerCase().includes(matchSearch.toLowerCase()) ||
      m.comp.toLowerCase().includes(matchSearch.toLowerCase()),
  );

  const handleSaveLayout = useCallback(() => {
    // read current sizes from the group imperatively
    const group = panelGroupRef.current;
    if (group) {
      // PanelGroup doesn't expose getLayout() on the handle in v4,
      // but we can persist via onLayout callback instead (handled below).
    }
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2000);
  }, []);

  const handleResetLayout = useCallback(() => {
    clearLayout();
    panelGroupRef.current?.setLayout([22, 50, 28]);
  }, []);

  const savedLayout = getSavedLayout();
  const defaultLayout: [number, number, number] = savedLayout ?? [22, 50, 28];

  return (
    <div className="-m-4 md:-m-6 lg:-m-8 h-[calc(100vh-56px)] flex flex-col">
      {/* Topbar */}
      <div className="flex items-center gap-3 border-b border-white/5 bg-[oklch(0.13_0.02_260)]/60 px-5 py-3 backdrop-blur-sm">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">Workspace</div>
          <h1 className="font-display text-lg font-bold tracking-tight">Research Workspace</h1>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          {/* Left panel toggle */}
          <button
            onClick={() => setLeftCollapsed((v) => !v)}
            title={leftCollapsed ? "Show match explorer" : "Hide match explorer"}
            className="hidden xl:inline-flex items-center gap-1 rounded-md border border-white/5 bg-white/5 px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            {leftCollapsed ? <PanelLeftOpen className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
          </button>

          {/* Right panel toggle */}
          <button
            onClick={() => setRightCollapsed((v) => !v)}
            title={rightCollapsed ? "Show intelligence panel" : "Hide intelligence panel"}
            className="hidden xl:inline-flex items-center gap-1 rounded-md border border-white/5 bg-white/5 px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            {rightCollapsed ? <PanelRightOpen className="h-3.5 w-3.5" /> : <PanelRightClose className="h-3.5 w-3.5" />}
          </button>

          <div className="hidden xl:block mx-1 h-4 w-px bg-white/10" />

          {/* Reset layout */}
          <button
            onClick={handleResetLayout}
            title="Reset to default layout"
            className="hidden xl:inline-flex items-center gap-1 rounded-md border border-white/5 bg-white/5 px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          {/* Save layout */}
          <button
            onClick={handleSaveLayout}
            className={`hidden xl:inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              savedNotice
                ? "border-emerald/20 bg-emerald/10 text-emerald"
                : "border-white/5 bg-white/5 text-muted-foreground hover:text-foreground"
            }`}
          >
            {savedNotice
              ? <><CheckCircle2 className="h-3.5 w-3.5" /> Saved</>
              : <><Save className="h-3.5 w-3.5" /> Save Layout</>}
          </button>

          <div className="mx-1 h-4 w-px bg-white/10" />

          <button className="inline-flex items-center gap-1.5 rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Save className="h-3.5 w-3.5" /> Save
          </button>
          <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90">
            <Plus className="h-3.5 w-3.5" /> New Note
          </button>
        </div>
      </div>

      {/* Three-column resizable layout */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup
          ref={panelGroupRef}
          orientation="horizontal"
          className="h-full"
          onLayout={(sizes) => saveLayout(sizes as [number, number, number])}
        >
          {/* LEFT — Match Explorer */}
          {!leftCollapsed && (
            <>
              <Panel defaultSize={defaultLayout[0]} minSize={16} maxSize={35}>
                <div className="flex h-full flex-col border-r border-white/5 overflow-hidden bg-[oklch(0.13_0.02_260)]/40">
                  <div className="border-b border-white/5 p-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-2">
                      Match Explorer
                    </div>
                    <div className="relative">
                      <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
                      <input
                        value={matchSearch}
                        onChange={(e) => setMatchSearch(e.target.value)}
                        placeholder="Filter matches…"
                        className="h-7 w-full rounded-md border border-white/5 bg-white/5 pl-7 pr-2 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/20"
                      />
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto py-1">
                    {filteredMatches.length === 0 ? (
                      <div className="flex flex-col items-center justify-center gap-3 px-4 py-10 text-center">
                        <div className="grid h-10 w-10 place-items-center rounded-full bg-white/5">
                          <Search className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div>
                          <div className="text-xs font-medium">No matches found</div>
                          <div className="mt-1 text-[10px] text-muted-foreground leading-relaxed">
                            No fixtures match <span className="font-mono text-foreground">"{matchSearch}"</span>.
                            Try a team name or competition.
                          </div>
                        </div>
                        <button
                          onClick={() => setMatchSearch("")}
                          className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                        >
                          Clear filter
                        </button>
                      </div>
                    ) : (
                      filteredMatches.map((m) => {
                        const active = selectedMatch.home === m.home && selectedMatch.away === m.away;
                        return (
                          <button
                            key={`${m.home}-${m.away}`}
                            onClick={() => setSelectedMatch(m)}
                            className={`w-full text-left px-3 py-2.5 transition-colors ${active ? "bg-primary/10" : "hover:bg-white/[0.03]"}`}
                          >
                            <div className="flex items-center justify-between gap-1 mb-0.5">
                              <span className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">{m.comp}</span>
                              <span className={`text-[9px] font-mono ${m.ko.includes("LIVE") ? "text-emerald" : "text-muted-foreground"}`}>{m.ko}</span>
                            </div>
                            <div className="text-xs font-medium leading-tight">
                              {m.home} <span className="text-muted-foreground">vs</span> {m.away}
                            </div>
                            <div className="mt-1 flex items-center gap-2">
                              <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                                <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${m.conf}%` }} />
                              </div>
                              <span className="font-mono text-[9px] text-muted-foreground">{m.conf}</span>
                              <span className="text-[9px] font-mono text-emerald">{m.ev}</span>
                            </div>
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              </Panel>
              <PanelResizeHandle className="w-px bg-white/5 hover:bg-primary/30 transition-colors cursor-col-resize" />
            </>
          )}

          {/* CENTER — Research Workspace */}
          <Panel
            defaultSize={
              leftCollapsed && rightCollapsed ? 100 :
              leftCollapsed ? defaultLayout[1] + defaultLayout[0] :
              rightCollapsed ? defaultLayout[1] + defaultLayout[2] :
              defaultLayout[1]
            }
            minSize={30}
          >
            <div className="flex h-full flex-col overflow-hidden">
              {/* Note tabs */}
              <div className="flex items-center gap-1 overflow-x-auto border-b border-white/5 bg-[oklch(0.13_0.02_260)]/40 px-3 py-2">
                {notes.map((note) => (
                  <button
                    key={note.id}
                    onClick={() => setActiveNote(note.id)}
                    className={`shrink-0 flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-colors ${
                      activeNote === note.id
                        ? "bg-primary/10 text-foreground border border-primary/20"
                        : "text-muted-foreground hover:bg-white/5 hover:text-foreground border border-transparent"
                    }`}
                  >
                    <StickyNote className="h-3 w-3" />
                    <span className="max-w-[140px] truncate">{note.title.split("—")[0].trim()}</span>
                  </button>
                ))}
                <button className="shrink-0 grid h-6 w-6 place-items-center rounded-md text-muted-foreground hover:bg-white/5 hover:text-foreground">
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Editor toolbar */}
              <div className="flex items-center gap-0.5 border-b border-white/5 px-3 py-1.5">
                <ToolbarButton icon={Bold}     label="Bold"      />
                <ToolbarButton icon={Italic}   label="Italic"    />
                <div className="mx-1.5 h-4 w-px bg-white/10" />
                <ToolbarButton icon={List}     label="List"      />
                <ToolbarButton icon={Code}     label="Code"      />
                <ToolbarButton icon={AlignLeft}label="Align"     />
                <div className="mx-1.5 h-4 w-px bg-white/10" />
                <ToolbarButton icon={RefreshCw}label="Sync with AI" />
                <div className="ml-auto flex items-center gap-1">
                  <ToolbarButton icon={Maximize2} label="Fullscreen" />
                </div>
              </div>

              {/* Editor area */}
              <div className="flex-1 overflow-y-auto p-5">
                <textarea
                  defaultValue={noteContent}
                  className="h-full w-full resize-none bg-transparent font-mono text-sm leading-relaxed text-foreground/90 focus:outline-none placeholder:text-muted-foreground"
                  spellCheck={false}
                />
              </div>

              {/* Editor footer */}
              <div className="flex items-center justify-between border-t border-white/5 px-4 py-2 text-[10px] text-muted-foreground">
                <div className="flex items-center gap-3">
                  <span>Markdown</span>
                  <span>·</span>
                  <span>Auto-saved 2m ago</span>
                </div>
                <div className="flex items-center gap-2">
                  <span>342 words</span>
                  <button className="inline-flex items-center gap-1 rounded border border-white/5 bg-white/5 px-1.5 py-0.5 hover:text-foreground">
                    <Save className="h-3 w-3" /> Save
                  </button>
                </div>
              </div>
            </div>
          </Panel>

          {/* RIGHT — Intelligence Panel */}
          {!rightCollapsed && (
            <>
              <PanelResizeHandle className="w-px bg-white/5 hover:bg-primary/30 transition-colors cursor-col-resize" />
              <Panel defaultSize={defaultLayout[2]} minSize={20} maxSize={45}>
                <div className="flex h-full flex-col overflow-hidden border-l border-white/5">
                  {/* Tabs */}
                  <div className="flex border-b border-white/5 shrink-0">
                    {(
                      [
                        { id: "signals",    label: "Signals",    icon: Target      },
                        { id: "discussion", label: "Discussion", icon: MessageSquare},
                        { id: "similar",    label: "Similar",    icon: History     },
                      ] as const
                    ).map(({ id, label, icon: Icon }) => (
                      <button
                        key={id}
                        onClick={() => setRightTab(id)}
                        className={`flex flex-1 items-center justify-center gap-1 py-2.5 text-[11px] font-medium transition-colors ${
                          rightTab === id
                            ? "border-b-2 border-primary text-foreground"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <Icon className="h-3 w-3" />
                        {label}
                      </button>
                    ))}
                  </div>

                  {/* Tab content */}
                  {rightTab === "signals" && <SignalsPanel match={selectedMatch} />}
                  {rightTab === "discussion" && <AiDiscussionPanel />}
                  {rightTab === "similar" && <SimilarMatchExplorer match={selectedMatch} />}
                </div>
              </Panel>
            </>
          )}
        </PanelGroup>
      </div>
    </div>
  );
}
