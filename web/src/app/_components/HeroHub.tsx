"use client";

import { MotionConfig } from "motion/react";
import { Activity, GitBranch, Shield } from "lucide-react";
import { AnimatedList } from "@/components/magicui/animated-list";
import { BorderBeam } from "@/components/magicui/border-beam";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { Glyph, TOOLS } from "@/components/ui/logos";

/* Hero visual: the actual Persnally dashboard, alive. Your profile + provenance,
   a live feed of what it learned from your AI history (Magic UI AnimatedList),
   and decay-weighted interests (NumberTicker), framed with BorderBeam. */

const claude = TOOLS.find((t) => t.name === "Claude")!.icon;

const EVENTS = [
  { id: "import", icon: <Glyph icon={claude} className="size-3.5 text-ink" />, label: "Imported 142 Claude conversations", meta: "source · ~/.claude" },
  { id: "decision", icon: <GitBranch className="size-3.5" />, label: "Decided: SQLite over Postgres", meta: "decision · 6 mentions" },
  { id: "behavior", icon: <Activity className="size-3.5" />, label: "Pattern: ships the smallest design", meta: "behavior" },
  { id: "principle", icon: <Shield className="size-3.5" />, label: "Value: guards user trust", meta: "principle" },
];

const INTERESTS = [
  { name: "event sourcing", w: 0.92 },
  { name: "local-first software", w: 0.81 },
  { name: "go-to-market", w: 0.58 },
  { name: "rust", w: 0.44 },
];

function EventRow({ icon, label, meta }: { icon: React.ReactNode; label: string; meta: string }) {
  return (
    <div className="flex w-full items-center gap-3 rounded-lg border border-line bg-night/50 px-3 py-2">
      <span className="grid size-7 shrink-0 place-items-center rounded-md bg-electric/15 text-electric">{icon}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] text-ink">{label}</p>
        <p className="truncate font-mono text-[10px] text-faint">{meta}</p>
      </div>
    </div>
  );
}

export function HeroHub() {
  return (
    <MotionConfig reducedMotion="user">
      <div className="relative mx-auto max-w-4xl overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_50px_150px_-50px_rgba(44,103,255,0.45)]">
        <BorderBeam size={120} duration={8} colorFrom="#2c67ff" colorTo="#ffffff" borderWidth={1.5} />

        <div className="flex items-center gap-2 border-b border-line/70 bg-panel/50 px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="ml-2 text-sm font-semibold tracking-tight text-ink">
            persnally<span className="text-electric">.</span>
          </span>
          <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[10px] text-faint">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-electric" /> live · on your machine
          </span>
        </div>

        <div className="grid gap-px bg-line/60 md:grid-cols-5">
          <div className="space-y-5 bg-surface p-6 md:col-span-3 md:p-7">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-faint">Your profile</p>
              <p className="mt-2 text-base font-medium leading-snug text-ink">
                A builder shipping a local-first context engine — moves fast, decides from first
                principles, and guards user trust as non-negotiable.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span className="font-mono text-[11px] text-electric">↳ why does it think this?</span>
                <span className="rounded-md border border-line px-2 py-0.5 font-mono text-[11px] text-faint">
                  142 events
                </span>
              </div>
            </div>

            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-faint">
                Learned from your AI history
              </p>
              <AnimatedList delay={1100} className="mt-3 min-h-[210px] items-stretch">
                {EVENTS.map((e) => (
                  <EventRow key={e.id} icon={e.icon} label={e.label} meta={e.meta} />
                ))}
              </AnimatedList>
            </div>
          </div>

          <div className="bg-surface p-6 md:col-span-2 md:p-7">
            <p className="font-mono text-[11px] uppercase tracking-wider text-faint">
              Interests · decay-weighted
            </p>
            <ul className="mt-4 space-y-4">
              {INTERESTS.map((t) => (
                <li key={t.name}>
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="truncate text-sm text-ink">{t.name}</span>
                    <NumberTicker
                      value={t.w}
                      decimalPlaces={2}
                      className="font-mono text-[11px] text-faint dark:text-faint"
                    />
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line/60">
                    <div className="h-full rounded-full bg-electric" style={{ width: `${Math.max(t.w * 100, 6)}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <p className="mt-5 text-center text-xs text-faint">
        Your context, learned once — read by every AI over MCP.
      </p>
    </MotionConfig>
  );
}
