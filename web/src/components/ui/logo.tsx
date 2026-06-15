/* Persnally logomark — a bold geometric "P" with a squared counter (the engine)
   and an electric connector tab (#2c67ff): your context, plugged into every tool.
   Body inherits currentColor; counter is a true cut-out, so it works on any bg. */
export function Mark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={className} aria-hidden>
      <rect x="18" y="12" width="9" height="44" rx="4.5" fill="currentColor" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        fill="currentColor"
        d="M25 12 H35 a13 13 0 0 1 0 26 H25 Z M30 18.5 h5 a2.5 2.5 0 0 1 2.5 2.5 v4 a2.5 2.5 0 0 1 -2.5 2.5 h-5 a2.5 2.5 0 0 1 -2.5 -2.5 v-4 a2.5 2.5 0 0 1 2.5 -2.5 z"
      />
      <rect x="9" y="19" width="9" height="9" rx="2.5" fill="#2c67ff" />
    </svg>
  );
}
