/* Clean SVG visuals that explain Persnally's features — line-art, electric accents. */

const LINE = "#262a34";
const VOLT = "#6b6bff";
const ELECTRIC = "#0100fe";
const MUTE = "#8b90a0";

/* Cross-vendor: one local engine, every tool reads it over MCP. */
export function HubGraphic() {
  const tools = [
    { x: 26, y: 26, label: "Claude" },
    { x: 222, y: 26, label: "Cursor" },
    { x: 26, y: 118, label: "ChatGPT" },
    { x: 222, y: 118, label: "agents" },
  ];
  return (
    <svg viewBox="0 0 320 176" className="h-auto w-full" role="img" aria-label="One context, every tool">
      {tools.map((t) => (
        <line
          key={t.label}
          x1="160"
          y1="88"
          x2={t.x + 36}
          y2={t.y + 13}
          stroke={VOLT}
          strokeWidth="1.5"
          strokeDasharray="5 7"
          className="beam-line"
          opacity="0.7"
        />
      ))}
      {tools.map((t) => (
        <g key={t.label}>
          <rect x={t.x} y={t.y} width="72" height="26" rx="7" fill="#0e1016" stroke={LINE} />
          <text x={t.x + 36} y={t.y + 17} textAnchor="middle" fontSize="11" fill={MUTE} fontFamily="ui-monospace, monospace">
            {t.label}
          </text>
        </g>
      ))}
      <circle cx="160" cy="88" r="38" fill={ELECTRIC} opacity="0.12" />
      <rect x="118" y="74" width="84" height="28" rx="9" fill="#0b0c12" stroke={VOLT} strokeWidth="1.5" />
      <text x="160" y="92" textAnchor="middle" fontSize="11" fill={VOLT} fontFamily="ui-monospace, monospace">
        persnallyd
      </text>
    </svg>
  );
}

/* Provenance: every claim links to the exact events behind it. */
export function ProvenanceGraphic() {
  const events = [40, 120, 200];
  return (
    <svg viewBox="0 0 280 176" className="h-auto w-full" role="img" aria-label="Every claim cites its evidence">
      <rect x="40" y="20" width="200" height="40" rx="9" fill="#0b0c12" stroke={VOLT} strokeWidth="1.5" />
      <rect x="54" y="33" width="120" height="6" rx="3" fill={MUTE} opacity="0.7" />
      <rect x="54" y="45" width="80" height="6" rx="3" fill={MUTE} opacity="0.4" />
      <text x="214" y="44" textAnchor="middle" fontSize="10" fill={VOLT} fontFamily="ui-monospace, monospace">
        why?
      </text>
      {events.map((x) => (
        <line key={x} x1="140" y1="60" x2={x + 30} y2="116" stroke={VOLT} strokeWidth="1.5" strokeDasharray="4 6" className="beam-line" opacity="0.6" />
      ))}
      {events.map((x, i) => (
        <g key={x}>
          <rect x={x} y="116" width="60" height="40" rx="8" fill="#0e1016" stroke={LINE} />
          <circle cx={x + 14} cy="136" r="4" fill={ELECTRIC} />
          <text x={x + 38} y="133" textAnchor="middle" fontSize="9" fill={MUTE} fontFamily="ui-monospace, monospace">
            event
          </text>
          <text x={x + 38} y="145" textAnchor="middle" fontSize="9" fill={MUTE} opacity="0.6" fontFamily="ui-monospace, monospace">
            #{i + 1}
          </text>
        </g>
      ))}
    </svg>
  );
}
