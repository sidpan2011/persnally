"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

const INTEREST_OPTIONS = [
  "AI/ML", "Web Development", "Mobile Development", "DevOps/Cloud",
  "Data Science", "Cybersecurity", "Blockchain/Web3", "Open Source",
  "Startups/VC", "Hackathons", "Product Development", "Systems Programming",
  "Game Development", "Developer Tools",
];

export default function PreferencesPage() {
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const [interests, setInterests] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("intermediate");
  const [location, setLocation] = useState("");
  const [contentStyle, setContentStyle] = useState("technical_with_business_context");
  const [opportunityTypes, setOpportunityTypes] = useState<string[]>(["hackathons", "jobs", "funding"]);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setToken(session.access_token);
    });
  }, []);

  const loadPrefs = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiFetch("/preferences", token);
      if (data.interests) setInterests(data.interests);
      if (data.experience_level) setExperienceLevel(data.experience_level);
      if (data.location) setLocation(data.location);
      if (data.content_style) setContentStyle(data.content_style);
      if (data.opportunity_types) setOpportunityTypes(data.opportunity_types);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) loadPrefs();
  }, [token, loadPrefs]);

  const toggleInterest = (interest: string) => {
    setInterests((prev) =>
      prev.includes(interest.toLowerCase())
        ? prev.filter((i) => i !== interest.toLowerCase())
        : [...prev, interest.toLowerCase()]
    );
  };

  const addCustom = () => {
    const t = customInterest.trim().toLowerCase();
    if (t && !interests.includes(t)) {
      setInterests((prev) => [...prev, t]);
      setCustomInterest("");
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await apiFetch("/preferences", token, {
        method: "PUT",
        body: JSON.stringify({
          interests,
          experience_level: experienceLevel,
          location,
          content_style: contentStyle,
          prioritize_local: !!location,
          opportunity_types: opportunityTypes,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-black mb-6">Preferences</h1>

      {/* Interests */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Interests</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {INTEREST_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => toggleInterest(opt)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors cursor-pointer ${
                interests.includes(opt.toLowerCase())
                  ? "bg-black text-white border-black"
                  : "border-gray-200 text-gray-600 hover:border-gray-400"
              }`}
            >
              {opt}
            </button>
          ))}
          {interests
            .filter((i) => !INTEREST_OPTIONS.map((o) => o.toLowerCase()).includes(i))
            .map((custom) => (
              <span key={custom} className="px-3 py-1.5 rounded-full text-sm bg-black text-white border border-black">
                {custom}
                <button onClick={() => setInterests((p) => p.filter((x) => x !== custom))} className="ml-1 cursor-pointer">&times;</button>
              </span>
            ))}
        </div>
        <div className="flex gap-2">
          <input
            value={customInterest}
            onChange={(e) => setCustomInterest(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addCustom()}
            placeholder="Add custom..."
            className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-black"
          />
          <button onClick={addCustom} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 cursor-pointer">Add</button>
        </div>
      </section>

      {/* Experience */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Experience Level</h3>
        <select
          value={experienceLevel}
          onChange={(e) => setExperienceLevel(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-black"
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="intermediate_to_advanced">Advanced</option>
          <option value="expert">Expert</option>
        </select>
      </section>

      {/* Content Style */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Content Style</h3>
        <select
          value={contentStyle}
          onChange={(e) => setContentStyle(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-black"
        >
          <option value="technical">Deep Technical</option>
          <option value="technical_with_business_context">Technical + Business</option>
          <option value="business_focused">Business Focused</option>
        </select>
      </section>

      {/* Location */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Location</h3>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. San Francisco, USA"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-black"
        />
      </section>

      {/* Opportunity Types */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Opportunity Types</h3>
        <div className="flex flex-wrap gap-2">
          {["hackathons", "jobs", "funding", "events", "conferences"].map((type) => (
            <button
              key={type}
              onClick={() =>
                setOpportunityTypes((prev) =>
                  prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
                )
              }
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors capitalize cursor-pointer ${
                opportunityTypes.includes(type)
                  ? "bg-black text-white border-black"
                  : "border-gray-200 text-gray-600 hover:border-gray-400"
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </section>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="bg-black text-white px-6 py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-300 cursor-pointer"
      >
        {saving ? "Saving..." : saved ? "Saved!" : "Save Preferences"}
      </button>
    </div>
  );
}
