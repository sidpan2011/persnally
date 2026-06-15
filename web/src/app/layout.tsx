import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Geist_Mono } from "next/font/google";
import { OpenPanelComponent } from "@openpanel/nextjs";
import "./globals.css";

// OpenPanel client id (public browser key) — kept out of source. Set
// NEXT_PUBLIC_OPENPANEL_CLIENT_ID in .env.local for dev and in your host for prod.
const OPENPANEL_CLIENT_ID = process.env.NEXT_PUBLIC_OPENPANEL_CLIENT_ID;

const sans = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

const description =
  "Persnally is a local-first personal context engine. It learns who you are from your AI history and serves that context to every AI tool you use — local-first, across every AI.";

export const metadata: Metadata = {
  metadataBase: new URL("https://persnally.com"),
  title: "Persnally — the context engine for you",
  description,
  keywords: ["personal context engine", "local-first", "MCP", "AI memory", "Claude", "ChatGPT", "Cursor"],
  openGraph: {
    title: "Persnally — so every AI finally knows you",
    description,
    url: "https://persnally.com",
    siteName: "Persnally",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Persnally — so every AI finally knows you",
    description,
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${mono.variable}`}>
      <body className="antialiased">
        {OPENPANEL_CLIENT_ID && (
          <OpenPanelComponent
            clientId={OPENPANEL_CLIENT_ID}
            trackScreenViews
            trackOutgoingLinks
            trackAttributes
          />
        )}
        {children}
      </body>
    </html>
  );
}
