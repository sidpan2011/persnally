"use client";

import { createClient } from "@/lib/supabase/client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  const handleGitHubLogin = async () => {
    const supabase = createClient();
    await supabase.auth.signInWithOAuth({
      provider: "github",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        scopes: "read:user repo",
      },
    });
  };

  return (
    <div className="relative min-h-screen bg-night text-ink flex items-center justify-center px-4 overflow-hidden">
      <div className="aurora pointer-events-none absolute inset-0 opacity-60" />
      <div className="relative z-10 max-w-md w-full">
        <div className="border-glow rounded-2xl border border-line bg-surface p-8 text-center shadow-[0_0_60px_-20px_var(--color-electric)]">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-electric mb-5">
            Context engine
          </p>
          <h1 className="text-gradient text-4xl font-semibold tracking-tight mb-3">
            Persnally
          </h1>
          <p className="text-mute mb-10">
            So every AI finally knows you.
          </p>

          {error && (
            <div className="rounded-lg border border-electric/30 bg-panel p-3 mb-6 text-sm text-[#ff7a7a]">
              Authentication failed. Please try again.
            </div>
          )}

          <button
            onClick={handleGitHubLogin}
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-electric px-6 py-3 text-sm font-medium text-white shadow-[0_0_28px_-6px_var(--color-electric)] transition-colors hover:bg-electric-deep cursor-pointer"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Continue with GitHub
          </button>

          <p className="mt-6 text-xs text-faint">
            We analyze your GitHub to understand your tech stack, not to access
            your code.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-night" />}>
      <LoginContent />
    </Suspense>
  );
}
