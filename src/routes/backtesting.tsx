import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard, SectionTitle } from "../components/titan/primitives";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/backtesting")({ component: BT });

const equity = Array.from({ length: 30 }, (_, i) => ({
  d: `D${i + 1}`,
  v: 10000 + Math.round(i * 180 + Math.sin(i / 2) * 400 + Math.random() * 300),
}));

function BT() {
  return (
    <PlaceholderPage eyebrow="Simulation" title="Backtesting" description="Reproducible historical simulations with closing-line value and slippage.">
      <GlassCard className="p-5">
        <SectionTitle title="Sample equity curve" description="Strategy: EV≥3 · Kelly 0.25 · 90-day window" />
        <div className="h-80">
          <ResponsiveContainer>
            <LineChart data={equity} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
              <XAxis dataKey="d" stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="oklch(0.68 0.02 250)" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "oklch(0.18 0.025 260)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="v" stroke="oklch(0.75 0.18 155)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </PlaceholderPage>
  );
}
