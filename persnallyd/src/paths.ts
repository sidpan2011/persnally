import { homedir } from "node:os";
import { join } from "node:path";

/** All local state lives here. PERSNALLY_DIR override exists for tests and power users. */
export const DATA_DIR = process.env.PERSNALLY_DIR ?? join(homedir(), ".persnally");
