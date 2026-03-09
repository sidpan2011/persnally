import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <span className="text-xl font-bold tracking-tight text-black uppercase">
          Persnally
        </span>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/sidpan2011/persnally"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500 hover:text-black transition-colors"
          >
            GitHub
          </a>
          <a
            href="#install"
            className="bg-black text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            Install
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-4 pt-24 pb-16 text-center">
        <div className="inline-block mb-6 px-3 py-1 rounded-full bg-gray-100 text-xs font-medium text-gray-600">
          Open Source MCP Server
        </div>
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-black leading-tight">
          Your AI already knows
          <br />
          <span className="text-gray-400">what you care about.</span>
        </h1>
        <p className="mt-6 text-lg text-gray-500 max-w-xl mx-auto leading-relaxed">
          Persnally is an MCP server that learns from your conversations with
          Claude. It builds a private interest graph and sends you a
          personalized digest — no setup, no surveys, just chat.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <a
            href="#install"
            className="bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Install in 2 Minutes
          </a>
          <a
            href="#how-it-works"
            className="text-gray-500 px-4 py-3 font-medium hover:text-black transition-colors"
          >
            How it works
          </a>
        </div>
      </section>

      {/* Terminal Preview */}
      <section className="max-w-2xl mx-auto px-4 pb-20">
        <div className="bg-gray-950 rounded-xl border border-gray-800 overflow-hidden shadow-2xl">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="ml-2 text-xs text-gray-500 font-mono">
              claude desktop
            </span>
          </div>
          <div className="p-6 font-mono text-sm leading-relaxed">
            <p className="text-gray-400">
              <span className="text-blue-400">you:</span> I&apos;m building a
              real-time data pipeline with Kafka and Rust. Trying to decide
              between rdkafka and kafka-rust...
            </p>
            <p className="text-gray-400 mt-4">
              <span className="text-green-400">claude:</span> Let me compare
              both libraries for your use case...
            </p>
            <p className="text-gray-600 mt-4 text-xs">
              <span className="text-purple-400">persnally</span> tracked:{" "}
              <span className="text-gray-400">
                Rust async programming (0.9), Kafka data pipelines (0.8),
                systems architecture (0.5)
              </span>
            </p>
            <p className="text-gray-600 mt-2 text-xs italic">
              No raw messages stored. Only structured signals.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="max-w-4xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-black mb-4">
          How It Works
        </h2>
        <p className="text-center text-gray-500 mb-16 max-w-lg mx-auto">
          Persnally runs silently alongside your AI conversations. No behavior
          change required.
        </p>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              step: "01",
              title: "Install the MCP server",
              desc: "One npm install, add to your Claude Desktop config. Takes under 2 minutes. Persnally runs locally on your machine.",
            },
            {
              step: "02",
              title: "Chat like you normally do",
              desc: "As you discuss topics with Claude, Persnally extracts structured signals — topics, intent, sentiment, depth. Claude IS the NLP engine.",
            },
            {
              step: "03",
              title: "Get your personalized digest",
              desc: "Daily or weekly, Persnally curates content matched to your interest graph and sends it via email. Real links, real articles, zero filler.",
            },
          ].map((item) => (
            <div key={item.step}>
              <div className="text-sm font-mono text-gray-400 mb-3">
                {item.step}
              </div>
              <h3 className="text-lg font-semibold text-black mb-2">
                {item.title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* The Insight */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-black mb-6">
            The key insight
          </h2>
          <p className="text-xl text-gray-600 leading-relaxed mb-8">
            Every other recommendation engine asks you to fill out surveys, rate
            things, or connect accounts. Persnally doesn&apos;t need any of
            that.
          </p>
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-left max-w-xl mx-auto">
            <p className="text-gray-800 leading-relaxed">
              When you talk to Claude about Rust async programming, startup
              fundraising, or LLM fine-tuning —{" "}
              <strong>
                Claude already understands the context, sentiment, and depth
              </strong>
              . Persnally just gives it a structured way to report what it
              observed. Zero extra AI cost. Zero NLP pipeline.
            </p>
            <p className="mt-4 text-sm text-gray-500">
              Your conversations are the most honest signal of what you care
              about. Not what you say you like — what you actually spend time
              on.
            </p>
          </div>
        </div>
      </section>

      {/* Interest Graph */}
      <section className="max-w-4xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-black mb-4">
          A living interest graph
        </h2>
        <p className="text-center text-gray-500 mb-12 max-w-lg mx-auto">
          Not a static preference list. A weighted, decaying, sentiment-aware
          graph that evolves as you do.
        </p>
        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              title: "Exponential Decay",
              desc: "Topics you discussed months ago fade naturally. What you talked about yesterday carries more weight. 7-day half-life keeps the graph fresh.",
            },
            {
              title: "Sentiment Awareness",
              desc: "\"I hate CSS\" and \"I love CSS\" are very different signals. Negative sentiment deprioritizes topics — no frustrated content in your digest.",
            },
            {
              title: "Depth Scoring",
              desc: "A brief mention of React scores differently than a 30-minute deep dive on React Server Components. Depth matters.",
            },
            {
              title: "Balanced Allocation",
              desc: "Your digest covers multiple interest categories proportionally. No echo chambers — technology, business, career, science all get fair weight.",
            },
            {
              title: "Topic Normalization",
              desc: "\"React.js\", \"React JS\", and \"ReactJS\" all map to the same node. The graph handles synonyms so you get clean, deduplicated interests.",
            },
            {
              title: "Intent Tracking",
              desc: "Are you learning, building, researching, or debugging? Intent shapes what content gets surfaced — tutorials vs deep dives vs release notes.",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <h3 className="font-semibold text-black mb-2">{feature.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Privacy */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-black mb-4">
            Privacy by architecture
          </h2>
          <p className="text-center text-gray-500 mb-12 max-w-lg mx-auto">
            Not privacy by policy. By architecture. Raw conversations never
            leave your machine.
          </p>
          <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto">
            <div>
              <h3 className="font-semibold text-black mb-4">
                What IS stored
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span>
                  <span>Topic name (e.g., &quot;Rust async&quot;)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span>
                  <span>Weight (0.1 to 1.0)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span>
                  <span>Category, intent, sentiment</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span>
                  <span>Entity names (e.g., &quot;tokio&quot;, &quot;axum&quot;)</span>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-black mb-4">
                What is NEVER stored
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">&times;</span>
                  <span>Your messages or conversations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">&times;</span>
                  <span>Claude&apos;s responses</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">&times;</span>
                  <span>Code snippets or file contents</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">&times;</span>
                  <span>Personal information or secrets</span>
                </li>
              </ul>
            </div>
          </div>
          <p className="text-center text-sm text-gray-400 mt-10">
            Your interest graph is a JSON file on your machine. You can read it,
            edit it, or delete it anytime.
            <br />
            Use <code className="bg-gray-200 px-1.5 py-0.5 rounded text-gray-600">persnally_forget</code> to
            remove any topic, or clear everything.
          </p>
        </div>
      </section>

      {/* Install */}
      <section id="install" className="max-w-3xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-black mb-4">
          Get started in 2 minutes
        </h2>
        <p className="text-center text-gray-500 mb-10">
          Install the MCP server and add it to Claude Desktop.
        </p>

        {/* Step 1 */}
        <div className="mb-8">
          <div className="text-sm font-mono text-gray-400 mb-2">
            1. Install globally
          </div>
          <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-300">
            <span className="text-green-400">$</span> npm install -g persnally
          </div>
        </div>

        {/* Step 2 */}
        <div className="mb-8">
          <div className="text-sm font-mono text-gray-400 mb-2">
            2. Add to Claude Desktop config
          </div>
          <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-300 overflow-x-auto">
            <pre>{`{
  "mcpServers": {
    "persnally": {
      "command": "persnally",
      "args": []
    }
  }
}`}</pre>
          </div>
        </div>

        {/* Step 3 */}
        <div className="mb-8">
          <div className="text-sm font-mono text-gray-400 mb-2">
            3. Set your email
          </div>
          <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-300">
            <span className="text-gray-500">
              Tell Claude:
            </span>{" "}
            &quot;Set my Persnally email to me@example.com&quot;
          </div>
        </div>

        {/* Step 4 */}
        <div>
          <div className="text-sm font-mono text-gray-400 mb-2">
            4. Just chat
          </div>
          <p className="text-sm text-gray-500 leading-relaxed">
            That&apos;s it. Persnally will start learning from your conversations
            automatically. Ask Claude &quot;show my Persnally interests&quot;
            anytime to see what&apos;s been tracked.
          </p>
        </div>
      </section>

      {/* MCP Tools */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-black mb-4">
            5 tools, zero complexity
          </h2>
          <p className="text-center text-gray-500 mb-12 max-w-lg mx-auto">
            Persnally exposes 5 MCP tools that Claude calls automatically during
            your conversations.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                name: "persnally_track",
                desc: "Extracts topics, intent, and sentiment from the current conversation. Called automatically by Claude.",
              },
              {
                name: "persnally_interests",
                desc: "Shows your current interest profile — what Persnally has learned, grouped by category.",
              },
              {
                name: "persnally_digest",
                desc: "Generates and sends your personalized digest email based on your interest graph.",
              },
              {
                name: "persnally_config",
                desc: "Set your email, digest frequency (daily/weekly), and API preferences.",
              },
              {
                name: "persnally_forget",
                desc: "Remove a specific topic or clear all data. Your data, your control.",
              },
            ].map((tool) => (
              <div
                key={tool.name}
                className="bg-white rounded-lg border border-gray-200 p-5"
              >
                <code className="text-sm font-mono font-semibold text-black">
                  {tool.name}
                </code>
                <p className="text-gray-500 text-sm mt-2 leading-relaxed">
                  {tool.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Source CTA */}
      <section className="max-w-3xl mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold text-black mb-4">
          Open source. Local first. Yours forever.
        </h2>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          Persnally is fully open source under MIT. Your interest graph lives on
          your machine. No vendor lock-in, no data silos.
        </p>
        <div className="flex items-center justify-center gap-4">
          <a
            href="https://github.com/sidpan2011/persnally"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            View on GitHub
          </a>
          <a
            href="#install"
            className="inline-block border border-gray-300 text-black px-8 py-3 rounded-lg font-medium hover:border-black transition-colors"
          >
            Install Now
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-5xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-400">
          <span className="font-bold tracking-tight text-black uppercase">
            Persnally
          </span>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/sidpan2011/persnally"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-black transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://www.npmjs.com/package/persnally"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-black transition-colors"
            >
              npm
            </a>
            <Link href="/login" className="hover:text-black transition-colors">
              Dashboard
            </Link>
          </div>
          <span>Open source &middot; MIT License</span>
        </div>
      </footer>
    </div>
  );
}
