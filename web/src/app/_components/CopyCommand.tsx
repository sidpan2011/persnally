"use client";

import { useState } from "react";

export function CopyCommand({ command, className = "" }: { command: string; className?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard blocked — the command is still visible to select */
    }
  };

  return (
    <button
      onClick={copy}
      aria-label={`Copy: ${command}`}
      className={`group flex items-center gap-3 rounded-xl border border-line bg-surface/80 px-4 py-3 text-left transition-colors hover:border-electric/50 ${className}`}
    >
      <span className="select-none text-electric" aria-hidden>
        $
      </span>
      <code className="min-w-0 flex-1 overflow-x-auto whitespace-nowrap font-mono text-[12px] text-ink sm:text-[13.5px] [scrollbar-width:none]">
        {command}
      </code>
      <span
        className={`shrink-0 font-mono text-[11px] uppercase tracking-wider transition-colors ${
          copied ? "text-electric" : "text-faint group-hover:text-mute"
        }`}
      >
        {copied ? "copied" : "copy"}
      </span>
    </button>
  );
}
