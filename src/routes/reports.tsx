import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "../components/titan/PlaceholderPage";
import { GlassCard } from "../components/titan/primitives";
import { FileText, Download } from "lucide-react";

export const Route = createFileRoute("/reports")({ component: Reports });

const reports = [
  { title: "Weekly Intelligence Digest", period: "Week 41", size: "3.2 MB" },
  { title: "Model Calibration Report", period: "Sep 2026", size: "1.8 MB" },
  { title: "Market Movement Study", period: "Q3 2026", size: "5.7 MB" },
  { title: "Backtest — EV≥3 Strategy", period: "90-day", size: "2.1 MB" },
];

function Reports() {
  return (
    <PlaceholderPage eyebrow="Exports" title="Reports" description="Signed, versioned reports across intelligence surfaces.">
      <div className="grid gap-3 md:grid-cols-2">
        {reports.map((r) => (
          <GlassCard key={r.title} className="flex items-center gap-3 p-4">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate font-medium">{r.title}</div>
              <div className="text-xs text-muted-foreground">{r.period} · {r.size}</div>
            </div>
            <button className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
              <Download className="h-3.5 w-3.5" /> PDF
            </button>
          </GlassCard>
        ))}
      </div>
    </PlaceholderPage>
  );
}
