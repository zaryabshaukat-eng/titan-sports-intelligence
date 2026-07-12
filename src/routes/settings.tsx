import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "../components/titan/AppShell";
import { GlassCard, SectionTitle } from "../components/titan/primitives";
import { User, Bell, Shield, Plug, Palette, Globe } from "lucide-react";

export const Route = createFileRoute("/settings")({ component: SettingsPage });

const sections = [
  { icon: User, title: "Profile & Workspace", desc: "Organization, workspace defaults, timezone." },
  { icon: Bell, title: "Alerts & Notifications", desc: "Delivery channels, thresholds, quiet hours." },
  { icon: Shield, title: "Security", desc: "SSO, MFA, session policies, IP allowlist." },
  { icon: Plug, title: "Integrations", desc: "Data feeds, bookmakers, webhooks, API keys." },
  { icon: Palette, title: "Interface", desc: "Layout density, chart palette, mono font." },
  { icon: Globe, title: "Regions & Compliance", desc: "Jurisdiction constraints, data residency." },
];

function SettingsPage() {
  return (
    <>
      <PageHeader eyebrow="Configuration" title="Settings" description="Enterprise controls for your Titan workspace." />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sections.map((s) => (
          <GlassCard key={s.title} className="p-5 transition-all hover:border-white/15">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 text-primary">
                <s.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h3 className="font-display font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.desc}</p>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <GlassCard className="mt-6 p-6">
        <SectionTitle title="General preferences" description="Applied across the entire workspace." />
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { l: "Workspace name", v: "Titan Operations" },
            { l: "Default timezone", v: "Europe/London (UTC+0)" },
            { l: "Odds format", v: "Decimal" },
            { l: "Stake unit", v: "£100" },
          ].map((f) => (
            <div key={f.l}>
              <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{f.l}</label>
              <input defaultValue={f.v} className="h-10 w-full rounded-md border border-white/10 bg-white/5 px-3 text-sm focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/20" />
            </div>
          ))}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button className="rounded-md border border-white/10 bg-white/5 px-4 py-2 text-sm">Cancel</button>
          <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Save changes</button>
        </div>
      </GlassCard>
    </>
  );
}
