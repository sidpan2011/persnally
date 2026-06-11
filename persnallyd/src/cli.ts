#!/usr/bin/env node
/**
 * persnallyd CLI — the developer's window into the daemon.
 * Merges into the `persnally` npm identity at Phase 1 launch.
 */

import { DEFAULT_PORT, startDaemon, VERSION } from "./daemon.js";
import { parseClaudeExport, extractEvents } from "./importers/claude.js";
import { renderProfile, synthesizeProfile } from "./profile.js";
import { DEFAULT_DB_PATH, EventStore } from "./store.js";

const USAGE = `persnallyd ${VERSION} — so every AI finally knows you

Usage:
  persnallyd init                   Create the local store (~/.persnally/persnally.db)
  persnallyd import claude <dir>    Import a Claude data export (needs ANTHROPIC_API_KEY)
  persnallyd profile                Synthesize your profile from the store (needs ANTHROPIC_API_KEY)
  persnallyd show [topics|events|profile]   Show topics (default), recent events, or the profile
  persnallyd forget <topic>         Hard-delete a topic and everything derived from it
  persnallyd forget --all           Delete all data
  persnallyd forget --batch <id>    Undo one import batch
  persnallyd status                 Store stats and daemon health
  persnallyd serve [--port N]       Run the local HTTP daemon (127.0.0.1:${DEFAULT_PORT})
`;

async function main(): Promise<void> {
  const [cmd, ...args] = process.argv.slice(2);
  switch (cmd) {
    case "init": {
      const store = new EventStore();
      store.close();
      console.log(`Initialized ${DEFAULT_DB_PATH}`);
      return;
    }
    case "import": {
      const [kind, dir] = args;
      if (kind !== "claude" || !dir) return die("usage: persnallyd import claude <export-dir>");
      if (!process.env.ANTHROPIC_API_KEY) return die("ANTHROPIC_API_KEY is required for extraction");
      const parsed = parseClaudeExport(dir);
      console.error(
        `Parsed ${parsed.conversations.length} conversations, ` +
        `${parsed.projects.length} projects, memory: ${parsed.memoryText.length} chars. Extracting...`,
      );
      const { events, batch } = await extractEvents(parsed);
      const store = new EventStore();
      store.append(events);
      store.rebuild();
      store.close();
      console.log(`Imported ${events.length} events (batch ${batch}).`);
      console.log(`Undo with: persnallyd forget --batch ${batch}`);
      return;
    }
    case "profile": {
      if (!process.env.ANTHROPIC_API_KEY) return die("ANTHROPIC_API_KEY is required for synthesis");
      const store = new EventStore();
      console.error("Synthesizing profile from the event store...");
      const profile = await synthesizeProfile(store);
      store.close();
      console.log(renderProfile(profile));
      return;
    }
    case "show": {
      const store = new EventStore();
      if (args[0] === "profile") {
        const p = store.getProfile();
        console.log(p ? renderProfile(p) : "No profile yet. Run: persnallyd profile");
      } else if (args[0] === "events") {
        for (const e of store.query({ limit: 20 })) {
          console.log(`${e.ts}  ${e.type.padEnd(18)} ${e.source.padEnd(16)} ${summarize(e.payload)}`);
        }
      } else {
        const topics = store.topics(25);
        if (!topics.length) console.log("No topics yet. Run an import or connect an MCP client.");
        for (const t of topics) {
          console.log(`${t.weight.toFixed(2).padStart(6)}  ${t.topic} (${t.category}, ${t.signals} signals)`);
        }
      }
      store.close();
      return;
    }
    case "forget": {
      const store = new EventStore();
      if (args[0] === "--all") {
        store.forgetAll();
        console.log("All data deleted.");
      } else if (args[0] === "--batch" && args[1]) {
        console.log(`Deleted ${store.forgetBatch(args[1])} events from batch ${args[1]}.`);
      } else if (args[0]) {
        console.log(`Deleted ${store.forgetTopic(args[0])} events for "${args[0]}".`);
      } else {
        die("usage: persnallyd forget <topic> | --all | --batch <id>");
      }
      store.close();
      return;
    }
    case "status": {
      const store = new EventStore();
      const s = store.stats();
      store.close();
      console.log(`Store: ${DEFAULT_DB_PATH}`);
      console.log(`Events: ${s.total} (${s.first ?? "—"} → ${s.last ?? "—"})`);
      for (const [t, n] of Object.entries(s.byType)) console.log(`  ${t}: ${n}`);
      try {
        const r = await fetch(`http://127.0.0.1:${DEFAULT_PORT}/health`);
        console.log(`Daemon: running (v${((await r.json()) as { version: string }).version})`);
      } catch {
        console.log("Daemon: not running");
      }
      return;
    }
    case "serve": {
      const port = args[0] === "--port" && args[1] ? Number(args[1]) : DEFAULT_PORT;
      const store = new EventStore();
      startDaemon(store, port);
      console.error(`persnallyd v${VERSION} listening on 127.0.0.1:${port}`);
      return;
    }
    default:
      console.log(USAGE);
      process.exitCode = cmd ? 1 : 0;
  }
}

function summarize(payload: Record<string, unknown>): string {
  const s = JSON.stringify(payload);
  return s.length > 80 ? s.slice(0, 77) + "..." : s;
}

function die(msg: string): void {
  console.error(msg);
  process.exit(1);
}

main().catch((e) => die(e instanceof Error ? e.message : String(e)));
