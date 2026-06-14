/* Section visuals — small, clean SVG/JSX graphics for the landing. */
import { Glyph, TOOLS } from "@/components/ui/logos";

/* Problem: each tool meets you as a stranger — siloed, amnesiac. */
export function FragmentedTools() {
  const tools = TOOLS.slice(0, 3); // Claude, ChatGPT, Cursor
  return (
    <div className="relative space-y-3">
      {tools.map((t) => (
        <div key={t.name} className="rounded-xl border border-line bg-surface/80 p-4">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm text-ink">
              <Glyph icon={t.icon} className="size-4" />
              {t.name}
            </span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-faint">
              no memory of you
            </span>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <span className="grid size-9 shrink-0 place-items-center rounded-full border border-dashed border-line text-faint">
              ?
            </span>
            <div className="flex-1 space-y-1.5">
              <div className="h-2 w-2/3 rounded bg-line" />
              <div className="h-2 w-1/3 rounded bg-line/60" />
            </div>
          </div>
        </div>
      ))}
      <p className="pt-1 text-center font-mono text-[11px] text-faint">
        three tools · three strangers · zero shared context
      </p>
    </div>
  );
}

/* ── Trust pillar mini-visuals ───────────────────────────────── */

const L = "#262a34";
const V = "#6b6bff";
const E = "#0100fe";
const M = "#8b90a0";
const box = "h-28 w-full";

export function LocalViz() {
  return (
    <svg viewBox="0 0 260 110" className={box} role="img" aria-label="stays on your machine">
      <rect x="40" y="20" width="120" height="74" rx="10" fill="#0b0c12" stroke={L} />
      <text x="54" y="38" fontSize="9" fill={M} fontFamily="ui-monospace,monospace">~/.persnally</text>
      {[50, 62, 74].map((y, i) => (
        <g key={y}>
          <circle cx="56" cy={y} r="2.5" fill={E} opacity={1 - i * 0.2} />
          <rect x="64" y={y - 3} width={80 - i * 16} height="5" rx="2.5" fill={M} opacity={0.4 - i * 0.06} />
        </g>
      ))}
      <path d="M196 34 l20 7 v15 c0 14 -10 21 -20 25 c-10 -4 -20 -11 -20 -25 v-15 z" fill={E} opacity="0.14" stroke={V} strokeWidth="1.4" />
      <path d="M187 58 l7 7 l12 -14" stroke={V} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ProvenanceViz() {
  return (
    <svg viewBox="0 0 260 110" className={box} role="img" aria-label="every claim cites its evidence">
      <rect x="30" y="16" width="200" height="30" rx="8" fill="#0b0c12" stroke={V} strokeWidth="1.4" />
      <rect x="44" y="27" width="110" height="5" rx="2.5" fill={M} opacity="0.6" />
      <text x="200" y="35" textAnchor="middle" fontSize="8.5" fill={V} fontFamily="ui-monospace,monospace">why?</text>
      {[60, 120, 180].map((x) => (
        <g key={x}>
          <line x1="120" y1="46" x2={x + 22} y2="74" stroke={V} strokeWidth="1.3" strokeDasharray="3 5" className="beam-line" opacity="0.6" />
          <rect x={x} y="74" width="44" height="22" rx="6" fill="#0e1016" stroke={L} />
          <circle cx={x + 11} cy="85" r="3" fill={E} />
          <text x={x + 28} y="88" textAnchor="middle" fontSize="8" fill={M} fontFamily="ui-monospace,monospace">evt</text>
        </g>
      ))}
    </svg>
  );
}

export function DeletableViz() {
  return (
    <svg viewBox="0 0 260 110" className={box} role="img" aria-label="truly deletable">
      {[22, 46, 70].map((y, i) => (
        <g key={y} opacity={i === 1 ? 0.35 : 1}>
          <rect x="30" y={y} width="170" height="18" rx="6" fill="#0e1016" stroke={L} />
          <circle cx="44" cy={y + 9} r="3" fill={i === 1 ? M : E} />
          <rect x="56" y={y + 6} width={110 - i * 20} height="5" rx="2.5" fill={M} opacity="0.4" />
          {i === 1 && <line x1="30" y1={y + 9} x2="200" y2={y + 9} stroke={V} strokeWidth="1.4" />}
        </g>
      ))}
      <g>
        <circle cx="224" cy="55" r="14" fill={E} opacity="0.14" stroke={V} strokeWidth="1.4" />
        <line x1="218" y1="55" x2="230" y2="55" stroke={V} strokeWidth="2" strokeLinecap="round" />
      </g>
      <text x="115" y="104" textAnchor="middle" fontSize="9" fill={M} fontFamily="ui-monospace,monospace">forget → events + derivations gone</text>
    </svg>
  );
}

export function SourceViz() {
  return (
    <svg viewBox="0 0 260 110" className={box} role="img" aria-label="source-available, open spec">
      <rect x="30" y="20" width="200" height="74" rx="10" fill="#0b0c12" stroke={L} />
      <text x="44" y="40" fontSize="11" fill={V} fontFamily="ui-monospace,monospace">{"{ }"}</text>
      {[52, 62, 72, 82].map((y, i) => (
        <rect key={y} x={64 + (i % 2) * 10} y={y - 4} width={120 - i * 22} height="5" rx="2.5" fill={M} opacity={0.5 - i * 0.05} />
      ))}
      <path d="M196 40 v-6 a8 8 0 0 1 16 0" fill="none" stroke={V} strokeWidth="1.6" />
      <rect x="192" y="40" width="24" height="20" rx="4" fill={E} opacity="0.18" stroke={V} strokeWidth="1.4" />
    </svg>
  );
}
