import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, SectionTitle } from "../components/titan/primitives";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/market-intelligence")({ component: MI });

const data = Array.from({ length: 24 }, (_, i) => ({
  h: `${i}h`,
  sharp: 40 + Math.round(Math.sin(i / 3) * 15 + Math.random() * 8),
  public: 60 + Math.round(Math.cos(i / 4) * 12 + Math.random() * 6),
}));

function MI() {
  return (
    <>
      <PageHeader eyebrow="Flow Analytics" title="Market Intelligence" description="Line movement, sharp flow, and consensus deviation across 42 books." />
      <GlassCard className="p-5">
        <SectionTitle title="Sharp vs public money" description="24h percentage split, weighted by liquidity" />
        <div className="h-80">
          <ResponsiveContainer>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0.4} /><stop offset="100%" stopColor="oklch(0.72 0.19 245)" stopOpacity={0} /></linearGradient>
                <linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0.4} /><stop offset="100%" stopColor="oklch(0.75 0.18 155)" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
              <XAxis dataKey="h" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }} />
              <Area type="monotone" dataKey="sharp" stroke="oklch(0.72 0.19 245)" strokeWidth={2} fill="url(#s)" />
              <Area type="monotone" dataKey="public" stroke="oklch(0.75 0.18 155)" strokeWidth={2} fill="url(#p)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </>
  );
}
