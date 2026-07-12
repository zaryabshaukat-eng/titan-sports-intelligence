import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatusPill, SectionTitle } from "../components/titan/primitives";
import {
  LineChart, Database, History, Swords, ShieldAlert, Layers,
  MessageSquareCode, Sparkles, Rewind, ArrowRight,
} from "lucide-react";

export const Route = createFileRoute("/ai-intelligence")({ component: AIPage });

type Engine = {
  name: string; desc: string; icon: React.ComponentType<{ className?: string }>;
  status: "online" | "training" | "idle" | "beta"; health: number;
};
const engines: Engine[] = [
  { name: "Market Intelligence Engine", desc: "Cross-book line movement, sharp flow detection, and consensus modelling.", icon: LineChart, status: "online", health: 98 },
  { name: "Statistical Engine", desc: "Poisson, Dixon-Coles, xG/xGA regression and generalized team strength models.", icon: Database, status: "online", health: 96 },
  { name: "Historical Engine", desc: "Deep-history pattern matching across 30+ seasons and 200K+ fixtures.", icon: History, status: "online", health: 94 },
  { name: "Tactical Engine", desc: "Formation, pressing intensity, and matchup mismatch analysis.", icon: Swords, status: "training", health: 71 },
  { name: "Risk Engine", desc: "Bankroll modelling, Kelly sizing, drawdown & correlation risk.", icon: ShieldAlert, status: "online", health: 92 },
  { name: "Consensus Engine", desc: "Ensembles across all engines with dynamic weighting.", icon: Layers, status: "online", health: 89 },
  { name: "Explainability Engine", desc: "SHAP-style attribution and natural-language rationale for every signal.", icon: MessageSquareCode, status: "beta", health: 68 },
  { name: "Prediction Engine", desc: "Calibrated probability outputs across all supported markets.", icon: Sparkles, status: "training", health: 74 },
  { name: "Backtesting Engine", desc: "Reproducible historical simulations with slippage and closing-line value.", icon: Rewind, status: "online", health: 90 },
];

function AIPage() {
  return (
    <>
      <PageHeader
        eyebrow="Neural Fabric"
        title="AI Intelligence"
        description="The Titan intelligence stack — nine engines converging into a single decision surface."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {engines.map((e) => (
          <GlassCard key={e.name} className="group relative overflow-hidden p-5 transition-all hover:border-white/15">
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br from-primary/20 to-emerald/10 opacity-40 blur-2xl transition-opacity group-hover:opacity-70" />
            <div className="relative">
              <div className="flex items-start justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-lg border border-white/10 bg-white/5 text-primary">
                  <e.icon className="h-5 w-5" />
                </div>
                <StatusPill status={e.status} />
              </div>
              <h3 className="mt-4 font-display text-base font-semibold">{e.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{e.desc}</p>

              <div className="mt-5">
                <div className="mb-1 flex justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
                  <span>Engine health</span>
                  <span className="font-mono text-foreground">{e.health}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary to-emerald" style={{ width: `${e.health}%` }} />
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-xs">
                <span className="text-muted-foreground">Connection: <span className="font-mono text-foreground">engine.{e.name.split(" ")[0].toLowerCase()}.v1</span></span>
                <button className="inline-flex items-center gap-1 text-primary hover:underline">Configure <ArrowRight className="h-3 w-3" /></button>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <GlassCard className="mt-6 p-5">
        <SectionTitle title="Extension surface" description="Every engine exposes a strict service contract, ready to bind to production intelligence." />
        <div className="grid gap-3 md:grid-cols-3">
          {["Signal ingest → /engines/*/ingest", "Inference → /engines/*/infer", "Explainability → /engines/*/explain"].map((t) => (
            <div key={t} className="rounded-lg border border-white/5 bg-white/[0.02] p-3 font-mono text-xs text-muted-foreground">
              {t}
            </div>
          ))}
        </div>
      </GlassCard>
    </>
  );
}
