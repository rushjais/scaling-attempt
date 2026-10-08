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
