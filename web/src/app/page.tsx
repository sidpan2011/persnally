import Link from "next/link";
import { CopyCommand } from "./_components/CopyCommand";
import { HeroHub } from "./_components/HeroHub";
import { AnimatedGridPattern } from "@/components/magicui/animated-grid-pattern";
import { SetupTabs } from "./_components/SetupTabs";
import { SpotlightCard } from "./_components/SpotlightCard";
import { Features } from "@/components/ui/features-10";
import { GithubIcon, NpmIcon, Glyph, TOOLS } from "@/components/ui/logos";
import { RepetitionFeed } from "./_components/RepetitionFeed";
import { ArrowUpRight, Check, ChevronRight, Cpu, Database, Download, FileJson, Plug, Star, X } from "lucide-react";

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
      persnally<span className="text-electric">.</span>
    </span>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-electric">{children}</span>
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
          className="rounded-lg bg-electric px-4 py-2 text-sm font-medium text-white shadow-[0_0_28px_-6px_var(--color-electric)] transition-colors hover:bg-electric-deep"
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
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[820px] overflow-hidden">
        <div className="aurora" />
        <AnimatedGridPattern
          numSquares={34}
          maxOpacity={0.15}
          duration={4}
          className="[mask-image:radial-gradient(640px_circle_at_50%_170px,white,transparent)] text-electric/35 stroke-electric/10"
        />
      </div>

      <div className="mx-auto max-w-4xl text-center">
        <div className="rise" style={{ animationDelay: "0ms" }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 px-3 py-1 font-mono text-[11px] text-mute backdrop-blur">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-electric" />
            Your own context engine
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
          className="rise mx-auto mt-6 max-w-2xl text-pretty text-base leading-relaxed text-mute"
          style={{ animationDelay: "160ms" }}
        >
          Persnally learns who you are from your AI history — your chats, your code, your decisions —
          and feeds it to every tool you use, so you stop re-explaining your stack, your conventions,
          and yourself to every new AI. It lives on your machine, and it&apos;s yours.
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
          <a
            href="https://www.producthunt.com/products/persnally?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-persnally"
            {...EXT}
            aria-label="Persnally on Product Hunt"
            className="mt-1 inline-block transition-opacity hover:opacity-90"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1182562&theme=light&t=1782584790813"
              alt="Persnally - So every AI finally knows you | Product Hunt"
              width={250}
              height={54}
            />
          </a>
        </div>
      </div>

      <div className="rise mt-16 sm:mt-20" style={{ animationDelay: "340ms" }}>
        <HeroHub />
      </div>
    </Section>
  );
}

/* ── Marquee: works with the tools you already use ───────────── */

function Marquee() {
  const row = [...TOOLS, ...TOOLS];
  return (
    <Section className="py-10">
      <p className="mb-7 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-faint">
        Works with the AI tools you already use
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
            You explain yourself.
            <br className="hidden sm:block" /> Again. And again.
          </h2>
          <p className="mt-6 text-lg leading-relaxed text-mute">
            ChatGPT doesn&apos;t know what you told Claude. Your coding agent relearns your stack
            every session, or stops to ask. So you paste the same context — your tools, your
            conventions, your taste — into tool after tool.
          </p>
          <p className="mt-4 text-[15px] leading-relaxed text-faint">
            Each meets you as a stranger. And the model vendors can&apos;t fix it — their business
            is keeping you inside their walls, not sharing you across them.
          </p>
        </div>
        <RepetitionFeed />
      </div>
    </Section>
  );
}

/* ── How it works — animated beam pipeline ───────────────────── */

function HowItWorks() {
  const steps = [
    {
      k: "01",
      label: "Import",
      Icon: Download,
      t: "Import your history",
      d: "One command finds your Claude & ChatGPT exports, your Claude Code sessions, and your git repos, and reads them.",
      visual: <ImportViz />,
    },
    {
      k: "02",
      label: "Learn · local",
      Icon: Cpu,
      t: "It learns, on your machine",
      d: "A local daemon turns that activity into a structured, evidence-linked model of who you are — kept on your machine, never our cloud.",
      visual: <LearnViz />,
    },
    {
      k: "03",
      label: "Serve · MCP",
      Icon: Plug,
      t: "Every AI reads it",
      d: "Connected over MCP — the open protocol your AI tools already speak — Claude, Cursor, and your agents read your context the moment a session starts.",
      visual: <ServeViz />,
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

      <div className="mt-14 flex flex-col gap-4 lg:flex-row lg:items-stretch lg:gap-3">
        {steps.flatMap((s, i) => {
          const card = (
            <div key={s.k} className="flex flex-1 flex-col rounded-2xl border border-line bg-surface p-6">
              <div className="flex items-center gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl border border-electric/30 bg-electric/10 text-electric shadow-[0_0_28px_-8px_var(--color-electric)]">
                  <s.Icon className="size-5" strokeWidth={1.75} />
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-faint">
                  Step {s.k} · {s.label}
                </span>
              </div>
              <h3 className="mt-5 text-lg font-medium text-ink">{s.t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-mute">{s.d}</p>
              <div className="mt-auto pt-6">{s.visual}</div>
            </div>
          );
          if (i === steps.length - 1) return [card];
          return [
            card,
            <div key={`c-${i}`} className="hidden shrink-0 items-center lg:flex">
              <ChevronRight className="size-5 text-faint" />
            </div>,
          ];
        })}
      </div>
    </Section>
  );
}

const claudeIcon = TOOLS.find((t) => t.name === "Claude")!.icon;

function StepPanel({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-line bg-night/50 p-3.5">{children}</div>;
}

function ImportViz() {
  const sources = ["Claude & ChatGPT exports", "Claude Code sessions", "git repos"];
  return (
    <StepPanel>
      <p className="font-mono text-[12px] text-mute">
        <span className="text-electric">$</span> persnally import
      </p>
      <ul className="mt-2.5 space-y-1.5 font-mono text-[11px] text-faint">
        {sources.map((src) => (
          <li key={src} className="flex items-center gap-2">
            <Check className="size-3 shrink-0 text-electric" />
            {src}
          </li>
        ))}
      </ul>
    </StepPanel>
  );
}

function LearnViz() {
  const signals = ["ships the smallest design", "prefers SQLite", "guards user trust"];
  return (
    <StepPanel>
      <p className="font-mono text-[11px] text-faint">building your model…</p>
      <ul className="mt-2.5 space-y-1.5 text-[13px] text-mute">
        {signals.map((sig) => (
          <li key={sig} className="flex items-center gap-2">
            <span className="size-1.5 shrink-0 rounded-full bg-electric" />
            {sig}
          </li>
        ))}
      </ul>
      <span className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-electric/30 bg-electric/10 px-2 py-0.5 font-mono text-[10px] text-electric">
        <Cpu className="size-3" />
        on your machine
      </span>
    </StepPanel>
  );
}

function ServeViz() {
  return (
    <StepPanel>
      <span className="flex items-center gap-2 text-[13px] text-ink">
        <Glyph icon={claudeIcon} className="size-3.5 text-ink" />
        Claude · session started
      </span>
      <div className="mt-3 rounded-lg border border-line bg-surface/60 px-3 py-2.5">
        <p className="font-mono text-[11px] text-electric">↳ loaded your context</p>
        <p className="mt-1 flex items-center gap-1.5 font-mono text-[10px] text-faint">
          get_context <Check className="size-3 text-electric" /> 12ms
        </p>
      </div>
    </StepPanel>
  );
}

/* ── Trust — spotlight bento ─────────────────────────────────── */

function Trust() {
  const pillars = [
    {
      t: "Local-first",
      d: "Your context lives in ~/.persnally on your machine — not our cloud, not any vendor's silo. Serving it to an AI is a local read: instant, offline, free.",
      viz: <LocalProof />,
    },
    {
      t: "Truly deletable",
      d: "Forget a topic and it erases the events and everything derived from them, then rebuilds. No tombstones, no residue.",
      viz: <DeleteProof />,
    },
    {
      t: "Provenance-complete",
      d: "Every claim links to the exact events behind it. “Why does it think this?” is a real lookup, never a guess.",
      viz: <AuditProof />,
    },
    {
      t: "Source-available",
      d: "Read the engine, audit the claims, run it yourself. The event schema and MCP interface are an open spec.",
      viz: <SourceProof />,
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
          Trust isn&apos;t a privacy policy here — it&apos;s the architecture. Not promises;
          properties you can check.
        </p>
      </div>

      <div className="mt-14 grid gap-5 md:grid-cols-2">
        {pillars.map((p) => (
          <SpotlightCard key={p.t} className="p-6">
            <h3 className="text-lg font-medium text-ink">{p.t}</h3>
            <p className="mt-2 text-[15px] leading-relaxed text-mute">{p.d}</p>
            <div className="mt-5">{p.viz}</div>
          </SpotlightCard>
        ))}
      </div>

      <div className="mt-6 flex flex-col items-center gap-6 rounded-2xl border border-line bg-surface/50 p-8 text-center">
        <div className="flex flex-wrap justify-center gap-2.5">
          {["No account", "Bring your own keys", "Works offline", "Open spec"].map((c) => (
            <span
              key={c}
              className="inline-flex items-center gap-1.5 rounded-full border border-line bg-night/40 px-3 py-1 font-mono text-[11px] text-mute"
            >
              <Check className="size-3 text-electric" />
              {c}
            </span>
          ))}
        </div>
        <a
          href={GITHUB}
          {...EXT}
          className="group inline-flex items-center gap-1.5 text-sm text-mute transition-colors hover:text-ink"
        >
          <GithubIcon className="size-3.5" />
          Read the source
          <ArrowUpRight className="size-3 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </a>
      </div>
    </Section>
  );
}

function ProofPanel({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-line bg-night/50 p-3.5">{children}</div>;
}

function LocalProof() {
  const files = [
    { icon: <Database className="size-3.5" />, name: "events.db" },
    { icon: <FileJson className="size-3.5" />, name: "profile.json" },
    { icon: <FileJson className="size-3.5" />, name: "interests.json" },
  ];
  return (
    <ProofPanel>
      <p className="font-mono text-[11px] text-faint">~/.persnally</p>
      <ul className="mt-2.5 space-y-1.5 font-mono text-[12px] text-mute">
        {files.map((f) => (
          <li key={f.name} className="flex items-center gap-2">
            <span className="text-electric">{f.icon}</span>
            {f.name}
          </li>
        ))}
      </ul>
      <p className="mt-3 font-mono text-[10px] text-faint">stays on your machine, never our cloud</p>
    </ProofPanel>
  );
}

function DeleteProof() {
  return (
    <ProofPanel>
      <p className="font-mono text-[12px] text-mute">
        <span className="text-electric">$</span> persnally forget “rust”
      </p>
      <ul className="mt-2.5 space-y-1.5 font-mono text-[11px] text-faint">
        <li className="flex items-center gap-2">
          <Check className="size-3 shrink-0 text-electric" />
          18 events erased
        </li>
        <li className="flex items-center gap-2">
          <Check className="size-3 shrink-0 text-electric" />
          derived views rebuilt
        </li>
      </ul>
      <p className="mt-2.5 font-mono text-[10px] text-faint">no tombstones · no residue</p>
    </ProofPanel>
  );
}

function AuditProof() {
  const events = [
    { id: "#412", t: "vetoed telemetry" },
    { id: "#087", t: "chose local-first" },
    { id: "#203", t: "removed analytics" },
  ];
  return (
    <ProofPanel>
      <p className="font-mono text-[11px] text-electric">↳ why “guards user trust”?</p>
      <ul className="mt-2.5 space-y-1.5 font-mono text-[11px] text-mute">
        {events.map((e) => (
          <li key={e.id} className="flex items-center gap-2">
            <span className="text-faint">{e.id}</span>
            {e.t}
          </li>
        ))}
      </ul>
      <p className="mt-2.5 font-mono text-[10px] text-faint">3 events · 0 guesses</p>
    </ProofPanel>
  );
}

function SourceProof() {
  return (
    <a
      href={GITHUB}
      {...EXT}
      className="group block rounded-xl border border-line bg-night/50 p-3.5 transition-colors hover:border-electric/40"
    >
      <div className="flex items-center gap-2 text-ink">
        <GithubIcon className="size-4" />
        <span className="font-mono text-[12px]">sidpan2011/persnally</span>
        <ArrowUpRight className="ml-auto size-3.5 text-faint transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      </div>
      <div className="mt-2.5 flex items-center gap-3 font-mono text-[10px] text-faint">
        <span className="flex items-center gap-1">
          <Star className="size-3" />
          star
        </span>
        <span>FSL → MIT after 2y</span>
        <span>open spec</span>
      </div>
    </a>
  );
}

/* ── Positioning ─────────────────────────────────────────────── */

function Positioning() {
  const them = [
    "Your context lives in their cloud",
    "They own what it knows about you",
    "Locked to one app — every other AI starts over",
    "A black box — it can't tell you why",
  ];
  const us = [
    "Knows you across every AI you use",
    "Yours — you own it outright, no vendor holds it",
    "Every claim cites its evidence — ask it why",
    "See it, audit it, delete it — for real",
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
            Every AI knows <span className="text-mute">you.</span>
            <br className="hidden sm:block" /> And it&apos;s{" "}
            <span className="text-gradient">yours.</span>
          </p>
        </div>

        <div className="mx-auto mt-14 grid max-w-3xl gap-5 md:grid-cols-2">
          <div className="rounded-2xl border border-line bg-night/40 p-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-faint">
              Every other memory tool
            </p>
            <p className="mt-1.5 text-sm italic text-faint">“memory that lives in someone’s cloud”</p>
            <ul className="mt-6 space-y-3.5">
              {them.map((x) => (
                <li key={x} className="flex items-start gap-3 text-[15px] text-mute">
                  <X className="mt-0.5 size-4 shrink-0 text-faint" strokeWidth={2} />
                  {x}
                </li>
              ))}
            </ul>
          </div>

          <div className="border-glow rounded-2xl border border-electric/30 bg-gradient-to-b from-electric/[0.07] to-surface p-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-electric">Persnally</p>
            <p className="mt-1.5 text-sm text-mute">your own context engine</p>
            <ul className="mt-6 space-y-3.5">
              {us.map((x) => (
                <li key={x} className="flex items-start gap-3 text-[15px] text-ink">
                  <Check className="mt-0.5 size-4 shrink-0 text-electric" strokeWidth={2.25} />
                  {x}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <p className="mx-auto mt-10 max-w-xl text-center text-sm leading-relaxed text-faint">
          Every memory tool now promises your context is &ldquo;yours.&rdquo; Persnally is the one
          where that&apos;s true — it knows you everywhere, you own it outright, and you can see and
          delete everything it knows.
        </p>

        <div className="mt-8 flex justify-center">
          <a
            href="#start"
            className="rounded-lg bg-electric px-5 py-2.5 text-sm font-medium text-white shadow-[0_0_28px_-6px_var(--color-electric)] transition-colors hover:bg-electric-deep"
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
    <Section id="start" className="relative overflow-hidden py-28">
      <div className="pointer-events-none absolute left-1/2 top-8 h-[420px] w-[680px] max-w-full -translate-x-1/2 rounded-full bg-electric/10 blur-[130px]" />
      <div className="relative mx-auto max-w-2xl text-center">
        <Eyebrow>Five minutes to your mirror</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Install, and see yourself.
        </h2>
        <p className="mt-6 text-lg leading-relaxed text-mute">
          One command finds your exports, reads your repos, synthesizes a profile, connects your AI
          clients, and opens the dashboard.
        </p>
      </div>

      <div className="relative mx-auto mt-10 max-w-2xl">
        <SetupTabs />
        <p className="mt-5 text-center font-mono text-[12px] text-faint">
          macOS · Linux · Windows · Node 20+ · bring your own key, or run fully local with Ollama
        </p>
        <div className="mt-6 flex justify-center">
          <a
            href={GITHUB}
            {...EXT}
            className="group inline-flex items-center gap-1.5 text-sm text-mute transition-colors hover:text-ink"
          >
            <GithubIcon className="size-4" />
            Read the source
            <ArrowUpRight className={arrowCls} />
          </a>
        </div>
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
