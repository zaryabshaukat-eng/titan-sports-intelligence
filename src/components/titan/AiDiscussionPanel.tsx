/**
 * AI Discussion Panel
 *
 * Shows a placeholder conversation between Titan intelligence engines,
 * visualising how they collaborate to reach a consensus recommendation.
 * No real AI yet — pure UI scaffold for future engine integration.
 */

import { useState } from "react";
import { Brain, LineChart, ShieldAlert, Layers, Database, Swords, RefreshCw } from "lucide-react";
import { StatusPill } from "./primitives";

interface Message {
  engine: string;
  role: "market" | "statistical" | "risk" | "historical" | "tactical" | "consensus";
  content: string;
  time: string;
  confidence?: number;
  tags?: string[];
}

const ENGINE_META = {
  market: {
    icon: LineChart,
    color: "text-emerald",
    bg: "bg-emerald/10",
    border: "border-emerald/20",
    dot: "bg-emerald",
  },
  statistical: {
    icon: Brain,
    color: "text-primary",
    bg: "bg-primary/10",
    border: "border-primary/20",
    dot: "bg-primary",
  },
  risk: {
    icon: ShieldAlert,
    color: "text-warning",
    bg: "bg-warning/10",
    border: "border-warning/20",
    dot: "bg-warning",
  },
  historical: {
    icon: Database,
    color: "text-primary",
    bg: "bg-primary/5",
    border: "border-primary/10",
    dot: "bg-primary",
  },
  tactical: {
    icon: Swords,
    color: "text-muted-foreground",
    bg: "bg-white/5",
    border: "border-white/10",
    dot: "bg-muted-foreground",
  },
  consensus: {
    icon: Layers,
    color: "text-emerald",
    bg: "bg-emerald/10",
    border: "border-emerald/20",
    dot: "bg-emerald animate-pulse",
  },
};

const THREAD_MAN_CITY: Message[] = [
  {
    engine: "Market Engine",
    role: "market",
    content:
      "Sharp movement detected on Man City vs Arsenal. Over 2.5 line shifted from 1.92 → 1.85 across Pinnacle, Betfair, and Bet365 in the last 40 minutes. Steam move pattern confirmed — coordinated sharp action.",
    time: "4m ago",
    confidence: 91,
    tags: ["Line movement", "Sharp money"],
  },
  {
    engine: "Statistical Engine",
    role: "statistical",
    content:
      "Historical trend supports home side. Man City averaging 2.4 xG over last 6 Premier League home fixtures; Arsenal's defensive shape concedes 1.3 xGA away. Dixon-Coles model assigns 71% probability to Over 2.5 at Etihad.",
    time: "3m 44s ago",
    confidence: 87,
    tags: ["xG", "Dixon-Coles"],
  },
  {
    engine: "Historical Engine",
    role: "historical",
    content:
      "Pattern matched 847 analogous fixtures across 30 seasons. In meetings where xG differential ≥ 0.8 and sharp money confirmed line movement, Over 2.5 settled at a 73% rate. Closing-line value averaged +2.9% in this cohort.",
    time: "3m 21s ago",
    confidence: 84,
    tags: ["Pattern match", "847 fixtures"],
  },
  {
    engine: "Tactical Engine",
    role: "tactical",
    content:
      "⚠ Note: currently in training cycle — formation signal weighted at 60% capacity. Preliminary read: Arsenal pressing with PPDA 8.2 (highest in division), likely to push City into high-press exchanges. This inflates chance volume for both sides.",
    time: "2m 55s ago",
    confidence: 61,
    tags: ["PPDA", "Training mode"],
  },
  {
    engine: "Risk Engine",
    role: "risk",
    content:
      "Lineup uncertainty flag raised. Haaland listed as doubtful (training report, 6am). If confirmed absent, model edge for Over 2.5 reduces from +6.8% → +2.1%. Recommend holding stake until confirmed XI, or applying 0.6× Kelly fraction now.",
    time: "2m 18s ago",
    confidence: 79,
    tags: ["Lineup risk", "Kelly adjustment"],
  },
  {
    engine: "Consensus Engine",
    role: "consensus",
    content:
      "Ensemble confidence adjusted to 82 (↓ from 87 pending lineup confirmation). Weighted recommendation: HOLD — await official lineup. If Haaland starts, execute at current odds (1.85). If absent, reassess against revised fair line of 1.81. EV edge remains positive in both scenarios.",
    time: "1m 52s ago",
    confidence: 82,
    tags: ["Consensus", "Recommendation"],
  },
];

const THREAD_BUNDESLIGA: Message[] = [
  {
    engine: "Market Engine",
    role: "market",
    content:
      "Bayern vs Dortmund Asian Handicap -0.5 line stable across all major books. No significant sharp movement in past 2h. Public money 68% on Bayern, typical for this fixture.",
    time: "11m ago",
    confidence: 72,
    tags: ["AH -0.5", "No steam"],
  },
  {
    engine: "Statistical Engine",
    role: "statistical",
    content:
      "Bayern xG dominance at Allianz Arena: 2.8 avg over last 8 home Bundesliga matches vs Dortmund's 1.1 xGA away. Model implies 74% win probability for Bayern, fair line -0.5 at 1.91. Current best available 1.95 — marginal edge only.",
    time: "10m 30s ago",
    confidence: 74,
    tags: ["xG", "Home dominance"],
  },
  {
    engine: "Risk Engine",
    role: "risk",
    content:
      "Thin edge flag. At +2.1% EV the Kelly fraction is 1.2% — below minimum threshold for active recommendation. No action warranted unless line lengthens to 2.00+.",
    time: "9m ago",
    confidence: 68,
    tags: ["Thin edge", "Below threshold"],
  },
  {
    engine: "Consensus Engine",
    role: "consensus",
    content:
      "Consensus: PASS. Insufficient edge to warrant a position. Monitor for line movement — a move to 2.00 would upgrade to WATCH status. Ticket back on next market scan in 30 minutes.",
    time: "8m 12s ago",
    confidence: 68,
    tags: ["Consensus", "Pass"],
  },
];

const THREADS = [
  { id: "man-city", label: "Man City vs Arsenal", messages: THREAD_MAN_CITY, status: "online" as const },
  { id: "bundesliga", label: "Bayern vs Dortmund", messages: THREAD_BUNDESLIGA, status: "idle" as const },
];

function MessageBubble({ msg }: { msg: Message }) {
  const meta = ENGINE_META[msg.role];
  const Icon = meta.icon;
  const isConsensus = msg.role === "consensus";

  return (
    <div className={`relative ${isConsensus ? "mt-1" : ""}`}>
      {isConsensus && (
        <div className="mb-2 flex items-center gap-2">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-emerald/30 to-transparent" />
          <span className="text-[9px] font-semibold uppercase tracking-[0.2em] text-emerald/70">Consensus Reached</span>
          <div className="h-px flex-1 bg-gradient-to-r from-emerald/30 via-transparent to-transparent" />
        </div>
      )}
      <div className={`rounded-xl border p-3 ${meta.border} ${meta.bg} ${isConsensus ? "ring-1 ring-emerald/20" : ""}`}>
        {/* Header */}
        <div className="mb-2 flex items-center gap-2">
          <div className={`grid h-6 w-6 shrink-0 place-items-center rounded-md border ${meta.border} bg-white/5 ${meta.color}`}>
            <Icon className="h-3 w-3" />
          </div>
          <span className={`text-[10px] font-bold uppercase tracking-wider ${meta.color}`}>{msg.engine}</span>
          <span className="ml-auto shrink-0 font-mono text-[9px] text-muted-foreground">{msg.time}</span>
        </div>

        {/* Body */}
        <p className="text-xs leading-relaxed text-foreground/80">{msg.content}</p>

        {/* Footer */}
        {(msg.confidence !== undefined || msg.tags?.length) && (
          <div className="mt-2.5 flex items-center gap-2 flex-wrap">
            {msg.confidence !== undefined && (
              <div className="flex items-center gap-1.5">
                <div className="h-1 w-16 overflow-hidden rounded-full bg-white/10">
                  <div
                    className={`h-full rounded-full ${meta.dot.replace("animate-pulse", "")}`}
                    style={{ width: `${msg.confidence}%` }}
                  />
                </div>
                <span className={`font-mono text-[9px] ${meta.color}`}>{msg.confidence}</span>
              </div>
            )}
            {msg.tags?.map((tag) => (
              <span key={tag} className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[9px] text-muted-foreground">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function AiDiscussionPanel() {
  const [activeThread, setActiveThread] = useState(THREADS[0].id);
  const thread = THREADS.find((t) => t.id === activeThread)!;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Thread selector */}
      <div className="border-b border-white/5 px-3 py-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 mb-2">
          AI Discussion
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {THREADS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveThread(t.id)}
              className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
                activeThread === t.id
                  ? "bg-primary/10 text-foreground border border-primary/20"
                  : "text-muted-foreground hover:bg-white/5 border border-transparent"
              }`}
            >
              <StatusPill status={t.status} />
              <span className="truncate max-w-[100px]">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mx-3 mt-3 mb-1 flex items-start gap-1.5 rounded-md border border-warning/20 bg-warning/5 px-2.5 py-2">
        <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" />
        <p className="text-[9px] leading-relaxed text-warning/80">
          Placeholder UI — no real AI connected. Engine responses are simulated for interface development.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {thread.messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
      </div>

      {/* Footer */}
      <div className="border-t border-white/5 px-3 py-2">
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <RefreshCw className="h-3 w-3" />
          <span>Discussion refreshes when engines update consensus</span>
        </div>
      </div>
    </div>
  );
}
