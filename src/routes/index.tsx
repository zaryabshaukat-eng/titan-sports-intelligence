import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import {
  Activity, Radio, Building2, LineChart as LineIcon, Target, Shuffle,
  Brain, History, Sparkles, Bell, Download, RefreshCw, ArrowUpRight,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";

export const Route = createFileRoute("/")({ component: Dashboard });

const evSeries = [
  { t: "00:00", ev: 2.1, model: 1.4 }, { t: "03:00", ev: 2.8, model: 1.7 },
  { t: "06:00", ev: 3.4, model: 2.1 }, { t: "09:00", ev: 4.1, model: 2.6 },
  { t: "12:00", ev: 5.7, model: 3.4 }, { t: "15:00", ev: 6.2, model: 4.1 },
  { t: "18:00", ev: 7.9, model: 5.2 }, { t: "21:00", ev: 8.4, model: 6.1 },
  { t: "Now",   ev: 9.1, model: 6.8 },
];
const marketBars = [
  { m: "1X2", v: 342 }, { m: "O/U", v: 289 }, { m: "AH", v: 214 },
  { m: "BTTS", v: 176 }, { m: "Corners", v: 132 }, { m: "Cards", v: 98 },
];

const opportunities = [
  { match: "Man City vs Arsenal", market: "Over 2.5", ev: "+6.8%", conf: 82, book: "Pinnacle" },
  { match: "Real Madrid vs Barcelona", market: "BTTS Yes", ev: "+5.2%", conf: 78, book: "Bet365" },
  { match: "Bayern vs Dortmund", market: "AH -0.5", ev: "+4.9%", conf: 74, book: "Betfair" },
  { match: "Inter vs Juventus", market: "Under 2.5", ev: "+4.1%", conf: 71, book: "William Hill" },
  { match: "PSG vs Marseille", market: "Home ML", ev: "+3.8%", conf: 69, book: "Pinnacle" },
];

const alerts = [
  { t: "2m ago", type: "Value", msg: "EV spike detected — Man City vs Arsenal (+6.8%)", level: "primary" },
  { t: "8m ago", type: "Arbitrage", msg: "3-way opportunity across Pinnacle / Bet365 / Betfair", level: "emerald" },
  { t: "14m ago", type: "Model", msg: "Confidence updated for Serie A slate (+2.1 pts)", level: "primary" },
  { t: "26m ago", type: "Market", msg: "Sharp money movement — Bayern -0.5 line", level: "warning" },
];

function Dashboard() {
  return (
    <>
      <PageHeader
        eyebrow="Command Center"
        title="Intelligence Dashboard"
        description="Real-time telemetry across markets, models, and opportunities."
        actions={
          <>
            <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
              <RefreshCw className="h-3.5 w-3.5" /> Sync
            </button>
            <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90">
              <Download className="h-3.5 w-3.5" /> Export
            </button>
          </>
        }
      />

      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <StatCard label="Today's Matches" value="248" delta={{ value: "+12", positive: true }} icon={Activity} />
        <StatCard label="Live Matches" value="37" sub="8 in stoppage" icon={Radio} accent="emerald" />
        <StatCard label="Bookmakers" value="42" sub="41 online · 1 degraded" icon={Building2} />
        <StatCard label="Markets Monitored" value="18.4K" delta={{ value: "+3.2%", positive: true }} icon={LineIcon} />
        <StatCard label="Value Opportunities" value="63" sub="EV ≥ 3%" icon={Target} accent="emerald" />
        <StatCard label="Arbitrage" value="9" sub="ROI 1.2 – 4.8%" icon={Shuffle} accent="warning" />
        <StatCard label="Model Confidence" value="87.4%" delta={{ value: "+1.6%", positive: true }} icon={Brain} accent="primary" />
        <StatCard label="Historical Accuracy" value="72.1%" sub="rolling 90d" icon={History} />
        <StatCard label="Expected Value" value="+£24.7K" delta={{ value: "+8.4%", positive: true }} icon={Sparkles} accent="emerald" />
        <StatCard label="Today's Alerts" value="128" sub="12 high priority" icon={Bell} accent="warning" />
      </div>

      {/* Charts row */}
      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <GlassCard className="p-5 xl:col-span-2">
          <SectionTitle
            title="Expected Value flow"
            description="24h EV surface vs model consensus"
            action={<StatusPill status="online" label="Live" />}
          />
          <div className="h-72">
            <ResponsiveContainer>
              <AreaChart data={evSeries} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="gEv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gMd" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
                <XAxis dataKey="t" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "oklch(0.97 0 0)" }}
                />
                <Area type="monotone" dataKey="ev" stroke="oklch(0.72 0.19 245)" strokeWidth={2} fill="url(#gEv)" />
                <Area type="monotone" dataKey="model" stroke="oklch(0.75 0.18 155)" strokeWidth={2} fill="url(#gMd)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <SectionTitle title="Model confidence" description="Cross-engine consensus" />
          <div className="relative grid h-48 place-items-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart innerRadius="70%" outerRadius="100%" data={[{ name: "conf", value: 87.4, fill: "oklch(0.72 0.19 245)" }]} startAngle={90} endAngle={-270}>
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar background={{ fill: "oklch(1 0 0 / 0.05)" }} dataKey="value" cornerRadius={20} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute text-center">
              <div className="font-display text-3xl font-bold">87.4%</div>
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Consensus</div>
            </div>
          </div>
          <div className="mt-4 space-y-2 text-xs">
            {[
              { l: "Statistical Engine", v: 91 },
              { l: "Market Engine", v: 84 },
              { l: "Tactical Engine", v: 79 },
              { l: "Historical Engine", v: 88 },
            ].map((r) => (
              <div key={r.l}>
                <div className="mb-1 flex justify-between">
                  <span className="text-muted-foreground">{r.l}</span>
                  <span className="font-mono">{r.v}%</span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${r.v}%` }} />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Row 3 */}
      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <GlassCard className="p-5 xl:col-span-2">
          <SectionTitle
            title="Top value opportunities"
            description="Filtered by EV ≥ 3% and confidence ≥ 65"
            action={<a className="inline-flex items-center gap-1 text-xs text-primary hover:underline" href="/value-analysis">View all <ArrowUpRight className="h-3 w-3" /></a>}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 font-medium">Match</th>
                  <th className="pb-3 font-medium">Market</th>
                  <th className="pb-3 font-medium">EV</th>
                  <th className="pb-3 font-medium">Confidence</th>
                  <th className="pb-3 font-medium">Best Book</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {opportunities.map((o) => (
                  <tr key={o.match} className="hover:bg-white/[0.02]">
                    <td className="py-3 font-medium">{o.match}</td>
                    <td className="py-3 text-muted-foreground">{o.market}</td>
                    <td className="py-3 font-mono text-emerald">{o.ev}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1 w-16 overflow-hidden rounded-full bg-white/5">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${o.conf}%` }} />
                        </div>
                        <span className="font-mono text-xs text-muted-foreground">{o.conf}</span>
                      </div>
                    </td>
                    <td className="py-3 text-muted-foreground">{o.book}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <SectionTitle title="Market activity" description="Signals by market type" />
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={marketBars} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
                <XAxis dataKey="m" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="v" fill="oklch(0.72 0.19 245)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* Alerts row */}
      <div className="mt-4">
        <GlassCard className="p-5">
          <SectionTitle
            title="Latest alerts"
            description="Streaming from all engines"
            action={<a className="inline-flex items-center gap-1 text-xs text-primary hover:underline" href="/alerts">Open alert center <ArrowUpRight className="h-3 w-3" /></a>}
          />
          <div className="space-y-2">
            {alerts.map((a, i) => {
              const styles = {
                primary: "bg-primary/10 text-primary",
                emerald: "bg-emerald/10 text-emerald",
                warning: "bg-warning/10 text-warning",
              }[a.level as "primary" | "emerald" | "warning"];
              const text = {
                primary: "text-primary",
                emerald: "text-emerald",
                warning: "text-warning",
              }[a.level as "primary" | "emerald" | "warning"];
              return (
                <div key={i} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
                  <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-md ${styles}`}>
                    <Bell className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-semibold uppercase tracking-wider ${text}`}>{a.type}</span>
                      <span className="text-[10px] text-muted-foreground">{a.t}</span>
                    </div>
                    <div className="truncate text-sm">{a.msg}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      </div>
    </>
  );
}
