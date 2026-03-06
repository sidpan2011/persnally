import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");

  if (code) {
    const supabase = await createServerSupabaseClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error && data.session) {
      // Store GitHub token in connected_accounts via API
      const provider = data.session.user.app_metadata?.provider;
      if (provider === "github") {
        const ghToken = data.session.provider_token;
        const ghUser = data.session.user.user_metadata;

        if (ghToken) {
          try {
            await fetch(
              `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/github/connect`,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${data.session.access_token}`,
                },
                body: JSON.stringify({
                  provider_uid: ghUser?.provider_id || data.session.user.id,
                  username: ghUser?.user_name || ghUser?.preferred_username || "",
                  access_token: ghToken,
                  scopes: ["read:user", "repo"],
                }),
              }
            );
          } catch {
            // Non-blocking — user can still proceed
            console.error("Failed to store GitHub token");
          }
        }
      }

      // Check if user is onboarded
      const { data: userData } = await supabase
        .from("users")
        .select("onboarded")
        .eq("id", data.session.user.id)
        .single();

      if (userData?.onboarded) {
        return NextResponse.redirect(`${origin}/dashboard`);
      }
      return NextResponse.redirect(`${origin}/onboarding`);
    }
  }

  return NextResponse.redirect(`${origin}/login?error=auth_failed`);
}
