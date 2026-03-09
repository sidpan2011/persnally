/**
 * Digest Client — Sends interest graph to the Persnally API for digest generation.
 *
 * When the user triggers `persnally_digest` (not preview), the MCP server
 * sends the interest graph to the API, which runs the full curation pipeline
 * and sends the email via Resend.
 *
 * The API URL and API key are configured via persnally_config or env vars.
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const CONFIG_FILE = join(homedir(), ".persnally", "config.json");

interface DigestPayload {
  email: string;
  interest_graph: {
    topics: Array<{ topic: string; weight: number; category: string; intent: string; entities: string[] }>;
    categories: Record<string, number>;
    total_signals: number;
  };
  balanced_allocation: Record<string, {
    allocation: number;
    topics: Array<{ topic: string; weight: number; intent: string; entities: string[] }>;
  }>;
  preferences: {
    max_items: number;
    frequency: string;
  };
}

interface DigestResponse {
  job_id: string;
  status: string;
}

export class DigestClient {
  private apiUrl: string;
  private apiKey: string;

  constructor() {
    // Load from config or env
    const config = this.loadConfig();
    this.apiUrl = config.api_url || process.env.PERSNALLY_API_URL || "https://api.persnally.com";
    this.apiKey = config.api_key || process.env.PERSNALLY_API_KEY || "";
  }

  private loadConfig(): Record<string, string> {
    try {
      if (existsSync(CONFIG_FILE)) {
        const data = readFileSync(CONFIG_FILE, "utf-8");
        return JSON.parse(data);
      }
    } catch {
      // Ignore
    }
    return {};
  }

  /**
   * Send digest request to the API.
   * Returns job_id for polling, or null if API is not configured.
   */
  async requestDigest(payload: DigestPayload): Promise<DigestResponse | null> {
    if (!this.apiKey && !payload.email) {
      return null;
    }

    try {
      const response = await fetch(`${this.apiUrl}/digest/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(this.apiKey ? { "X-API-Key": this.apiKey } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const text = await response.text();
        console.error(`Digest API error (${response.status}): ${text}`);
        return null;
      }

      return await response.json() as DigestResponse;
    } catch (error) {
      console.error("Failed to reach digest API:", error);
      return null;
    }
  }

  /**
   * Sync interest graph to cloud (non-blocking, best-effort).
   */
  async syncGraph(email: string, interestGraph: DigestPayload["interest_graph"]): Promise<void> {
    if (!this.apiKey) return;

    try {
      await fetch(`${this.apiUrl}/digest/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": this.apiKey,
        },
        body: JSON.stringify({
          email,
          interest_graph: interestGraph,
          total_signals: interestGraph.total_signals,
        }),
      });
    } catch {
      // Best-effort, don't block
    }
  }
}
