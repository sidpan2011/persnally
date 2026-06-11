#!/usr/bin/env node
/**
 * persnallyd CLI — the developer's window into the daemon.
 * Merges into the `persnally` npm identity at Phase 1 launch.
 */

import { execFileSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { applyApiKey, configPath, loadConfig, saveConfig } from "./config.js";
import { CLIENTS, connectAll, connectClient, type Client } from "./connect.js";
import { chooseExtractor } from "./llm.js";
import { alreadyImported, detectExports, markImported } from "./setup.js";
import { DEFAULT_PORT, startDaemon, VERSION } from "./daemon.js";
import { extractChatGPTEvents, parseChatGPTExport } from "./importers/chatgpt.js";
import { extractClaudeEvents, parseClaudeExport } from "./importers/claude.js";
import { gitEvents, scanRepos } from "./importers/git.js";
import {
  autostartInstalled, installAutostart, LOG_FILE, removeAutostart,
  removePidFile, runningPid, startDetached, stopDaemon, writePidFile,
} from "./lifecycle.js";
import { renderProfile, synthesizeProfile } from "./profile.js";
import { DEFAULT_DB_PATH, EventStore } from "./store.js";

const USAGE = `persnallyd ${VERSION} — so every AI finally knows you

Usage:
  persnallyd setup                  One command: find exports, import, synthesize, connect, open
  persnallyd connect [client|--all] Add Persnally to claude-code | claude-desktop | cursor
  persnallyd init                   Create the local store (~/.persnally/persnally.db)
  persnallyd import claude <dir>    Import a Claude data export (needs ANTHROPIC_API_KEY)
  persnallyd import chatgpt <path>  Import a ChatGPT export dir or conversations.json (needs ANTHROPIC_API_KEY)
  persnallyd import git <path> [--author <email>]   Import repo activity (offline, no LLM); path = repo or folder of repos
  persnallyd profile                Synthesize your profile from the store (needs ANTHROPIC_API_KEY)
  persnallyd show [topics|events|profile]   Show topics (default), recent events, or the profile
  persnallyd forget <topic>         Hard-delete a topic and everything derived from it
  persnallyd forget --all           Delete all data
  persnallyd forget --batch <id>    Undo one import batch
  persnallyd status                 Store stats and daemon health
  persnallyd start [--port N]       Start the daemon in the background
  persnallyd stop                   Stop the background daemon
  persnallyd serve [--port N]       Run the daemon in the foreground (127.0.0.1:${DEFAULT_PORT})
  persnallyd autostart [--remove]   Start the daemon at login and keep it alive (macOS)
  persnallyd config set-key <key>   Store the Anthropic API key (owner-only file) for the daemon
  persnallyd config                 Show config (key masked)
`;

function parsePort(args: string[]): number {
  const i = args.indexOf("--port");
  return i > -1 && args[i + 1] ? Number(args[i + 1]) : DEFAULT_PORT;
}

async function main(): Promise<void> {
  const [cmd, ...args] = process.argv.slice(2);
  applyApiKey();
  switch (cmd) {
    case "setup": {
      const port = parsePort(args);
      console.log("Persnally setup — so every AI finally knows you.\n");

      // 1. Extraction engine (optional — git-only works without one)
      let engine = null;
      try {
        engine = await chooseExtractor("extract");
        console.log(`✓ Extraction engine: ${engine.label}`);
      } catch {
        console.log("· No extraction engine (no API key, no Ollama) — conversation imports skipped, git still works.");
      }

      // 2. Daemon
      if (!runningPid()) {
        await startDetached(process.argv[1]!, port);
        console.log(`✓ Daemon started (http://127.0.0.1:${port})`);
      } else {
        console.log("✓ Daemon already running");
      }

      // 3. Conversation exports from ~/Downloads (zipped or unzipped)
      const store = new EventStore();
      let imported = 0;
      for (const found of detectExports()) {
        if (alreadyImported(found.origin)) {
          console.log(`· Skipping ${found.origin} (already imported)`);
        } else if (engine) {
          console.log(`→ Importing ${found.kind} export: ${found.origin}`);
          const parsed = found.kind === "claude" ? parseClaudeExport(found.path) : parseChatGPTExport(found.path);
          const result = found.kind === "claude"
            ? await extractClaudeEvents(parsed, engine.extract, engine.model)
            : await extractChatGPTEvents(parsed, engine.extract, engine.model);
          store.append(result.events);
          markImported(found.origin);
          imported += result.events.length;
          console.log(`  ✓ ${result.events.length} events`);
        }
        if (found.cleanup) rmSync(found.cleanup, { recursive: true, force: true });
      }

      // 4. Git activity from ~/Projects
      const projects = join(homedir(), "Projects");
      if (existsSync(projects) && !alreadyImported(projects)) {
        const summaries = scanRepos(projects);
        if (summaries.length) {
          const { events } = gitEvents(summaries);
          store.append(events);
          markImported(projects);
          imported += events.length;
          console.log(`✓ Imported ${summaries.length} git repo(s) from ~/Projects (${events.length} events, fully offline)`);
        }
      }
      store.rebuild();

      // 5. Profile
      if (engine && store.stats().total > 0) {
        console.log("→ Synthesizing your profile…");
        const profileEngine = await chooseExtractor("profile");
        await synthesizeProfile(store, profileEngine.extract, profileEngine.model);
        console.log("  ✓ Profile ready");
      }
      store.close();

      // 6. AI clients
      for (const { client, file } of connectAll()) {
        console.log(file ? `✓ Connected ${client}` : `· ${client} not installed — skipped`);
      }

      console.log(`\nDone${imported ? ` — ${imported} events imported` : ""}. Dashboard: http://127.0.0.1:${port}`);
      if (process.platform === "darwin" && process.stdout.isTTY) {
        try { execFileSync("open", [`http://127.0.0.1:${port}`]); } catch { /* non-fatal */ }
      }
      return;
    }
    case "connect": {
      const target = args[0] === "--all" || !args[0] ? null : (args[0] as Client);
      if (target && !CLIENTS.includes(target)) return die(`unknown client — use ${CLIENTS.join(" | ")} | --all`);
      const results = target ? [{ client: target, file: connectClient(target) }] : connectAll();
      for (const { client, file } of results) {
        console.log(file ? `Connected ${client} (${file})` : `${client} not installed — skipped`);
      }
      return;
    }
    case "config": {
      if (args[0] === "set-key") {
        if (!args[1]?.startsWith("sk-ant-")) return die("expected an Anthropic key (sk-ant-...)");
        saveConfig({ anthropic_api_key: args[1] });
        console.log(`Key saved to ${configPath()} (mode 600). Restart the daemon to apply: persnallyd stop`);
        return;
      }
      const cfg = loadConfig();
      const key = typeof cfg.anthropic_api_key === "string" ? cfg.anthropic_api_key : "";
      console.log(`Config: ${configPath()}`);
      console.log(`anthropic_api_key: ${key ? key.slice(0, 12) + "…" + key.slice(-4) : "(not set)"}`);
      return;
    }
    case "init": {
      const store = new EventStore();
      store.close();
      console.log(`Initialized ${DEFAULT_DB_PATH}`);
      return;
    }
    case "import": {
      const [kind, path] = args;
      if (!kind || !path) return die("usage: persnallyd import claude|chatgpt|git <path>");

      let events, batch;
      if (kind === "git") {
        const authorIdx = args.indexOf("--author");
        const summaries = scanRepos(path, authorIdx > -1 ? args[authorIdx + 1] : undefined);
        if (!summaries.length) return die(`No git repos with your commits found at ${path}`);
        console.error(`Found ${summaries.length} repo(s): ${summaries.map((s) => `${s.repo} (${s.commits} commits)`).join(", ")}`);
        ({ events, batch } = gitEvents(summaries));
      } else if (kind === "claude" || kind === "chatgpt") {
        const engine = await chooseExtractor("extract");
        const parsed = kind === "claude" ? parseClaudeExport(path) : parseChatGPTExport(path);
        console.error(`Parsed ${parsed.conversations.length} conversations. Extracting with ${engine.label}...`);
        ({ events, batch } = kind === "claude"
          ? await extractClaudeEvents(parsed, engine.extract, engine.model)
          : await extractChatGPTEvents(parsed, engine.extract, engine.model));
      } else {
        return die(`unknown import source "${kind}" — use claude, chatgpt, or git`);
      }

      const store = new EventStore();
      store.append(events);
      store.rebuild();
      store.close();
      console.log(`Imported ${events.length} events (batch ${batch}).`);
      console.log(`Undo with: persnallyd forget --batch ${batch}`);
      return;
    }
    case "profile": {
      const engine = await chooseExtractor("profile");
      const store = new EventStore();
      console.error(`Synthesizing profile with ${engine.label}...`);
      const profile = await synthesizeProfile(store, engine.extract, engine.model);
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
      const pid = runningPid();
      console.log(pid ? `Daemon: running (pid ${pid})` : "Daemon: not running");
      console.log(`Autostart: ${autostartInstalled() ? "installed" : "not installed"}`);
      return;
    }
    case "start": {
      const existing = runningPid();
      if (existing) return die(`daemon already running (pid ${existing})`);
      const pid = await startDetached(process.argv[1]!, parsePort(args));
      console.log(`persnallyd started (pid ${pid}). Dashboard: http://127.0.0.1:${parsePort(args)}`);
      console.log(`Logs: ${LOG_FILE}`);
      return;
    }
    case "stop": {
      if (autostartInstalled()) {
        console.error("Note: autostart is installed — launchd will restart the daemon. Use `persnallyd autostart --remove` to stop it permanently.");
      }
      const pid = await stopDaemon();
      console.log(pid ? `Stopped daemon (pid ${pid}).` : "Daemon was not running.");
      return;
    }
    case "autostart": {
      if (args[0] === "--remove") {
        console.log(removeAutostart() ? "Autostart removed; daemon stopped." : "Autostart was not installed.");
        return;
      }
      // A running daemon holds the pidfile and would put launchd in a retry loop — hand over first.
      const stopped = await stopDaemon();
      if (stopped) console.log(`Stopped existing daemon (pid ${stopped}) — launchd takes over.`);
      const plist = installAutostart(process.argv[1]!, parsePort(args));
      console.log(`Autostart installed (${plist}). The daemon now runs at login and restarts if it exits.`);
      return;
    }
    case "serve": {
      const existing = runningPid();
      if (existing) return die(`daemon already running (pid ${existing}) — stop it first`);
      const port = parsePort(args);
      const store = new EventStore();
      const server = startDaemon(store, port);
      server.on("error", (e: NodeJS.ErrnoException) => {
        die(e.code === "EADDRINUSE" ? `port ${port} is already in use` : e.message);
      });
      writePidFile();
      const shutdown = () => {
        server.close();
        store.close();
        removePidFile();
        process.exit(0);
      };
      process.on("SIGTERM", shutdown);
      process.on("SIGINT", shutdown);
      console.error(`persnallyd v${VERSION} listening on 127.0.0.1:${port}`);
      console.error(`Dashboard: http://127.0.0.1:${port}`);
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
