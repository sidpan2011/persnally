import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <span className="text-xl font-bold tracking-tight text-black uppercase">
          Persnally
        </span>
        <Link
          href="/login"
          className="bg-black text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          Get Started
        </Link>
      </nav>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-4 pt-24 pb-16 text-center">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-black leading-tight">
          Your tech news,
          <br />
          <span className="text-gray-400">actually personalized.</span>
        </h1>
        <p className="mt-6 text-lg text-gray-500 max-w-xl mx-auto leading-relaxed">
          Connect your GitHub. Tell us what you care about. Get 5 curated
          updates daily — no noise, no spam, just what matters to you.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/login"
            className="bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Start for Free
          </Link>
          <a
            href="#how-it-works"
            className="text-gray-500 px-4 py-3 font-medium hover:text-black transition-colors"
          >
            How it works
          </a>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="max-w-4xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-black mb-16">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              step: "01",
              title: "Connect GitHub",
              desc: "We analyze your repos, stars, and tech stack to understand what you actually work with.",
            },
            {
              step: "02",
              title: "Set Preferences",
              desc: "Pick your interests, experience level, and content style. Tell us what excites you.",
            },
            {
              step: "03",
              title: "Get Your Daily 5",
              desc: "Every day, our AI crawls the internet and sends you 5 hand-picked updates via email.",
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

      {/* Features */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-black mb-16">
            What Makes It Different
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                title: "Real-Time Web Crawling",
                desc: "We crawl 13+ sources including TechCrunch, HackerNews, GitHub Trending, Product Hunt, and more. Content is always fresh — max 3 days old.",
              },
              {
                title: "GitHub-Aware Intelligence",
                desc: "Your repos and stars tell us your real tech stack. We use that as context (not surveillance) to match content to your actual skill level.",
              },
              {
                title: "AI-Powered Curation",
                desc: "Claude AI reads, scores, and validates every recommendation. Broken links? Spam? Vague claims? Automatically rejected.",
              },
              {
                title: "Quality Over Quantity",
                desc: "Exactly 5 items per day. Each one verified, balanced, and relevant. We'd rather skip a day than send you garbage.",
              },
              {
                title: "Balanced & Diverse",
                desc: "No echo chambers. Each newsletter covers different sources, different topics, and different angles — keeping things interesting.",
              },
              {
                title: "Free & Open Source",
                desc: "Persnally is free to use and open source. No paywalls, no tracking pixels, no selling your data.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="bg-white rounded-lg border border-gray-200 p-6"
              >
                <h3 className="font-semibold text-black mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sources */}
      <section className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold text-black mb-4">
          We Crawl the Internet For You
        </h2>
        <p className="text-gray-500 mb-10">
          Real-time data from sources you trust.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {[
            "GitHub Trending",
            "HackerNews",
            "TechCrunch",
            "The Verge",
            "Wired",
            "Product Hunt",
            "Dev.to",
            "Reddit",
            "Devpost",
            "GitHub Blog",
            "OpenAI Blog",
            "Anthropic Blog",
            "Y Combinator",
          ].map((source) => (
            <span
              key={source}
              className="px-4 py-2 bg-gray-100 rounded-full text-sm text-gray-600 font-medium"
            >
              {source}
            </span>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold text-black mb-4">
          Stop drowning in newsletters.
        </h2>
        <p className="text-gray-500 mb-8">
          Get one that actually knows you.
        </p>
        <Link
          href="/login"
          className="inline-block bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
        >
          Get Started — It&apos;s Free
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-5xl mx-auto px-4 flex items-center justify-between text-sm text-gray-400">
          <span className="font-bold tracking-tight text-black uppercase">
            Persnally
          </span>
          <span>Open source &middot; Free forever</span>
        </div>
      </footer>
    </div>
  );
}
