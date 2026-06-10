/**
 * EventStore — append-only SQLite event log plus rebuildable derived views.
 * Single source of truth per docs/EVENT_SCHEMA.md; views can always be re-derived.
 */

import Database from "better-sqlite3";
import { mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { normalizeTopic, validateEvent, type PersnallyEvent } from "./events.js";

export const DEFAULT_DB_PATH = join(homedir(), ".persnally", "persnally.db");

export interface QueryOpts {
  type?: string;
  source?: string;
  since?: string;
  limit?: number;
}

export interface TopicRow {
  topic_key: string;
  topic: string;
  category: string;
  signals: number;
  weight: number;
  entities: string[];
  first_seen: string;
  last_seen: string;
  event_ids: string[];
}

export class EventStore {
  private db: Database.Database;

  constructor(path: string = DEFAULT_DB_PATH) {
    mkdirSync(dirname(path), { recursive: true });
    this.db = new Database(path);
    this.db.pragma("journal_mode = WAL");
    this.migrate();
  }

  private migrate(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS events (
        id          TEXT PRIMARY KEY,
        ts          TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        source      TEXT NOT NULL,
        type        TEXT NOT NULL,
        payload     TEXT NOT NULL,
        provenance  TEXT NOT NULL,
        schema_ver  INTEGER NOT NULL DEFAULT 1
      );
      CREATE INDEX IF NOT EXISTS idx_events_ts   ON events (ts);
      CREATE INDEX IF NOT EXISTS idx_events_type ON events (type, ts);
      CREATE INDEX IF NOT EXISTS idx_events_src  ON events (source, ts);
      CREATE TABLE IF NOT EXISTS view_topics (
        topic_key  TEXT PRIMARY KEY,
        topic      TEXT NOT NULL,
        category   TEXT NOT NULL,
        signals    INTEGER NOT NULL,
        weight     REAL NOT NULL,
        entities   TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_seen  TEXT NOT NULL,
        event_ids  TEXT NOT NULL
      );
    `);
  }

  append(events: PersnallyEvent[]): number {
    const insert = this.db.prepare(
      `INSERT INTO events (id, ts, recorded_at, source, type, payload, provenance, schema_ver)
       VALUES (@id, @ts, @recorded_at, @source, @type, @payload, @provenance, @schema_ver)`,
    );
    const run = this.db.transaction((batch: PersnallyEvent[]) => {
      for (const raw of batch) {
        const e = validateEvent(raw);
        insert.run({
          ...e,
          payload: JSON.stringify(e.payload),
          provenance: JSON.stringify(e.provenance),
        });
      }
    });
    run(events);
    return events.length;
  }

  query(opts: QueryOpts = {}): PersnallyEvent[] {
    const where: string[] = [];
    const params: Record<string, unknown> = {};
    if (opts.type) { where.push("type = @type"); params.type = opts.type; }
    if (opts.source) { where.push("source = @source"); params.source = opts.source; }
    if (opts.since) { where.push("ts >= @since"); params.since = opts.since; }
    const sql = `SELECT * FROM events ${where.length ? "WHERE " + where.join(" AND ") : ""}
                 ORDER BY ts DESC LIMIT @limit`;
    params.limit = opts.limit ?? 100;
    return this.db.prepare(sql).all(params).map(rowToEvent);
  }

  stats(): { total: number; byType: Record<string, number>; bySource: Record<string, number>; first: string | null; last: string | null } {
    const total = (this.db.prepare("SELECT COUNT(*) n FROM events").get() as { n: number }).n;
    const group = (col: string) =>
      Object.fromEntries(
        (this.db.prepare(`SELECT ${col} k, COUNT(*) n FROM events GROUP BY ${col}`).all() as { k: string; n: number }[])
          .map((r) => [r.k, r.n]),
      );
    const span = this.db.prepare("SELECT MIN(ts) first, MAX(ts) last FROM events").get() as { first: string | null; last: string | null };
    return { total, byType: group("type"), bySource: group("source"), ...span };
  }

  topics(limit = 50): TopicRow[] {
    const rows = this.db
      .prepare("SELECT * FROM view_topics ORDER BY weight DESC LIMIT ?")
      .all(limit) as Array<Omit<TopicRow, "entities" | "event_ids"> & { entities: string; event_ids: string }>;
    return rows.map((r) => ({ ...r, entities: JSON.parse(r.entities), event_ids: JSON.parse(r.event_ids) }));
  }

  /**
   * Re-derive view_topics from signal.topic events.
   * TODO(phase1): port decay/sentiment weighting from interest-engine.ts —
   * with the known fix for the raw_weight frequency double-count.
   */
  rebuild(): void {
    this.db.exec("DELETE FROM view_topics");
    const topics = new Map<string, TopicRow>();
    for (const e of this.query({ type: "signal.topic", limit: 1_000_000 })) {
      const p = e.payload as { topic: string; weight: number; category: string; depth: string; entities: string[] };
      const key = normalizeTopic(p.topic);
      if (!key) continue;
      const depthScore = { mention: 0.3, moderate: 0.6, deep: 1.0 }[p.depth] ?? 0.3;
      const existing = topics.get(key);
      if (existing) {
        existing.signals += 1;
        existing.weight += p.weight * depthScore;
        existing.entities = [...new Set([...existing.entities, ...p.entities])].slice(0, 20);
        existing.first_seen = e.ts < existing.first_seen ? e.ts : existing.first_seen;
        existing.last_seen = e.ts > existing.last_seen ? e.ts : existing.last_seen;
        existing.event_ids.push(e.id);
      } else {
        topics.set(key, {
          topic_key: key,
          topic: p.topic,
          category: p.category,
          signals: 1,
          weight: p.weight * depthScore,
          entities: p.entities.slice(0, 20),
          first_seen: e.ts,
          last_seen: e.ts,
          event_ids: [e.id],
        });
      }
    }
    const insert = this.db.prepare(
      `INSERT INTO view_topics VALUES (@topic_key, @topic, @category, @signals, @weight, @entities, @first_seen, @last_seen, @event_ids)`,
    );
    const run = this.db.transaction((rows: TopicRow[]) => {
      for (const r of rows) {
        insert.run({ ...r, entities: JSON.stringify(r.entities), event_ids: JSON.stringify(r.event_ids) });
      }
    });
    run([...topics.values()]);
  }

  /** Hard-deletes matching topic events plus derived events referencing them, then rebuilds. */
  forgetTopic(topic: string): number {
    const key = normalizeTopic(topic);
    const candidates = this.query({ type: "signal.topic", limit: 1_000_000 }).filter(
      (e) => normalizeTopic((e.payload as { topic: string }).topic) === key,
    );
    const ids = new Set(candidates.map((e) => e.id));
    for (const e of this.query({ limit: 1_000_000 })) {
      const prov = e.provenance as { kind: string; from?: string[] };
      if (prov.kind === "derived" && prov.from?.some((id) => ids.has(id))) ids.add(e.id);
    }
    const del = this.db.prepare("DELETE FROM events WHERE id = ?");
    const run = this.db.transaction((toDelete: string[]) => {
      for (const id of toDelete) del.run(id);
    });
    run([...ids]);
    this.rebuild();
    return ids.size;
  }

  /** Removes every event from one import batch — a bad import is fully reversible. */
  forgetBatch(batch: string): number {
    const result = this.db
      .prepare("DELETE FROM events WHERE json_extract(provenance, '$.batch') = ?")
      .run(batch);
    this.rebuild();
    return result.changes;
  }

  forgetAll(): void {
    this.db.exec("DELETE FROM events; DELETE FROM view_topics;");
  }

  close(): void {
    this.db.close();
  }
}

function rowToEvent(row: unknown): PersnallyEvent {
  const r = row as Record<string, string | number>;
  return {
    ...r,
    payload: JSON.parse(r.payload as string),
    provenance: JSON.parse(r.provenance as string),
  } as PersnallyEvent;
}
