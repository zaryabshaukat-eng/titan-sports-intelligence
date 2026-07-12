import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect } from "react";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, SectionTitle } from "../components/titan/primitives";
import { Badge, ProgressBar, StatusChip } from "../components/titan/ds";
import {
  FileText, Download, Maximize2, Minimize2, Printer, List,
  ChevronRight, ExternalLink, Clock, User, BarChart3, TrendingUp,
  Target, Activity, RefreshCw, BookOpen, ChevronDown, ChevronUp,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export const Route = createFileRoute("/reports")({ component: Reports });

/* ──────────── mock report data ──────────── */
const REPORT_LIST = [
  { id: "r1", title: "Weekly Intelligence Digest", period: "Week 41 — Jul 2026", size: "3.2 MB", author: "Titan AI", date: "Jul 12, 2026", status: "final" as const, sections: 6 },
  { id: "r2", title: "Model Calibration Report",   period: "Sep 2026",          size: "1.8 MB", author: "Statistical Engine", date: "Jul 10, 2026", status: "final" as const, sections: 4 },
  { id: "r3", title: "Market Movement Study",       period: "Q3 2026",          size: "5.7 MB", author: "Market Intelligence", date: "Jul 8, 2026", status: "draft" as const, sections: 8 },
  { id: "r4", title: "Backtest — EV≥3 Strategy",   period: "Rolling 90d",      size: "2.1 MB", author: "Backtesting Engine", date: "Jul 6, 2026", status: "final" as const, sections: 5 },
];

const evData = [
  { w: "Wk 35", ev: 4.1, baseline: 2.5 }, { w: "Wk 36", ev: 5.2, baseline: 2.5 },
  { w: "Wk 37", ev: 3.8, baseline: 2.5 }, { w: "Wk 38", ev: 6.4, baseline: 2.5 },
  { w: "Wk 39", ev: 7.1, baseline: 2.5 }, { w: "Wk 40", ev: 5.9, baseline: 2.5 },
  { w: "Wk 41", ev: 8.2, baseline: 2.5 },
];
const marketData = [
  { m: "1X2",     v: 342, arb: 12 }, { m: "O/U",     v: 289, arb: 8  },
  { m: "AH",      v: 214, arb: 19 }, { m: "BTTS",    v: 176, arb: 5  },
  { m: "Corners", v: 132, arb: 3  }, { m: "Cards",   v: 98,  arb: 2  },
];
const topBets = [
  { match: "Man City vs Arsenal",       market: "Over 2.5",     ev: "+6.8%", conf: 82, book: "Pinnacle", outcome: "Pending" },
  { match: "Real Madrid vs Barcelona",  market: "BTTS Yes",     ev: "+5.2%", conf: 78, book: "Bet365",   outcome: "Win" },
  { match: "Bayern vs Dortmund",        market: "AH -0.5",      ev: "+4.9%", conf: 74, book: "Betfair",  outcome: "Win" },
  { match: "Inter vs Juventus",         market: "Under 2.5",    ev: "+4.1%", conf: 71, book: "WH",       outcome: "Loss" },
  { match: "PSG vs Marseille",          market: "Home ML",      ev: "+3.8%", conf: 69, book: "Pinnacle", outcome: "Win" },
];
const engineHealth = [
  { name: "Statistical Engine", health: 96, requests: 61_440, latency: "312ms" },
  { name: "Market Intelligence",health: 98, requests: 48_200, latency: "241ms" },
  { name: "Historical Engine",   health: 94, requests: 29_100, latency: "198ms" },
  { name: "Consensus Engine",    health: 89, requests: 52_100, latency: "428ms" },
  { name: "Prediction Engine",   health: 74, requests: 18_900, latency: "621ms" },
];

const SECTIONS = [
  { id: "s1", title: "Executive Summary",        icon: BookOpen },
  { id: "s2", title: "Key Performance Metrics",  icon: BarChart3 },
  { id: "s3", title: "Expected Value Analysis",  icon: TrendingUp },
  { id: "s4", title: "Market Activity",          icon: Activity },
  { id: "s5", title: "Top Opportunities",        icon: Target },
  { id: "s6", title: "AI Engine Health",         icon: RefreshCw },
];

/* ──────────── Report Viewer component ──────────── */
function ReportViewer({ reportId, onClose }: { reportId: string; onClose: () => void }) {
  const report = REPORT_LIST.find((r) => r.id === reportId)!;
  const [fullscreen, setFullscreen] = useState(false);
  const [tocOpen, setTocOpen] = useState(true);
  const [activeSection, setActiveSection] = useState("s1");
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) setActiveSection(e.target.id); });
      },
      { rootMargin: "-30% 0px -60% 0px" }
    );
    Object.values(sectionRefs.current).forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    sectionRefs.current[id]?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handlePrint = () => window.print();

  const handleExport = () => {
    const data = JSON.stringify({ report: report.title, generated: new Date().toISOString(), sections: SECTIONS.map((s) => s.title) }, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${report.title.toLowerCase().replace(/\s+/g, "-")}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`flex flex-col ${fullscreen ? "fixed inset-0 z-[400] bg-[oklch(0.14_0.02_260)]" : ""}`}>
      {/* Viewer toolbar */}
      <div className="flex items-center gap-3 border-b border-white/5 bg-[oklch(0.13_0.02_260)]/80 backdrop-blur-sm px-5 py-3">
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-sm flex items-center gap-1">
          ← Reports
        </button>
        <div className="mx-2 h-4 w-px bg-white/10" />
        <div className="flex-1 min-w-0">
          <div className="font-display text-sm font-semibold truncate">{report.title}</div>
          <div className="text-[11px] text-muted-foreground">{report.period} · {report.author}</div>
        </div>
        <div className="flex items-center gap-1.5">
          <StatusChip status={report.status === "final" ? "online" : "beta"} label={report.status} />
          <button onClick={() => setTocOpen((v) => !v)} title="Toggle TOC" className="grid h-8 w-8 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground">
            <List className="h-3.5 w-3.5" />
          </button>
          <button onClick={handlePrint} title="Print" className="grid h-8 w-8 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground print:hidden">
            <Printer className="h-3.5 w-3.5" />
          </button>
          <button onClick={handleExport} title="Export JSON" className="inline-flex items-center gap-1.5 rounded-md border border-white/5 bg-white/5 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="h-3.5 w-3.5" /> Export
          </button>
          <button onClick={() => setFullscreen((v) => !v)} className="grid h-8 w-8 place-items-center rounded-md border border-white/5 bg-white/5 text-muted-foreground hover:text-foreground">
            {fullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* TOC sidebar */}
        {tocOpen && (
          <div className="w-52 shrink-0 border-r border-white/5 overflow-y-auto py-4 px-3 hidden md:block">
            <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/70 px-2 mb-3">
              Table of Contents
            </div>
            {SECTIONS.map((s, i) => {
              const Icon = s.icon;
              const active = activeSection === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => scrollTo(s.id)}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs transition-colors ${active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-white/5"}`}
                >
                  <span className="text-[10px] font-mono text-muted-foreground/50 w-4">{i + 1}</span>
                  <Icon className="h-3 w-3 shrink-0" />
                  <span className="truncate">{s.title}</span>
                  {active && <ChevronRight className="h-3 w-3 ml-auto shrink-0" />}
                </button>
              );
            })}
          </div>
        )}

        {/* Report content */}
        <div className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full print:px-0">

          {/* S1 — Executive Summary */}
          <div id="s1" ref={(el) => { sectionRefs.current["s1"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">01 — Executive Summary</div>
            <h2 className="font-display text-2xl font-bold mb-4">Weekly Intelligence Digest</h2>
            <div className="flex flex-wrap gap-3 mb-5 text-xs text-muted-foreground">
              <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{report.date}</span>
              <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{report.author}</span>
              <Badge variant="emerald">Final</Badge>
              <Badge variant="muted">{report.size}</Badge>
            </div>
            <div className="glass rounded-xl p-5 text-sm leading-relaxed text-muted-foreground space-y-3">
              <p>This digest covers intelligence activity for <strong className="text-foreground">Week 41 (July 6–12, 2026)</strong> across all Titan engines. The platform monitored <strong className="text-foreground">248 fixtures</strong>, generated <strong className="text-foreground">63 value signals</strong> (EV ≥ 3%), and identified <strong className="text-foreground">9 arbitrage opportunities</strong>.</p>
              <p>The Consensus Engine maintained an ensemble health score of <strong className="text-foreground">87.4%</strong>, with the Statistical Engine reporting the week's peak confidence on Man City vs Arsenal (Over 2.5, +6.8% EV). Closing-line value across settled bets averaged <strong className="text-foreground">+2.7%</strong>, confirming model edge retention.</p>
              <p>Notable: the Tactical Engine entered a training cycle on July 10, causing a temporary reduction in tactical signal weighting. Full capacity expected by July 15.</p>
            </div>
          </div>

          {/* S2 — KPIs */}
          <div id="s2" ref={(el) => { sectionRefs.current["s2"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">02 — Key Performance Metrics</div>
            <h2 className="font-display text-xl font-bold mb-4">Performance Overview</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 mb-4">
              <StatCard label="Fixtures Monitored" value="248" delta={{ value: "+12", positive: true }} icon={Activity} accent="primary" />
              <StatCard label="Value Signals"       value="63"  sub="EV ≥ 3%"                          icon={Target}   accent="emerald" />
              <StatCard label="Arbitrage Opps"      value="9"   sub="ROI 1.2–4.8%"                     icon={TrendingUp} accent="warning" />
              <StatCard label="Model Accuracy"      value="72.1%" delta={{ value: "+0.4%", positive: true }} icon={BarChart3} />
              <StatCard label="Avg CLV"             value="+2.7%" sub="settling bets"                  icon={Target}   accent="emerald" />
              <StatCard label="Ensemble Health"     value="87.4%" delta={{ value: "+1.6%", positive: true }} icon={RefreshCw} accent="primary" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <GlassCard className="p-4">
                <div className="text-xs text-muted-foreground mb-2">Win Rate (settled bets)</div>
                <ProgressBar value={72} label="Overall" variant="gradient" size="md" />
                <ProgressBar value={78} label="Value bets (EV≥3%)" variant="emerald" size="md" className="mt-3" />
                <ProgressBar value={81} label="High confidence (≥80)" variant="primary" size="md" className="mt-3" />
              </GlassCard>
              <GlassCard className="p-4">
                <div className="text-xs text-muted-foreground mb-2">Coverage by League</div>
                {[["Premier League",89],["La Liga",92],["Bundesliga",85],["Serie A",88],["Ligue 1",76]].map(([l,v]) => (
                  <ProgressBar key={String(l)} value={Number(v)} label={String(l)} size="sm" className="mt-2" />
                ))}
              </GlassCard>
            </div>
          </div>

          {/* S3 — EV Chart */}
          <div id="s3" ref={(el) => { sectionRefs.current["s3"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">03 — Expected Value Analysis</div>
            <h2 className="font-display text-xl font-bold mb-4">EV Trend — 7 Weeks</h2>
            <GlassCard className="p-5">
              <SectionTitle title="Average weekly EV vs baseline" description="Model edge vs 2.5% minimum threshold" />
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={evData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gEVr" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
                    <XAxis dataKey="w" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                    <Tooltip contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
                    <Area type="monotone" dataKey="ev" name="Avg EV" stroke="oklch(0.72 0.19 245)" strokeWidth={2} fill="url(#gEVr)" />
                    <Area type="monotone" dataKey="baseline" name="Baseline (2.5%)" stroke="oklch(1 0 0 / 0.3)" strokeWidth={1} strokeDasharray="4 4" fill="none" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>

          {/* S4 — Market Activity */}
          <div id="s4" ref={(el) => { sectionRefs.current["s4"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">04 — Market Activity</div>
            <h2 className="font-display text-xl font-bold mb-4">Signals by Market Type</h2>
            <GlassCard className="p-5">
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={marketData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
                    <XAxis dataKey="m" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
                    <Bar dataKey="v"   name="Value signals"  fill="oklch(0.72 0.19 245)" radius={[4,4,0,0]} />
                    <Bar dataKey="arb" name="Arbitrage opps" fill="oklch(0.75 0.18 155)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>

          {/* S5 — Top Opportunities */}
          <div id="s5" ref={(el) => { sectionRefs.current["s5"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">05 — Top Opportunities</div>
            <h2 className="font-display text-xl font-bold mb-4">Highest-EV Signals This Week</h2>
            <GlassCard className="overflow-hidden">
              <table className="w-full text-sm">
                <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {["Match","Market","EV","Confidence","Book","Outcome"].map((h) => (
                      <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {topBets.map((b) => (
                    <tr key={b.match} className="hover:bg-white/[0.025]">
                      <td className="px-4 py-3 font-medium">{b.match}</td>
                      <td className="px-4 py-3 text-muted-foreground">{b.market}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-emerald">{b.ev}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-1 w-16 overflow-hidden rounded-full bg-white/5">
                            <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${b.conf}%` }} />
                          </div>
                          <span className="font-mono text-xs text-muted-foreground">{b.conf}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{b.book}</td>
                      <td className="px-4 py-3">
                        <Badge variant={b.outcome === "Win" ? "emerald" : b.outcome === "Loss" ? "destructive" : "muted"}>
                          {b.outcome}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </GlassCard>
          </div>

          {/* S6 — AI Engine Health */}
          <div id="s6" ref={(el) => { sectionRefs.current["s6"] = el; }} className="mb-10 scroll-mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary mb-2">06 — AI Engine Health</div>
            <h2 className="font-display text-xl font-bold mb-4">Engine Status Summary</h2>
            <GlassCard className="overflow-hidden">
              <table className="w-full text-sm">
                <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {["Engine","Health","Requests (24h)","Latency"].map((h) => (
                      <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {engineHealth.map((e) => (
                    <tr key={e.name} className="hover:bg-white/[0.025]">
                      <td className="px-4 py-3 font-medium">{e.name}</td>
                      <td className="px-4 py-3 w-40">
                        <div className="flex items-center gap-2">
                          <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                            <div className={`h-full rounded-full ${e.health >= 90 ? "bg-emerald" : e.health >= 75 ? "bg-primary" : "bg-warning"}`} style={{ width: `${e.health}%` }} />
                          </div>
                          <span className="font-mono text-xs">{e.health}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{e.requests.toLocaleString()}</td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{e.latency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </GlassCard>

            <div className="mt-4 text-center text-xs text-muted-foreground">
              Report generated by Titan Intelligence OS · {report.date} · Confidential
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

/* ──────────── Reports list page ──────────── */
function Reports() {
  const [viewingId, setViewingId] = useState<string | null>(null);

  if (viewingId) {
    return <ReportViewer reportId={viewingId} onClose={() => setViewingId(null)} />;
  }

  return (
    <>
      <PageHeader
        eyebrow="Exports"
        title="Reports"
        description="Signed, versioned intelligence reports across all platform surfaces."
        actions={
          <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90">
            <FileText className="h-3.5 w-3.5" /> Generate Report
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        {REPORT_LIST.map((r) => (
          <GlassCard key={r.id} className="group flex flex-col gap-4 p-5 transition-all hover:border-white/15">
            <div className="flex items-start gap-3">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/5 text-primary">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="font-display text-sm font-semibold">{r.title}</div>
                  <Badge variant={r.status === "final" ? "emerald" : "warning"}>{r.status}</Badge>
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">{r.period}</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                { l: "Author",   v: r.author.split(" ")[0] },
                { l: "Sections", v: String(r.sections) },
                { l: "Size",     v: r.size },
              ].map((m) => (
                <div key={m.l} className="rounded-lg border border-white/5 bg-white/[0.02] py-2">
                  <div className="font-display text-sm font-bold">{m.v}</div>
                  <div className="text-[10px] text-muted-foreground">{m.l}</div>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-2 pt-1 border-t border-white/5">
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <Clock className="h-3 w-3" /> {r.date}
              </span>
              <div className="ml-auto flex items-center gap-2">
                <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                  <Download className="h-3.5 w-3.5" /> PDF
                </button>
                <button
                  onClick={() => setViewingId(r.id)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 border border-primary/20 px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                >
                  Open <ExternalLink className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </>
  );
}
