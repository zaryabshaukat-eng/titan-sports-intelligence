import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, StatCard } from "../components/titan/primitives";
import { Database, Layers, Calendar, HardDrive } from "lucide-react";

export const Route = createFileRoute("/historical-database")({ component: Hist });

function Hist() {
  return (
    <>
      <PageHeader eyebrow="Archive" title="Historical Database" description="Deep history across 30+ seasons and 200K+ fixtures." />
      <div className="grid gap-3 md:grid-cols-4">
        <StatCard label="Fixtures" value="214,382" icon={Database} />
        <StatCard label="Seasons Indexed" value="32" icon={Calendar} accent="emerald" />
        <StatCard label="Markets Archived" value="4.8M" icon={Layers} />
        <StatCard label="Storage" value="12.4 TB" icon={HardDrive} accent="warning" />
      </div>
      <GlassCard className="mt-4 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-white/5 bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Season</th>
              <th className="px-4 py-3 font-medium">Competition</th>
              <th className="px-4 py-3 font-medium">Matches</th>
              <th className="px-4 py-3 font-medium">Avg Goals</th>
              <th className="px-4 py-3 font-medium">Home Win %</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono">
            {[
              ["2024/25", "Premier League", 380, 2.84, 44.2],
              ["2024/25", "La Liga", 380, 2.61, 46.1],
              ["2024/25", "Serie A", 380, 2.72, 42.9],
              ["2023/24", "Bundesliga", 306, 3.21, 45.4],
              ["2023/24", "Champions League", 189, 3.04, 41.8],
              ["2022/23", "Premier League", 380, 2.85, 45.7],
              ["2022/23", "La Liga", 380, 2.51, 47.3],
            ].map((r, i) => (
              <tr key={i} className="hover:bg-white/[0.02]">
                {r.map((c, j) => <td key={j} className="px-4 py-3">{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>
    </>
  );
}
