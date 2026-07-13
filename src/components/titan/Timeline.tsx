import { useState, useMemo, memo } from "react";
import {
  TrendingUp, Brain, FlaskConical, Cpu, Bell, CheckCircle2,
  BookOpen, ChevronDown, ChevronRight, Filter, Calendar,
  ArrowUpRight, ArrowDownRight, Minus,
} from "lucide-react";

export type TimelineEventType =
  | "odds" | "prediction" | "research" | "model" | "alert" | "result" | "learning";

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: string;   // ISO string or readable label
  meta?: string;       // e.g. match name, engine name
  value?: string;      // e.g. "+6.8%", "87%"
  direction?: "up" | "down" | "flat";
  tags?: string[];
}

const TYPE_CONFIG: Record<TimelineEventType, {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
  label: string;
  dotColor: string;
}> = {
  odds:       { icon: TrendingUp,    color: "text-emerald",     bg: "bg-emerald/10",     label: "Odds Movement",     dotColor: "bg-emerald" },
  prediction: { icon: Brain,         color: "text-primary",     bg: "bg-primary/10",     label: "Prediction",        dotColor: "bg-primary" },
  research:   { icon: FlaskConical,  color: "text-warning",     bg: "bg-warning/10",     label: "Research",          dotColor: "bg-warning" },
  model:      { icon: Cpu,           color: "text-primary",     bg: "bg-primary/10",     label: "Model Update",      dotColor: "bg-primary" },
  alert:      { icon: Bell,          color: "text-destructive", bg: "bg-destructive/10", label: "Alert",             dotColor: "bg-destructive" },
  result:     { icon: CheckCircle2,  color: "text-emerald",     bg: "bg-emerald/10",     label: "Result",            dotColor: "bg-emerald" },
  learning:   { icon: BookOpen,      color: "text-warning",     bg: "bg-warning/10",     label: "Learning Event",    dotColor: "bg-warning" },
};

const ALL_TYPES: TimelineEventType[] = ["odds","prediction","research","model","alert","result","learning"];

/* ─────────── Sample data ─────────── */
export const SAMPLE_TIMELINE: TimelineEvent[] = [
  { id:"t1",  type:"odds",       title:"Line moved on Man City -1 AH",       description:"Sharp money confirmed across Pinnacle / Bet365 / Betfair. Moved from -1.1 to -0.9.",                          timestamp:"2 min ago",  meta:"Man City vs Arsenal",    value:"-0.20", direction:"down",  tags:["Premier League","AH"] },
  { id:"t2",  type:"prediction", title:"Over 2.5 probability updated",        description:"Statistical Engine recalibrated: 74% → 82% after xG trajectory revision.",                                   timestamp:"8 min ago",  meta:"Man City vs Arsenal",    value:"82%",   direction:"up",   tags:["O/U","Premier League"] },
  { id:"t3",  type:"alert",      title:"EV spike ≥ 5% detected",             description:"Closing-line value exceeds model threshold. Recommend action before line tightens.",                          timestamp:"14 min ago", meta:"Over 2.5 — Pinnacle",    value:"+6.8%", direction:"up",   tags:["EV","Urgent"] },
  { id:"t4",  type:"research",   title:"Pre-match note saved",               description:"Analyst saved research note: H2H trend, xG comparison, lineup impact.",                                        timestamp:"22 min ago", meta:"Man City vs Arsenal",    tags:["Note"] },
  { id:"t5",  type:"model",      title:"Consensus weights rebalanced",        description:"Ensemble weights updated: Statistical +4%, Market -2%, Tactical -2% (training).",                             timestamp:"1h ago",     meta:"Consensus Engine v5.0.1",tags:["Config"] },
  { id:"t6",  type:"result",     title:"Real Madrid 2-1 Barcelona — Final",  description:"Result confirmed. Prediction: Real Madrid ML (correct). CLV: +3.2%. Model accuracy maintained.",              timestamp:"2h ago",     meta:"La Liga",                value:"+3.2%", direction:"up",   tags:["La Liga","Correct"] },
  { id:"t7",  type:"learning",   title:"Model ingested result data",         description:"Historical Engine updated with 12 new La Liga fixtures. Pattern index rebuilt.",                               timestamp:"2h ago",     meta:"Historical Engine",      tags:["Training"] },
  { id:"t8",  type:"odds",       title:"BTTS Yes drifted from 1.68 → 1.74", description:"Market showing lack of confidence. Rechecking model fair-line assumptions.",                                   timestamp:"3h ago",     meta:"Real Madrid vs Barcelona",value:"+0.06",direction:"up",   tags:["La Liga","BTTS"] },
  { id:"t9",  type:"prediction", title:"Bayern -0.5 confidence: 74%",       description:"Tactical Engine complete. Formation analysis complete. Model consensus 74%.",                                   timestamp:"4h ago",     meta:"Bayern vs Dortmund",     value:"74%",   tags:["Bundesliga"] },
  { id:"t10", type:"model",      title:"Tactical Engine v2.1 deployed",     description:"New version with 2024-25 formation data. Training accuracy: 78.4%. Gradual weight rollout.",                   timestamp:"5h ago",     meta:"Tactical Engine",        tags:["Deploy"] },
  { id:"t11", type:"alert",      title:"Arbitrage: Pinnacle / Bet365 / WH", description:"3-way opportunity across 3 books. ROI: 2.4%. Window: ~8 min remaining before lines converge.",               timestamp:"Yesterday",  meta:"Inter vs Juventus",      value:"2.4%",  direction:"up",   tags:["Arb","Serie A"] },
  { id:"t12", type:"result",     title:"Backtesting complete — Q2 2024",    description:"847 fixtures. Net ROI: +11.4%. Calibration score: 0.84. Sharpe: 2.1. Report generated.",                      timestamp:"Yesterday",  meta:"Backtesting Engine",     value:"+11.4%",direction:"up",   tags:["Backtest"] },
  { id:"t13", type:"research",   title:"UCL R16 pattern summary published", description:"Deep analysis of last 6 Champions League R16 matchups with home advantage metrics.",                           timestamp:"Yesterday",  meta:"Champions League",       tags:["Report","UCL"] },
  { id:"t14", type:"learning",   title:"Bundesliga Q3 dataset ingested",    description:"14 new matches added to historical index. Pressure metric recalculated for 8 teams.",                          timestamp:"2 days ago", meta:"Historical Engine",      tags:["Training","Bundesliga"] },
  { id:"t15", type:"model",      title:"Statistical Engine v4.1.0 released",description:"Improved Dixon-Coles decay parameter. Home advantage coefficient updated for 12 leagues.",                     timestamp:"2 days ago", meta:"Statistical Engine",     tags:["Release"] },
];

/* ─────────── TimelineItem ─────────── */
function TimelineItem({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = TYPE_CONFIG[event.type];
  const Icon = cfg.icon;

  const directionIcon = event.direction === "up"   ? <ArrowUpRight className="h-3 w-3 text-emerald" /> :
                        event.direction === "down"  ? <ArrowDownRight className="h-3 w-3 text-destructive" /> :
                        event.direction === "flat"  ? <Minus className="h-3 w-3 text-muted-foreground" /> : null;

  return (
    <div className="relative flex gap-4">
      {/* Spine line */}
      {!isLast && (
        <div className="absolute left-5 top-10 w-px bg-white/[0.06] h-full" />
      )}

      {/* Dot + icon */}
      <div className="relative flex-none mt-1">
        <div className={`grid h-10 w-10 place-items-center rounded-full border border-white/10 ${cfg.bg} ${cfg.color} z-10 relative`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 pb-6`}>
        <button
          onClick={() => event.description && setExpanded((v) => !v)}
          className="w-full text-left group"
        >
          <div className="flex items-start gap-2 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-[10px] font-semibold uppercase tracking-wider ${cfg.color}`}>{cfg.label}</span>
                {event.meta && (
                  <span className="text-[10px] text-muted-foreground">· {event.meta}</span>
                )}
                <span className="text-[10px] text-muted-foreground ml-auto">{event.timestamp}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-2">
                <span className="text-sm font-medium group-hover:text-primary transition-colors">
                  {event.title}
                </span>
                {event.value && (
                  <span className={`inline-flex items-center gap-0.5 font-mono text-xs font-semibold ${
                    event.direction === "up"   ? "text-emerald" :
                    event.direction === "down" ? "text-destructive" : "text-muted-foreground"
                  }`}>
                    {directionIcon}{event.value}
                  </span>
                )}
              </div>
            </div>
            {event.description && (
              <div className="text-muted-foreground mt-1">
                {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
              </div>
            )}
          </div>

          {/* Tags */}
          {event.tags && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {event.tags.map((t) => (
                <span key={t} className="rounded-full border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-muted-foreground">
                  {t}
                </span>
              ))}
            </div>
          )}
        </button>

        {/* Expanded description */}
        {expanded && event.description && (
          <div className="mt-2 rounded-lg border border-white/5 bg-white/[0.025] px-3 py-2.5 text-xs text-muted-foreground leading-relaxed">
            {event.description}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─────────── Timeline (main export) ─────────── */
export interface TimelineProps {
  events?: TimelineEvent[];
  showFilters?: boolean;
  showGrouping?: boolean;
  maxHeight?: string;
}

export const Timeline = memo(function Timeline({
  events = SAMPLE_TIMELINE,
  showFilters = true,
  showGrouping = true,
  maxHeight = "none",
}: TimelineProps) {
  const [activeTypes, setActiveTypes] = useState<Set<TimelineEventType>>(new Set(ALL_TYPES));
  const [groupBy, setGroupBy] = useState<"none" | "time" | "type">("time");

  const toggleType = (t: TimelineEventType) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(t)) { if (next.size > 1) next.delete(t); }
      else next.add(t);
      return next;
    });
  };

  const filtered = useMemo(
    () => events.filter((e) => activeTypes.has(e.type)),
    [events, activeTypes]
  );

  // Group by time bucket
  const groups = useMemo(() => {
    if (groupBy === "none") return [{ label: "", items: filtered }];
    if (groupBy === "type") {
      return ALL_TYPES
        .filter((t) => activeTypes.has(t))
        .map((t) => ({ label: TYPE_CONFIG[t].label, items: filtered.filter((e) => e.type === t) }))
        .filter((g) => g.items.length > 0);
    }
    // time grouping
    const buckets: Record<string, TimelineEvent[]> = {};
    filtered.forEach((e) => {
      const bucket =
        e.timestamp.includes("min") || e.timestamp === "just now" || e.timestamp.includes("hr") || e.timestamp.includes("h ago")
          ? "Today"
          : e.timestamp === "Yesterday"
          ? "Yesterday"
          : "Earlier";
      (buckets[bucket] ??= []).push(e);
    });
    return (["Today","Yesterday","Earlier"] as const)
      .filter((b) => buckets[b]?.length)
      .map((b) => ({ label: b, items: buckets[b] }));
  }, [filtered, groupBy, activeTypes]);

  return (
    <div className="flex flex-col gap-4">
      {showFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          {ALL_TYPES.map((t) => {
            const cfg = TYPE_CONFIG[t];
            const active = activeTypes.has(t);
            return (
              <button
                key={t}
                onClick={() => toggleType(t)}
                className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider transition-colors ${
                  active
                    ? `${cfg.bg} ${cfg.color} border-transparent`
                    : "border-white/5 bg-white/[0.02] text-muted-foreground hover:border-white/10"
                }`}
              >
                <cfg.icon className="h-2.5 w-2.5" />
                {cfg.label}
              </button>
            );
          })}
          {showGrouping && (
            <div className="ml-auto flex items-center gap-1 rounded-md border border-white/5 bg-white/5 p-0.5 text-[10px]">
              {(["none","time","type"] as const).map((g) => (
                <button
                  key={g}
                  onClick={() => setGroupBy(g)}
                  className={`rounded px-2 py-1 transition-colors capitalize ${groupBy === g ? "bg-white/10 text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                >
                  {g === "none" ? "All" : g}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={maxHeight !== "none" ? { maxHeight, overflowY: "auto" } : undefined}>
        {groups.map((group) => (
          <div key={group.label} className="mb-2">
            {group.label && showGrouping && (
              <div className="mb-3 flex items-center gap-3">
                <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                  {group.label}
                </span>
                <div className="flex-1 h-px bg-white/[0.06]" />
                <span className="text-[10px] text-muted-foreground">{group.items.length} events</span>
              </div>
            )}
            {group.items.map((event, i) => (
              <TimelineItem key={event.id} event={event} isLast={i === group.items.length - 1} />
            ))}
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-white/5">
              <Calendar className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <div className="text-sm font-medium">No events match your filters</div>
              <div className="text-xs text-muted-foreground mt-1">Try enabling more event types above.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
