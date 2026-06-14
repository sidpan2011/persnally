import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
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
      <body className="antialiased">{children}</body>
    </html>
  );
}
