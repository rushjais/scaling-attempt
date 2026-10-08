# Pilot 1: Pelican `os.path` → `pathlib` (2026-10-07)

**Setup.** Pelican pinned at `3c69dc6`, Linux container (Python 3.11, Pelican's
test dependencies, en_US/fr_FR locales), prompt in `PROMPT.md`, hand checks in
`check/check.py`: visible suite, three site builds compared with the untouched
Pelican (sample EN, sample FR, and a hidden `RELATIVE_URLS` site with nested
folders and cross-links), a probe plugin checking that values reaching plugins
are still `str`, and a count of `os.path` uses left.

**Python 3.11, deliberately.** Pelican declares `requires-python >= 3.11`, so a
correct migration must work on 3.11, where `Path.relative_to()` can't walk up
with `..` (that arrived in 3.12). This makes the `relpath` sites a real
constraint, not one we invented.

## Trap check before any runs

Each candidate trap was simulated with a naive one-site edit (`mutations/`),
then run against the visible suite and the sample sites.

| Trap | Visible tests catch it? | Output changes? | Verdict |
|---|---|---|---|
| A: `os.path.join` on URLs for `RELATIVE_URLS` | yes (2 failures) | yes (19–21 files; 11 of 13 on the hidden site) | real, but visible |
| B: `attach_to` with `relative_to` | no | no | not a trap: the naive port gives the same result |
| C: `relative_dir` (`''` vs `'.'`) | no | no | not a trap: normalized away before output |
| D1: `content_written` signal sends a `Path` | no | no | **hidden** (probe plugin) |
| D2: path settings become `Path` | no | no | **hidden** (probe plugin) |

**Plugin/API boundary decision:** it counts. The prompt says only "no changes
to the public plugin or theme API"; the agent has to work out what's public. A
hidden probe plugin does ordinary string operations on paths it receives.

## Runs (Opus 5.5, 120 min / $20 limits)

| Run | Time | Cost | Visible tests | Sites differing (EN/FR/hidden) | Plugin values not `str` | `os.path` left (with comment) |
|---|---|---|---|---|---|---|
| p1-o55 | 9.6 min | $2.54 | 291 passed | 0 / 0 / 0 | none | 138 of 194 (85) |
| p2-o55 | 9.8 min | $3.21 | 291 passed | 0 / 0 / 0 | none | 128 of 194 (88) |

Both runs built their own differential checks without being asked: run 1
compared 11 site configurations old vs new and noticed some builds vary run to
run because of hash randomization; run 2 compared 21 sites and spot-checked
helpers on edge inputs (`..md`, `foo.`, empty paths, trailing slashes). Run 1
found and guarded a potential data-loss bug (`clean_output_dir` on an empty
path would have emptied the current directory).

## What the pilot found

1. **Opus 5.5 handles this task easily as specified.** Both runs passed every
   check in under 10 minutes. Per the pilot's decision rule, the traps are too
   well known or too easy to avoid.
2. **The "keep it with a comment" allowance let agents sidestep the traps.**
   Each run converted only ~56–66 of 194 call sites and kept the rest, almost
   always exactly where `pathlib` would change behavior (`relpath`,
   `splitext`, empty strings, URL joins). Keeping `os.path` wherever it's risky
   is safe, but it isn't the migration. The traps only bite when the risky
   sites must actually be ported.
3. **Two grader bugs, caught before they produced a false result.**
   - *The probe plugin changed the output.* It read `url`/`save_as` at content
     creation; Pelican never moves an output path that's already been read, so
     the probe froze attachment locations.
   - *That exposed real nondeterminism in Pelican.* Once something reads URLs
     early, which attachment gets frozen depends on set iteration order, i.e. on
     `PYTHONHASHSEED`. With the probe loaded, original Pelican put a shared
     attachment in two different places across 8 hash seeds.
   Together these made run 2 look like it broke 8 files on the hidden site.
   Fix: differential builds run without plugins and with a fixed hash seed; the
   probe runs in a separate build.

## Next

Tighten the requirement so the risky sites must be ported, not kept: filesystem
paths go through `pathlib`; `os.path`/string handling stays only for things
that aren't filesystem paths (URLs, URL templates). Grade completeness on
filesystem operations. Then a second quick pilot round (2 runs) to see whether
the traps bite once they can't be sidestepped.

# Pilot round 2: tightened prompt (2026-10-07)

**Change.** `PROMPT.md` now says filesystem paths must use `pathlib`;
`os.path`/string handling may stay only for values that aren't filesystem paths
(URLs, URL templates), each marked with a comment. Round 1's prompt is kept as
`PROMPT_v1.md`. Weaker models added, per review: one Opus 4.7 run and one
Sonnet 5.5 run. Limits unchanged (120 min / $20). Four runs in parallel: each
used ~150 MB, far below the Docker VM's 8.3 GB.

| Run | Model | Time | Cost | Visible | Sites (EN/FR/hidden) | Plugin values | `os.path` left (commented) |
|---|---|---|---|---|---|---|---|
| r2d-s55 | Sonnet 5.5 | 10.0 min | $1.80 | 291 passed | 0 / 0 / 0 | str | 13 (10) |
| r2c-o47 | Opus 4.7 | 20.6 min | $19.37 | 291 passed | 0 / 0 / 0 | str | 10 (9) |
| r2b-o55 | Opus 5.5 | 32.0 min | $11.33 | 291 passed | 0 / 0 / 0 | str | 21 (11) |
| r2a-o55 | Opus 5.5 | 14.2 min | n/a | 291 passed | 0 / 0 / 0 | str | 33 (23) |

**r2a-o55 is invalid (harness flaw).** Cleaning up a stray autoreloading
`pelican` server, the agent looped over `/proc` and killed every process whose
command line contained "pelican". The runner passed the prompt as a
command-line argument, and the prompt starts with "Pelican uses…", so the agent
killed its own Claude Code process (PID 1). Fix: the prompt now goes in on
stdin. Its code at the moment it died passed every check.

The tightened prompt worked as intended on completeness: 10–33 `os.path` uses
left instead of 128–138, so the risky sites were actually ported. It slowed
Opus 5.5 down (32 min vs ~10). It still broke nothing.

## Hidden-contract checks (`check/contracts/contracts.py`)

Per review: the question isn't "bigger codebase?" but "where can behavior hide
that reading the old code won't reveal?" Four scenarios, each run with original
Pelican and the candidate, comparing output trees and exit codes:

| Scenario | What it exercises |
|---|---|
| theme | a theme template doing string ops on path values (`source_path.endswith`, `save_as\|length`, `.upper()`, `output_file.startswith`, URL concatenation) |
| incremental | content cache on: build, edit one article, rebuild |
| old_cache | original Pelican writes the cache; the candidate rebuilds from it |
| fs_edges | a broken symlink and an unreadable folder in the content directory |

Controls: untouched Pelican matches in every scenario; a mutation that makes
`source_path` a `Path` fails all four (the template raises
`'PosixPath object' has no attribute 'endswith'`).

**All six pilot solutions (rounds 1 and 2, including the invalid run) pass all
four scenarios.**

## Conclusion of the pilot

This task, as built, doesn't produce failures in current models. Across six
solutions from three models, every one preserved behavior on the sample sites,
the hidden RELATIVE_URLS site, the plugin probe, and all four hidden-contract
scenarios. It separates models on cost and time (Sonnet 5.5: $1.80 / 10 min;
Opus 4.7: $19.37 / 21 min), not correctness.

The likely reason: in a behavior-preserving migration the old code is both the
specification and fully readable, and every run built its own old-vs-new
differential check without being asked (11, 21, and more site
configurations). Careful reading plus self-built differential testing covers a
migration like this. A bigger codebase would add work, not difficulty, unless
it brings behavior that isn't visible in the code being migrated.
