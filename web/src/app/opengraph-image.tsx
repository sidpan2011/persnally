import { ImageResponse } from "next/og";

export const alt = "Persnally — the context engine for you";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Branded social-share card: electric-on-black, matching the site.
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#000000",
          backgroundImage:
            "radial-gradient(60% 60% at 50% 32%, rgba(44,103,255,0.30), transparent 70%)",
          color: "#f5f6f8",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            fontSize: 34,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "#2c67ff",
            marginBottom: 30,
          }}
        >
          The context engine for you
        </div>
        <div style={{ display: "flex", fontSize: 116, fontWeight: 800, letterSpacing: "-0.04em" }}>
          <span>persnally</span>
          <span style={{ color: "#2c67ff" }}>.</span>
        </div>
        <div style={{ display: "flex", fontSize: 46, color: "#8b90a0", marginTop: 28 }}>
          <span>So every AI finally knows&nbsp;</span>
          <span style={{ color: "#f5f6f8" }}>you</span>
          <span>.</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
