"use client";

import { useRef, useState } from "react";

/* Aceternity-style spotlight: an electric glow follows the cursor across the card. */
export function SpotlightCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: -200, y: -200 });
  const [on, setOn] = useState(false);

  return (
    <div
      ref={ref}
      onMouseMove={(e) => {
        const r = ref.current?.getBoundingClientRect();
        if (r) setPos({ x: e.clientX - r.left, y: e.clientY - r.top });
      }}
      onMouseEnter={() => setOn(true)}
      onMouseLeave={() => setOn(false)}
      className={`group relative overflow-hidden rounded-2xl border border-line bg-surface transition-colors duration-300 hover:border-electric/40 ${className}`}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300"
        style={{
          opacity: on ? 1 : 0,
          background: `radial-gradient(340px circle at ${pos.x}px ${pos.y}px, color-mix(in oklab, var(--color-electric) 22%, transparent), transparent 70%)`,
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
