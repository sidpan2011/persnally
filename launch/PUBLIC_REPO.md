# Clean public repo — launch runbook

**Goal:** stand up a public repo for the Show HN that contains *only* the engine + sanitized docs, with **no internal strategy in its files or its git history**, while keeping the npm "Repository" link working.

**Why a fresh repo, not a history scrub:** this repo's *commit messages themselves* reference the pivot, fundraise timing, kill criteria, and competitive strategy ("Pivot decided", "launch prep", "Lock business doctrine"…). A `git filter-repo` scrub would have to rewrite history *and* every message, and one miss leaks. A fresh single-commit history is provably clean. The full history stays in the private repo.

---

## Confirm these 3 decisions before running

1. **Name / npm link (recommended: rename the private repo).** `package.json` `repository` → `github.com/sidpan2011/persnally`. The *private* repo holds that name today, which is why the npm link 404s. To make the link resolve to the *public* repo without a republish:
   - Rename private `persnally` → **`persnally-internal`** (GitHub auto-redirects the old URL; we update the local remote). Then create the public repo at `sidpan2011/persnally`.
   - *Alternative:* public repo at a different name + change `repository` in `package.json` → requires a 2.0.4 publish. Not recommended.
2. **History: fresh (recommended) vs scrub.** Fresh single commit. Confirmed above.
3. **`docs/ARCHITECTURE.md`: scrub or omit.** It has 1 line referencing internal strategy (`grep -n "PIVOT\|fundraise\|kill signal\|retention curve" docs/ARCHITECTURE.md`). Either scrub that reference or leave the file out. The rest of it (the eight invariants, the technical model) is fine and good launch material.

**Ongoing model (decide after launch, not now):** simplest long-term is the public `persnally` repo becomes the engine's home (FSL = develop in the open), and `persnally-internal` keeps only PIVOT/PROGRESS/launch + an archive of the old api/web. For launch, just get the snapshot up.

---

## The file split (explicit allowlist — copy only these)

**PUBLIC (goes to the new repo):**
- `persnallyd/` — the package (git-tracked files only; never `node_modules/`, `build/`, `*.tgz`, or the prepublish-copied `persnallyd/README.md`/`LICENSE`)
- `README.md`, `ROADMAP.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`
- `docs/EVENT_SCHEMA.md`, `docs/ARCHITECTURE.md` (after decision #3)
- `.github/workflows/ci.yml` (trimmed to the `persnallyd` job — drop the api/web jobs)
- `.gitignore`

**NEVER public (do not copy):**
- `PIVOT.md`, `PROGRESS.md`, `CLAUDE.md` — strategy/planning
- `launch/` — this kit, demo kit, security review
- `experiments/` — Phase 0 internal scripts
- `web/` — the marketing site (deployed separately to Vercel; not part of the npm package)
- `.env.example` — not part of the package
  <br>*(The v1 Python/Supabase backend — `api/`, `src/`, `supabase/`, `data_sources/`, `nixpacks.toml`, `railway.toml`, `requirements.txt`, `ruff.toml` — was removed entirely on 2026-06-18, so there's nothing left to exclude.)*

Layout choice: keep `persnallyd/` as a subdirectory (don't promote to root). The package already publishes from there; `prepublishOnly` copies `../README.md` + `../LICENSE`, which only works with the package in a subdir. Keeping the layout means **zero changes to the working package** — lowest risk.

---

## Phase 0 — prep inside the private repo (safe, do now)

```bash
# 1. Decide ARCHITECTURE.md (scrub the internal-strategy line or plan to omit)
grep -n "PIVOT\|fundraise\|kill signal\|retention curve\|raise on" docs/ARCHITECTURE.md

# 2. Author a trimmed public CI workflow (persnallyd job only) — save as a separate
#    file you'll copy in, e.g. .github/workflows/ci.public.yml, so you don't disturb
#    the private monorepo CI. It runs: cd persnallyd && npm ci && npm test.

# 3. Restore the CI badge at the top of README.md (it points at the public repo's
#    Actions; it 404s until the repo exists + is public — that's fine, add it now).
```

## Phase 1 — build the clean tree (local, reversible, allowlist-based)

```bash
SRC=/Users/sidhanthpandey/Projects/persnally
OUT=$(mktemp -d)/persnally-public
mkdir -p "$OUT"

# Copy ONLY git-tracked files from the package (excludes node_modules/build/tgz automatically)
git -C "$SRC" ls-files persnallyd | while read -r f; do
  mkdir -p "$OUT/$(dirname "$f")"; cp "$SRC/$f" "$OUT/$f"
done

# Copy the curated root + docs allowlist
for f in README.md ROADMAP.md LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md \
         CHANGELOG.md .gitignore docs/EVENT_SCHEMA.md docs/ARCHITECTURE.md; do
  mkdir -p "$OUT/$(dirname "$f")"; cp "$SRC/$f" "$OUT/$f"
done
mkdir -p "$OUT/.github/workflows"; cp "$SRC/.github/workflows/ci.public.yml" "$OUT/.github/workflows/ci.yml"
```

## Phase 2 — PROVE the tree is clean (the gate — do not skip)

```bash
cd "$OUT"
# Must print NOTHING. If anything lists, stop and remove it.
grep -rIl -E "PIVOT|fundraise|kill signal|kill criteria|retention curve|Show HN|nolabs|supermemory|Mem0 \\\$24M" . \
  --exclude-dir=node_modules 2>/dev/null
# Must list NO internal files/dirs:
ls -a; find . -maxdepth 2 -iname 'PIVOT*' -o -iname 'PROGRESS*' -o -iname 'CLAUDE.md' \
  -o -path './launch*' -o -path './experiments*' -o -path './api*' -o -path './web*' \
  -o -path './supabase*' 2>/dev/null
```
Both commands must come back empty. This is the leak gate.

## Phase 3 — init, free the name, push PRIVATE-first

```bash
cd "$OUT"
git init -q && git add -A
git commit -q -m "Persnally — your own context engine. Local-first, across every AI."

# Free the canonical name (GitHub keeps a redirect from the old URL)
gh repo rename persnally-internal -R sidpan2011/persnally          # private repo
git -C "$SRC" remote set-url origin github-personal:sidpan2011/persnally-internal.git

# Create the public-name repo as PRIVATE first, push, verify before exposing
gh repo create sidpan2011/persnally --private --source="$OUT" --remote=origin --push \
  --description "Your own context engine — local-first, across every AI. So every AI finally knows you."
```

## Phase 4 — verify before flipping public

```bash
# CI green on the new repo
gh run watch -R sidpan2011/persnally --exit-status
# A fresh clone builds + tests clean (proves the snapshot is self-contained)
D=$(mktemp -d); git clone git@github.com:sidpan2011/persnally.git "$D/p" \
  && cd "$D/p/persnallyd" && npm ci && npm test
# Re-run the leak gate against the PUSHED tree (paranoia is correct here)
gh api repos/sidpan2011/persnally/git/trees/HEAD?recursive=1 --jq '.tree[].path' \
  | grep -iE "PIVOT|PROGRESS|CLAUDE.md|launch/|experiments/|^api/|^web/|^src/|supabase" && echo "LEAK" || echo "clean"
```

## Phase 5 — launch moment (flip public)

```bash
gh repo edit sidpan2011/persnally --visibility public --accept-visibility-change-consequences
```
After this: the npm "Repository" link resolves, the README CI badge renders, and the Show HN has a clean repo to point at. `npm i -g persnally` is unaffected throughout (the package was already published; none of this touches the registry).

---

## Rollback / safety notes

- Nothing here touches npm. The published package is independent of this repo work.
- The public repo stays **private** until Phase 5, so a mistake before the flip is invisible.
- The private repo (now `persnally-internal`) retains the complete history and all internal docs — nothing is lost.
- If the rename causes friction with open PRs (#29, etc.), do the rename *after* those merge, or keep the public repo under a temporary name and rename at launch.
