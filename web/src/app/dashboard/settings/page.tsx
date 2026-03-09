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
        <div className="text-gray-400 text-sm">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-black">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">
          Manage your digest preferences and account
        </p>
      </div>

      {/* Account */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-black mb-4">Account</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Email</label>
            <div className="text-sm text-gray-800">{email}</div>
          </div>
        </div>
      </section>

      {/* Digest Preferences */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-black mb-4">Digest Preferences</h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Experience Level</label>
            <select
              value={prefs?.experience_level || "intermediate"}
              onChange={(e) => setPrefs(p => p ? { ...p, experience_level: e.target.value } : p)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:border-black focus:outline-none"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">Content Style</label>
            <select
              value={prefs?.content_style || "technical_deep_dive"}
              onChange={(e) => setPrefs(p => p ? { ...p, content_style: e.target.value } : p)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:border-black focus:outline-none"
            >
              <option value="technical_deep_dive">Deep Technical</option>
              <option value="technical_with_business_context">Technical + Business</option>
              <option value="business_focused">Business Focused</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">Location (optional)</label>
            <input
              type="text"
              value={prefs?.location || ""}
              onChange={(e) => setPrefs(p => p ? { ...p, location: e.target.value } : p)}
              placeholder="e.g., San Francisco, USA"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:border-black focus:outline-none"
            />
          </div>
        </div>
      </section>

      {/* MCP Server Setup */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-black mb-2">MCP Server</h2>
        <p className="text-sm text-gray-500 mb-4">
          Install the MCP server to start building your interest graph from Claude conversations.
        </p>
        <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-300 mb-3">
          <span className="text-green-400">$</span> npm install -g persnally
        </div>
        <p className="text-xs text-gray-400">
          Add to Claude Desktop config, then tell Claude: &quot;Set my Persnally email to {email}&quot;
        </p>
      </section>

      {/* Privacy */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-black mb-2">Privacy &amp; Data</h2>
        <p className="text-sm text-gray-500 mb-4">
          Your interest graph is built from structured signals only. Raw conversations are never stored.
        </p>
        <div className="space-y-2 text-sm text-gray-600">
          <p>
            To remove a topic: tell Claude <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">&quot;Remove [topic] from my Persnally profile&quot;</code>
          </p>
          <p>
            To clear all data: tell Claude <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">&quot;Clear all my Persnally data&quot;</code>
          </p>
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center gap-3">
        <button
          onClick={savePrefs}
          disabled={saving}
          className="bg-black text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
        {saved && <span className="text-sm text-green-600">Saved!</span>}
      </div>
    </div>
  );
}
