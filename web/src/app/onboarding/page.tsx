"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";

const INTEREST_OPTIONS = [
  "AI/ML",
  "Web Development",
  "Mobile Development",
  "DevOps/Cloud",
  "Data Science",
  "Cybersecurity",
  "Blockchain/Web3",
  "Open Source",
  "Startups/VC",
  "Hackathons",
  "Product Development",
  "Systems Programming",
  "Game Development",
  "Developer Tools",
];

const EXPERIENCE_LEVELS = [
  { value: "beginner", label: "Beginner", desc: "Just getting started" },
  { value: "intermediate", label: "Intermediate", desc: "Building projects" },
  {
    value: "intermediate_to_advanced",
    label: "Advanced",
    desc: "Shipping production code",
  },
  { value: "expert", label: "Expert", desc: "Leading architecture decisions" },
];

const CONTENT_STYLES = [
  {
    value: "technical",
    label: "Deep Technical",
    desc: "Code-first, implementation details",
  },
  {
    value: "technical_with_business_context",
    label: "Technical + Business",
    desc: "Tech trends with market context",
  },
  {
    value: "business_focused",
    label: "Business Focused",
    desc: "Industry news, funding, launches",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  const [githubUsername, setGithubUsername] = useState("");

  const [interests, setInterests] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("intermediate");
  const [location, setLocation] = useState("");
  const [contentStyle, setContentStyle] = useState(
    "technical_with_business_context"
  );
  const [opportunityTypes, setOpportunityTypes] = useState([
    "hackathons",
    "jobs",
    "funding",
  ]);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push("/login");
        return;
      }
      setToken(session.access_token);
      setGithubUsername(
        session.user.user_metadata?.user_name ||
          session.user.user_metadata?.preferred_username ||
          ""
      );
    });
  }, [router]);

  const toggleInterest = (interest: string) => {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((i) => i !== interest)
        : [...prev, interest]
    );
  };

  const addCustomInterest = () => {
    const trimmed = customInterest.trim();
    if (trimmed && !interests.includes(trimmed)) {
      setInterests((prev) => [...prev, trimmed]);
      setCustomInterest("");
    }
  };

  const toggleOpportunity = (type: string) => {
    setOpportunityTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleComplete = async () => {
    if (!token) return;
    setLoading(true);

    try {
      await apiFetch("/preferences", token, {
        method: "PUT",
        body: JSON.stringify({
          interests: interests.map((i) => i.toLowerCase()),
          experience_level: experienceLevel,
          location,
          content_style: contentStyle,
          prioritize_local: !!location,
          opportunity_types: opportunityTypes,
        }),
      });

      await apiFetch("/users/me", token, {
        method: "PATCH",
        body: JSON.stringify({ onboarded: true }),
      });

      router.push("/dashboard");
    } catch (err) {
      console.error("Onboarding error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
      <div className="max-w-xl w-full">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-10">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full transition-colors ${
                s <= step ? "bg-black" : "bg-gray-200"
              }`}
            />
          ))}
        </div>

        {/* Step 1: GitHub Connected */}
        {step === 1 && (
          <div>
            <h2 className="text-2xl font-bold mb-2">GitHub Connected</h2>
            <p className="text-gray-500 mb-8">
              We&apos;ll analyze your repos to understand your tech stack and
              interests.
            </p>

            <div className="border border-gray-200 rounded-lg p-4 flex items-center gap-4 mb-8">
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </div>
              <div>
                <div className="font-medium text-black">
                  @{githubUsername || "loading..."}
                </div>
                <div className="text-sm text-green-600">Connected</div>
              </div>
            </div>

            <button
              onClick={() => setStep(2)}
              className="w-full bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors cursor-pointer"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 2: Interests */}
        {step === 2 && (
          <div>
            <h2 className="text-2xl font-bold mb-2">
              What are you interested in?
            </h2>
            <p className="text-gray-500 mb-8">
              Select topics you want to stay updated on. Pick at least 3.
            </p>

            <div className="flex flex-wrap gap-2 mb-6">
              {INTEREST_OPTIONS.map((interest) => (
                <button
                  key={interest}
                  onClick={() => toggleInterest(interest)}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors cursor-pointer ${
                    interests.includes(interest)
                      ? "bg-black text-white border-black"
                      : "bg-white text-gray-700 border-gray-200 hover:border-gray-400"
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>

            <div className="flex gap-2 mb-8">
              <input
                type="text"
                value={customInterest}
                onChange={(e) => setCustomInterest(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addCustomInterest()}
                placeholder="Add custom interest..."
                className="flex-1 border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-black"
              />
              <button
                onClick={addCustomInterest}
                className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors cursor-pointer"
              >
                Add
              </button>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-3 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors cursor-pointer"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={interests.length < 3}
                className="flex-1 bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed cursor-pointer"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Preferences */}
        {step === 3 && (
          <div>
            <h2 className="text-2xl font-bold mb-2">Fine-tune your feed</h2>
            <p className="text-gray-500 mb-8">
              Help us personalize your daily briefing.
            </p>

            {/* Experience Level */}
            <div className="mb-6">
              <label className="text-sm font-medium text-gray-700 mb-3 block">
                Experience Level
              </label>
              <div className="grid grid-cols-2 gap-2">
                {EXPERIENCE_LEVELS.map((level) => (
                  <button
                    key={level.value}
                    onClick={() => setExperienceLevel(level.value)}
                    className={`p-3 rounded-lg border text-left transition-colors cursor-pointer ${
                      experienceLevel === level.value
                        ? "border-black bg-gray-50"
                        : "border-gray-200 hover:border-gray-400"
                    }`}
                  >
                    <div className="font-medium text-sm">{level.label}</div>
                    <div className="text-xs text-gray-500">{level.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Content Style */}
            <div className="mb-6">
              <label className="text-sm font-medium text-gray-700 mb-3 block">
                Content Style
              </label>
              <div className="space-y-2">
                {CONTENT_STYLES.map((style) => (
                  <button
                    key={style.value}
                    onClick={() => setContentStyle(style.value)}
                    className={`w-full p-3 rounded-lg border text-left transition-colors cursor-pointer ${
                      contentStyle === style.value
                        ? "border-black bg-gray-50"
                        : "border-gray-200 hover:border-gray-400"
                    }`}
                  >
                    <div className="font-medium text-sm">{style.label}</div>
                    <div className="text-xs text-gray-500">{style.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Location */}
            <div className="mb-6">
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Location (for local events & news)
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. San Francisco, USA"
                className="w-full border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-black"
              />
            </div>

            {/* Opportunity Types */}
            <div className="mb-8">
              <label className="text-sm font-medium text-gray-700 mb-3 block">
                I want to hear about
              </label>
              <div className="flex flex-wrap gap-2">
                {["hackathons", "jobs", "funding", "events", "conferences"].map(
                  (type) => (
                    <button
                      key={type}
                      onClick={() => toggleOpportunity(type)}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors capitalize cursor-pointer ${
                        opportunityTypes.includes(type)
                          ? "bg-black text-white border-black"
                          : "bg-white text-gray-700 border-gray-200 hover:border-gray-400"
                      }`}
                    >
                      {type}
                    </button>
                  )
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(2)}
                className="px-6 py-3 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors cursor-pointer"
              >
                Back
              </button>
              <button
                onClick={handleComplete}
                disabled={loading}
                className="flex-1 bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-300 cursor-pointer"
              >
                {loading ? "Setting up..." : "Start Getting Updates"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
