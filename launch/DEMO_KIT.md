# Cold-demo kit — the Phase 0/1 exit gate

The single highest-information action available before launch. Your own PIVOT.md
makes it a hard gate: *"If the import demo is merely 'neat' — stop and rethink.
Everything depends on it."* This kit makes the five demos produce comparable
evidence instead of vibes, and turns them into a feature-discovery engine.

## Pre-register the gate (fill in BEFORE demo #1)

Write these down first so the result can't be renegotiated afterward. From PIVOT.md:

- **PASS if:** ≥ **3 of 5** developers are *visibly* startled by their own profile (not polite "neat" — an actual "wait, how did it know that").
- **AND** setup completes **unaided** (you say nothing) for ≥ 4 of 5.
- **AND** time from `npm i` to reading their profile is **≤ 5 minutes** for the median.

Decision rule:
- **Gate passes →** green-light launch prep (public repo, assets, Show HN).
- **Gate fails →** stop. Diagnose (most likely: profile synthesis quality, or signal density). Fix. Re-demo. Do not launch a wobbly wow.

## Subject selection

- **3–5 developers with dense AI history** — heavy ChatGPT/Claude/Claude Code users. Thin-history friends test the density floor, not the wow; recruit at most one to check that path.
- Cold = they have not seen Persnally before and you have not pitched it.
- Mix of stacks (the git/Claude Code importers should work regardless).

## Outreach message (DM/Slack)

```
Hey — I built a thing and I need 15 honest minutes, not a favor. It reads your
AI history (Claude/ChatGPT/your code) locally and tells you who it thinks you
are. I want to watch you use it cold and say nothing — no pitch, no help. You
keep whatever it generates (and can wipe it with one command). Free to do it
[day] over a call or in person? I literally need your unfiltered reaction.
```

## Observer protocol (how to run each session)

The hard rule: **say as little as possible.** Every time you explain something,
you're hiding a real onboarding failure. Hand them the one-liner and watch.

What they do:
```
npm i -g persnally && persnally setup
```
(Optional, for the richest result: have them export Claude/ChatGPT data to
~/Downloads beforehand — but ALSO watch what happens for someone who doesn't.)

Watch for, and write down verbatim:
- **Where they hesitate.** Any moment they're unsure what's happening or what to do next = a setup bug. Note the exact step.
- **The first reaction to the profile.** Capture their *exact words*. "Huh, neat" ≠ "wait, that's creepy accurate." Only the second counts toward the gate.
- **Do they screenshot or read a line aloud, unprompted?** That's the organic-share signal — the Phase 1 viral mechanic showing up early. Gold.
- **Where they light up vs. shrug** — which section of the profile lands, which feels generic. *This is your feature roadmap.* The part that makes them lean in is the part to deepen.
- **Do they ask "can I connect this to my [tool]?"** — pull toward the Layer (retention), not just the Mirror (wow).
- **Time-to-wow.** Note `npm i` start and first-profile-read timestamps.

What NOT to do: don't explain the architecture, don't defend a weak profile,
don't fix their environment for them (note the breakage instead).

## Per-subject record (copy one block per person)

```
Subject:                          Date:
History density (heavy/medium/thin):
Setup completed unaided? (Y/N) — if N, where it broke:
Time npm i → profile read:
First words on seeing the profile (verbatim):
Startled? (Y/N — be strict):
Screenshotted / read aloud unprompted? (Y/N):
Section that landed hardest:
Section that felt generic:
Asked to connect a tool? (Y/N — which):
Top friction / bug:
One thing they wish it did:
```

## Tally (after all sessions)

```
Startled:        _ / 5   (gate: ≥3)
Unaided setup:   _ / 5   (gate: ≥4)
Median time-to-wow: ___  (gate: ≤5 min)
Organic shares:  _ / 5
GATE: PASS / FAIL
Top 3 frictions to fix:
Top 3 "wish it did" (feature signal):
```

## Launch screenshot / GIF shot list

(Can't generate images here — these are the exact captures to make once the gate passes. The dashboard is at http://127.0.0.1:4983.)

1. **Hero screenshot — the profile with evidence.** Dashboard scrolled to the
   profile: the headline + 2–3 sections, with one "why does it think this?"
   panel *expanded* showing the cited events. This is the viral artifact — it
   proves "evidence-linked," not horoscope. Use a real, impressive (non-sensitive)
   profile; redact anything private.
2. **The interest graph.** The decayed topic bars — shows the "decay-weighted,
   deletable" claim visually.
3. **Setup GIF (~30s, terminal).** `npm i -g persnally && persnally setup` →
   the find/import/synthesize/connect lines scrolling → "open dashboard". Trim
   dead air; the whole point is "one command, five minutes."
4. **Optional: MCP in action.** A Claude/Cursor session calling `persnally_context`
   and the answer being personalized — the "Layer" payoff. Strong if you can get
   a clean capture.

Put #1 at the top of the Show HN and the public README.
