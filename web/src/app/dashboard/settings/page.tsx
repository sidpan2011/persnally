"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

interface Preferences {
  interests: string[];
  experience_level: string;
  content_style: string;
  location: string;
  opportunity_types: string[];
  send_frequency?: string;
}

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadData = useCallback(async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    setEmail(session.user.email || "");

    try {
      const data = await apiFetch("/preferences", session.access_token);
      setPrefs(data);
    } catch {
      setPrefs({
        interests: [],
        experience_level: "intermediate",
        content_style: "technical_deep_dive",
        location: "",
        opportunity_types: ["hackathons", "open_source"],
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const savePrefs = async () => {
    if (!prefs) return;
    setSaving(true);
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    try {
      await apiFetch("/preferences", session.access_token, {
        method: "PUT",
        body: JSON.stringify(prefs),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error("Failed to save:", e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-mute text-sm">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="bg-night text-ink max-w-2xl space-y-8">
      <div>
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt mb-2">
          Settings
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Settings</h1>
        <p className="text-sm text-mute mt-1">
          Manage your digest preferences and account
        </p>
      </div>

      {/* Account */}
      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="font-semibold tracking-tight text-ink mb-4">Account</h2>
        <div className="space-y-3">
          <div>
            <label className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt block mb-1">Email</label>
            <div className="text-sm text-ink">{email}</div>
          </div>
        </div>
      </section>

      {/* Digest Preferences */}
      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="font-semibold tracking-tight text-ink mb-4">Digest Preferences</h2>
        <div className="space-y-4">
          <div>
            <label className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt block mb-1">Experience Level</label>
            <select
              value={prefs?.experience_level || "intermediate"}
              onChange={(e) => setPrefs(p => p ? { ...p, experience_level: e.target.value } : p)}
              className="w-full border border-line bg-panel text-ink rounded-lg px-3 py-2 text-sm focus:border-volt/30 focus:outline-none"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt block mb-1">Content Style</label>
            <select
              value={prefs?.content_style || "technical_deep_dive"}
              onChange={(e) => setPrefs(p => p ? { ...p, content_style: e.target.value } : p)}
              className="w-full border border-line bg-panel text-ink rounded-lg px-3 py-2 text-sm focus:border-volt/30 focus:outline-none"
            >
              <option value="technical_deep_dive">Deep Technical</option>
              <option value="technical_with_business_context">Technical + Business</option>
              <option value="business_focused">Business Focused</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt block mb-1">Location (optional)</label>
            <input
              type="text"
              value={prefs?.location || ""}
              onChange={(e) => setPrefs(p => p ? { ...p, location: e.target.value } : p)}
              placeholder="e.g., San Francisco, USA"
              className="w-full border border-line bg-panel text-ink placeholder:text-faint rounded-lg px-3 py-2 text-sm focus:border-volt/30 focus:outline-none"
            />
          </div>
        </div>
      </section>

      {/* MCP Server Setup */}
      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="font-semibold tracking-tight text-ink mb-2">MCP Server</h2>
        <p className="text-sm text-mute mb-4">
          Install the MCP server to start building your interest graph from Claude conversations.
        </p>
        <div className="rounded-xl border border-line bg-night p-4 font-mono text-[13px] text-ink mb-3">
          <span className="text-volt">$</span> npm install -g persnally
        </div>
        <p className="text-xs text-faint">
          Add to Claude Desktop config, then tell Claude: &quot;Set my Persnally email to {email}&quot;
        </p>
      </section>

      {/* Privacy */}
      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="font-semibold tracking-tight text-ink mb-2">Privacy &amp; Data</h2>
        <p className="text-sm text-mute mb-4">
          Your interest graph is built from structured signals only. Raw conversations are never stored.
        </p>
        <div className="space-y-2 text-sm text-mute">
          <p>
            To remove a topic: tell Claude <code className="bg-panel border border-line px-1.5 py-0.5 rounded font-mono text-xs text-ink">&quot;Remove [topic] from my Persnally profile&quot;</code>
          </p>
          <p>
            To clear all data: tell Claude <code className="bg-panel border border-line px-1.5 py-0.5 rounded font-mono text-xs text-ink">&quot;Clear all my Persnally data&quot;</code>
          </p>
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center gap-3">
        <button
          onClick={savePrefs}
          disabled={saving}
          className="rounded-lg bg-electric px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-volt disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
        {saved && <span className="text-sm text-volt">Saved!</span>}
      </div>
    </div>
  );
}
