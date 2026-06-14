import Link from "next/link";
import { CopyCommand } from "./_components/CopyCommand";
import { SetupTabs } from "./_components/SetupTabs";
import { SpotlightCard } from "./_components/SpotlightCard";
import { Features } from "@/components/ui/features-10";
import { GithubIcon, NpmIcon, Glyph, TOOLS } from "@/components/ui/logos";
import { FragmentedTools, LocalViz, ProvenanceViz, DeletableViz, SourceViz } from "./_components/visuals";
import { ArrowUpRight, Check, Cpu, Download, Plug, X } from "lucide-react";

const EXT = { target: "_blank", rel: "noopener noreferrer" } as const;
const arrowCls =
  "size-3.5 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5";

const GITHUB = "https://github.com/sidpan2011/persnally";
const NPM = "https://www.npmjs.com/package/persnally";

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <Nav />
      <main>
        <Hero />
        <Marquee />
        <Wedge />
        <Features />
        <HowItWorks />
        <Trust />
        <Positioning />
        <GetStarted />
      </main>
      <Footer />
    </div>
  );
}

/* ── Shared bits ─────────────────────────────────────────────── */

function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`font-semibold tracking-tight text-ink ${className}`}>
      persnally<span className="text-volt">.</span>
    </span>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt">{children}</span>
  );
}

function Section({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`mx-auto w-full max-w-6xl px-6 ${className}`}>
      {children}
    </section>
  );
}

/* ── Nav ─────────────────────────────────────────────────────── */

function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/60 bg-night/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link href="/" aria-label="Persnally home" className="transition-opacity hover:opacity-80">
          <Wordmark className="text-[17px]" />
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-mute md:flex">
          <a href="#how" className="transition-colors hover:text-ink">
            How it works
          </a>
          <a href="#trust" className="transition-colors hover:text-ink">
            Your data
          </a>
          <a
            href={GITHUB}
            {...EXT}
            className="group flex items-center gap-1.5 transition-colors hover:text-ink"
          >
            <GithubIcon className="size-4" />
            GitHub
            <ArrowUpRight className={arrowCls} />
          </a>
        </nav>
        <a
          href="#start"
          className="rounded-lg bg-electric px-4 py-2 text-sm font-medium text-white shadow-[0_0_28px_-6px_var(--color-electric)] transition-colors hover:bg-volt"
        >
          Get started
        </a>
      </div>
    </header>
  );
}

/* ── Hero ────────────────────────────────────────────────────── */

function Hero() {
  return (
    <Section className="relative pt-24 pb-24 sm:pt-32">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[760px] overflow-hidden">
        <div className="aurora" />
        <div className="absolute inset-0 bg-grid" />
      </div>

      <div className="mx-auto max-w-4xl text-center">
        <div className="rise" style={{ animationDelay: "0ms" }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 px-3 py-1 font-mono text-[11px] text-mute backdrop-blur">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-volt" />
            The context engine for you
          </span>
        </div>

        <h1
          className="rise mt-7 text-balance text-[2.6rem] font-semibold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl"
          style={{ animationDelay: "80ms" }}
        >
          Finally, every AI
          <br className="hidden sm:block" /> knows <span className="text-gradient">you</span>.
        </h1>

        <p
          className="rise mx-auto mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-mute sm:text-xl"
          style={{ animationDelay: "160ms" }}
        >
          Persnally learns who you are from your AI history — your chats, your code, your decisions —
          and feeds it to every tool you use, so you stop re-explaining your stack, your conventions,
          and yourself to every new AI.
        </p>

        <div
          className="rise mx-auto mt-9 flex max-w-md flex-col items-center gap-4"
          style={{ animationDelay: "240ms" }}
        >
          <CopyCommand command="npm i -g persnally && persnally setup" className="w-full shimmer" />
          <div className="flex items-center gap-4 text-xs text-mute">
            <a
              href={GITHUB}
              {...EXT}
              className="group flex items-center gap-1.5 transition-colors hover:text-ink"
            >
              <GithubIcon className="size-3.5" />
              Star on GitHub
              <ArrowUpRight className="size-3 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
            <span className="text-line">·</span>
            <a
              href={NPM}
              {...EXT}
              className="group flex items-center gap-1.5 transition-colors hover:text-ink"
            >
              <NpmIcon className="size-3.5" />
              View on npm
              <ArrowUpRight className="size-3 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          </div>
        </div>
      </div>

      <div className="rise mt-16 sm:mt-20" style={{ animationDelay: "340ms" }}>
        <MirrorCard />
      </div>
    </Section>
  );
}

/* The product, as the hero visual: an evidence-linked profile + decayed interests */
function MirrorCard() {
  const topics = [
    { name: "event sourcing", w: 0.92 },
    { name: "local-first software", w: 0.81 },
    { name: "go-to-market", w: 0.58 },
    { name: "rust", w: 0.44 },
  ];
  return (
    <div className="border-glow mx-auto max-w-4xl overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_50px_150px_-50px_rgba(1,0,254,0.5)]">
      <div className="flex items-center gap-2 border-b border-line/70 bg-panel/50 px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-line" />
        <span className="h-2.5 w-2.5 rounded-full bg-line" />
        <span className="h-2.5 w-2.5 rounded-full bg-line" />
        <span className="ml-2 font-mono text-[11px] text-faint">persnally — localhost:4983</span>
      </div>

      <div className="grid gap-px bg-line/60 md:grid-cols-5">
        <div className="bg-surface p-6 md:col-span-3 md:p-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-faint">Your profile</p>
          <p className="mt-3 text-lg font-medium leading-snug text-ink">
            A builder shipping a local-first context engine — moves fast, decides from first
            principles, and guards user trust as a non-negotiable.
          </p>
          <div className="mt-5 rounded-xl border border-line bg-night/40 p-4">
            <p className="text-sm leading-relaxed text-mute">
              Prefers the smallest design that solves the problem; reaches for SQLite and plain
              files before frameworks.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <span className="font-mono text-[11px] text-volt">↳ why does it think this?</span>
              <span className="rounded-md border border-line px-2 py-0.5 font-mono text-[11px] text-faint">
                7 events
              </span>
            </div>
          </div>
        </div>

        <div className="bg-surface p-6 md:col-span-2 md:p-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-faint">
            Interests · decay-weighted
          </p>
          <ul className="mt-4 space-y-4">
            {topics.map((t) => (
              <li key={t.name}>
                <div className="flex items-baseline justify-between gap-3">
                  <span className="truncate text-sm text-ink">{t.name}</span>
                  <span className="font-mono text-[11px] text-faint">{t.w.toFixed(2)}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line/60">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-electric to-volt"
                    style={{ width: `${Math.max(t.w * 100, 6)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ── Marquee: works with the tools you already use ───────────── */

function Marquee() {
  const row = [...TOOLS, ...TOOLS];
  return (
    <Section className="py-10">
      <p className="mb-7 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-faint">
        Reads your context in the tools you already use
      </p>
      <div className="marquee">
        {[0, 1].map((dup) => (
          <div className="marquee-track" key={dup} aria-hidden={dup === 1}>
            {row.map((t, i) => (
              <span
                key={`${dup}-${i}`}
                className="flex items-center gap-2.5 whitespace-nowrap text-lg font-medium text-mute"
              >
                <Glyph icon={t.icon} className="size-5" />
                {t.name}
              </span>
            ))}
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Wedge ───────────────────────────────────────────────────── */

function Wedge() {
  return (
    <Section className="py-28">
      <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div>
          <Eyebrow>The problem</Eyebrow>
          <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
            Every AI is brilliant — and amnesiac.
          </h2>
          <p className="mt-6 text-lg leading-relaxed text-mute">
            ChatGPT doesn&apos;t know what you told Claude. Your coding agent relearns your stack
            every session, or interrupts to ask. Each tool meets you as a stranger.
          </p>
          <p className="mt-4 text-[15px] leading-relaxed text-faint">
            And the model vendors can&apos;t fix it — their business is keeping you inside their
            walls, not sharing you across the others.
          </p>
        </div>
        <FragmentedTools />
      </div>
    </Section>
  );
}

/* ── How it works — animated beam pipeline ───────────────────── */

function HowItWorks() {
  const steps = [
    {
      k: "01",
      Icon: Download,
      t: "Import your history",
      d: "One command finds your Claude & ChatGPT exports, your Claude Code sessions, and your git repos, and reads them.",
    },
    {
      k: "02",
      Icon: Cpu,
      t: "It learns, on your machine",
      d: "A local daemon turns that activity into a structured, evidence-linked model of who you are. Nothing leaves your laptop.",
    },
    {
      k: "03",
      Icon: Plug,
      t: "Every AI reads it",
      d: "Connected over MCP — the open protocol your AI tools already speak — Claude, Cursor, and your agents read your context the moment a session starts.",
    },
  ];
  return (
    <Section id="how" className="py-28">
      <div className="max-w-2xl">
        <Eyebrow>How it works</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Your context, in every tool you touch.
        </h2>
      </div>

      <div className="mt-16 flex flex-col gap-10 lg:flex-row lg:items-start lg:gap-4">
        {steps.flatMap((s, i) => {
          const block = (
            <div key={s.k} className="flex-1">
              <div className="flex items-center gap-3">
                <span className="grid size-12 shrink-0 place-items-center rounded-xl border border-volt/30 bg-electric/10 shadow-[0_0_28px_-8px_var(--color-electric)]">
                  <s.Icon className="size-5 text-volt" strokeWidth={1.75} />
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-faint">
                  Step {s.k}
                </span>
              </div>
              <h3 className="mt-5 text-lg font-medium text-ink">{s.t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-mute">{s.d}</p>
            </div>
          );
          if (i === steps.length - 1) return [block];
          return [
            block,
            <div key={`beam-${i}`} className="hidden shrink-0 items-center self-start pt-6 lg:flex">
              <svg width="40" height="8" viewBox="0 0 40 8" aria-hidden>
                <line x1="0" y1="4" x2="40" y2="4" stroke="var(--color-line)" strokeWidth="1.5" />
                <line
                  className="beam-line"
                  x1="0"
                  y1="4"
                  x2="40"
                  y2="4"
                  stroke="var(--color-volt)"
                  strokeWidth="1.5"
                />
              </svg>
            </div>,
          ];
        })}
      </div>
    </Section>
  );
}

/* ── Trust — spotlight bento ─────────────────────────────────── */

function Trust() {
  const pillars = [
    {
      t: "Local-first",
      d: "Your context lives in ~/.persnally on your machine — not our cloud, not any vendor's silo. Serving it to an AI is a local read: instant, offline, free.",
      viz: <LocalViz />,
    },
    {
      t: "Provenance-complete",
      d: "Every claim links to the exact events behind it. “Why does it think this?” is a real lookup, never a guess.",
      viz: <ProvenanceViz />,
    },
    {
      t: "Truly deletable",
      d: "Forget a topic and it erases the events and everything derived from them, then rebuilds. No tombstones, no residue.",
      viz: <DeletableViz />,
    },
    {
      t: "Source-available",
      d: "Read the engine, audit the claims, run it yourself. The event schema and MCP interface are an open spec.",
      viz: <SourceViz />,
    },
  ];
  return (
    <Section id="trust" className="py-28">
      <div className="max-w-2xl">
        <Eyebrow>Your data, your rules</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
          A context engine you can actually trust.
        </h2>
        <p className="mt-6 text-lg leading-relaxed text-mute">
          Trust isn&apos;t a privacy policy here — it&apos;s the architecture. These aren&apos;t
          promises; they&apos;re properties of how it&apos;s built.
        </p>
      </div>

      <div className="mt-14 grid gap-5 md:grid-cols-2">
        {pillars.map((p) => (
          <SpotlightCard key={p.t}>
            <div className="border-b border-line/60 bg-night/30 px-6 pb-2 pt-6">{p.viz}</div>
            <div className="p-6">
              <h3 className="text-lg font-medium text-ink">{p.t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-mute">{p.d}</p>
            </div>
          </SpotlightCard>
        ))}
      </div>
    </Section>
  );
}

/* ── Positioning ─────────────────────────────────────────────── */

function Positioning() {
  const them = [
    "Built for agents & apps, not people",
    "Lives in their cloud",
    "Locked to one vendor",
    "You can't see, audit, or delete it",
  ];
  const us = [
    "Built for you",
    "Local-first, on your machine",
    "Across every AI vendor",
    "Read it, audit it, delete it — for real",
  ];
  return (
    <Section className="py-28">
      <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-b from-panel/50 to-surface px-6 py-20 sm:px-10">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-40">
          <div className="aurora" style={{ height: "100%", opacity: 0.28 }} />
        </div>

        <div className="text-center">
          <Eyebrow>The difference</Eyebrow>
          <p className="mx-auto mt-6 max-w-3xl text-balance text-[1.9rem] font-semibold leading-tight tracking-tight sm:text-[2.9rem] sm:leading-[1.1]">
            They built context <span className="text-mute">for agents.</span>
            <br className="hidden sm:block" /> We built it{" "}
            <span className="text-gradient">for you.</span>
          </p>
        </div>

        <div className="mx-auto mt-14 grid max-w-3xl gap-5 md:grid-cols-2">
          <div className="rounded-2xl border border-line bg-night/40 p-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-faint">
              Every other memory tool
            </p>
            <p className="mt-1.5 text-sm italic text-faint">“the memory layer for AI agents”</p>
            <ul className="mt-6 space-y-3.5">
              {them.map((x) => (
                <li key={x} className="flex items-start gap-3 text-[15px] text-mute">
                  <X className="mt-0.5 size-4 shrink-0 text-faint" strokeWidth={2} />
                  {x}
                </li>
              ))}
            </ul>
          </div>

          <div className="border-glow rounded-2xl border border-volt/30 bg-gradient-to-b from-electric/[0.07] to-surface p-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-volt">Persnally</p>
            <p className="mt-1.5 text-sm text-mute">the context engine for you</p>
            <ul className="mt-6 space-y-3.5">
              {us.map((x) => (
                <li key={x} className="flex items-start gap-3 text-[15px] text-ink">
                  <Check className="mt-0.5 size-4 shrink-0 text-volt" strokeWidth={2.25} />
                  {x}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <p className="mx-auto mt-10 max-w-xl text-center text-sm leading-relaxed text-faint">
          Every memory startup&apos;s homepage says &ldquo;for agents.&rdquo; Ours is the one that
          says <span className="text-mute">for you</span> — local-first, across every model, owned
          by you.
        </p>

        <div className="mt-8 flex justify-center">
          <a
            href="#start"
            className="rounded-lg bg-electric px-5 py-2.5 text-sm font-medium text-white shadow-[0_0_28px_-6px_var(--color-electric)] transition-colors hover:bg-volt"
          >
            Make every AI yours
          </a>
        </div>
      </div>
    </Section>
  );
}

/* ── Get started ─────────────────────────────────────────────── */

function GetStarted() {
  return (
    <Section id="start" className="py-28">
      <div className="mx-auto max-w-2xl text-center">
        <Eyebrow>Five minutes to your mirror</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Install, and see yourself.
        </h2>
        <p className="mt-6 text-lg leading-relaxed text-mute">
          One command finds your exports, reads your repos, synthesizes a profile, connects your AI
          clients, and opens the dashboard.
        </p>
      </div>

      <div className="mx-auto mt-10 max-w-2xl">
        <SetupTabs />
        <p className="mt-5 text-center font-mono text-[12px] text-faint">
          macOS · Linux · Windows · Node 20+ · bring your own key, or run fully local with Ollama
        </p>
      </div>

      <div className="mx-auto mt-8 flex max-w-2xl flex-wrap items-center justify-center gap-3">
        <a
          href={GITHUB}
          {...EXT}
          className="group flex items-center gap-2 rounded-lg border border-line bg-surface px-5 py-2.5 text-sm text-ink transition-colors hover:border-mute"
        >
          <GithubIcon className="size-4" />
          Read the source
          <ArrowUpRight className={arrowCls} />
        </a>
        <a
          href={NPM}
          {...EXT}
          className="group flex items-center gap-2 rounded-lg border border-line bg-surface px-5 py-2.5 text-sm text-ink transition-colors hover:border-mute"
        >
          <NpmIcon className="size-4" />
          persnally on npm
          <ArrowUpRight className={arrowCls} />
        </a>
      </div>
    </Section>
  );
}

/* ── Footer ──────────────────────────────────────────────────── */

function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-line/60">
      <Section className="flex flex-col items-start justify-between gap-8 pt-14 sm:flex-row sm:items-center">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-faint">
            © 2026 Persnally
          </p>
          <p className="mt-2.5 text-xl font-medium tracking-tight text-ink">
            So every AI finally knows <span className="text-gradient">you</span>.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-7 gap-y-3 text-sm text-mute">
          <a
            href={GITHUB}
            {...EXT}
            className="group flex items-center gap-1.5 transition-colors hover:text-ink"
          >
            <GithubIcon className="size-4" />
            GitHub
            <ArrowUpRight className={arrowCls} />
          </a>
          <a
            href={NPM}
            {...EXT}
            className="group flex items-center gap-1.5 transition-colors hover:text-ink"
          >
            <NpmIcon className="size-4" />
            npm
            <ArrowUpRight className={arrowCls} />
          </a>
          <a
            href={`${GITHUB}/blob/main/LICENSE`}
            {...EXT}
            className="group flex items-center gap-1 transition-colors hover:text-ink"
          >
            FSL-1.1-MIT
            <ArrowUpRight className={arrowCls} />
          </a>
        </div>
      </Section>

      {/* Giant brand wordmark — bold, full-bleed, subtle */}
      <div aria-hidden className="pointer-events-none mt-8 select-none px-6">
        <span className="block translate-y-[12%] bg-gradient-to-b from-ink/[0.10] to-ink/[0.02] bg-clip-text text-center text-[clamp(4rem,21vw,17rem)] font-bold leading-[0.8] tracking-tight text-transparent">
          persnally
          <span className="bg-gradient-to-b from-electric/60 to-electric/10 bg-clip-text text-transparent">
            .
          </span>
        </span>
      </div>
    </footer>
  );
}
