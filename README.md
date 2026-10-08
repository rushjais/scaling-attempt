# Scaling attempt: three pilots in a real codebase

A follow-up to [what-agents-dont-test](https://github.com/rushjais/what-agents-dont-test),
an RL task for coding agents that was small (one file, ~30-minute runs). This
repo is my attempt to build a second task inside a real, sizable codebase, and
the pilots I ran first to check that the failure I wanted to measure actually
exists. **It didn't, three times**, and the commit history shows each step.

The codebase is [Pelican](https://github.com/getpelican/pelican), a static site
generator (~8,700 source lines), pinned at `3c69dc6` and chosen from ten
measured candidates ([`SHORTLIST.md`](SHORTLIST.md)).

## Results

| Pilot | Task | Runs | Result |
|---|---|---|---|
| 1 | Migrate `os.path` → `pathlib`, behavior unchanged | 2 × Opus 5.5 | Both passed every check in ~10 min, by keeping `os.path` exactly where `pathlib` behaves differently |
| 2 | Same, but filesystem paths *must* use `pathlib` | Opus 5.5 ×2, Opus 4.7, Sonnet 5.5 | Every valid run passed; models differed on cost ($1.80 to $19.37), not correctness |
| 3 | Fix a real bug found in pilot 1: with some plugins, output differs between builds (submitted upstream: [pelican#3621](https://github.com/getpelican/pelican/pull/3621)) | Opus 5.5 ×2, Opus 4.7, Sonnet 5.5 | All four fixed the root cause in 1–5 minutes |

Full write-up of every run, check and decision: [`pilot/PILOT.md`](pilot/PILOT.md).

**What it taught me.** In these pilots, when the specification was readable
(the old code, in a migration), careful agents didn't miss it: every run built
its own old-vs-new comparison unprompted. Known bug patterns are solved instantly. In the first
project, agents failed when behavior had to be *discovered* and lay outside
what they thought to test, so a harder second task needs that property, not
more lines of code.

## How the checks were kept honest

Every hidden check was validated with a control that should fail it before a
pass was trusted:

- **Migration:** a hidden `RELATIVE_URLS` site the visible tests never
  exercise; a probe plugin checking that paths reaching plugins are still
  `str`; a theme template doing string operations on paths; incremental
  rebuilds; a cache written by the old code and read by the new; a broken
  symlink and an unreadable folder. Naive one-site edits (`pilot/mutations/`)
  showed which candidate traps were real, which the visible tests already
  caught, and which weren't traps at all.
- **Bug fix:** determinism across hash seeds, in CLI and library mode;
  unchanged output for already-reproducible sites; `get_files()` still a set.
  Two tempting wrong fixes (returning a sorted list; forcing a fixed hash
  seed) pass Pelican's own tests and each fail exactly one hidden check.

Two checker bugs and one harness bug were caught along the way and are
documented: a probe plugin that changed the output it observed, hash-order
nondeterminism that made a correct run look broken, and an agent that killed
its own process because the runner put the prompt (which starts "Pelican…")
in its command line.

## Layout

```
SHORTLIST.md            codebase selection: 10 projects measured, 4 shortlisted
pilot/
  PIN, fetch_pelican.sh   the pinned Pelican commit (fetched, not vendored)
  Dockerfile, requirements.txt, requirements.lock   the agent sandbox
  PROMPT_v1.md, PROMPT.md  migration prompts (pilot 1, pilot 2)
  run_pilot.py            one attempt: workspace, sandboxed agent, checks
  mutations/              naive edits used to test candidate traps
  check/                  migration checks (site diffs, probe plugin, contracts/)
  runs/                   every attempt: transcript, diff, summary
  PILOT.md                results and decisions for all three pilots
repro/
  PROMPT.md, starter_extra/   the bug-report ticket and its reproduction
  check_repro.py, hidden_plugins/   hidden checks for the bug fix
  reference_fix.patch     a 7-line fix proving the task is solvable
```

## Reproducing

Requires Docker and Python 3.11+.

```bash
pilot/fetch_pelican.sh                                  # Pelican at the pinned commit
docker build -t pelican-migration-pilot pilot/
python3 pilot/check/check.py pilot/upstream --baseline  # reference outputs
python3 repro/check_repro.py pilot/upstream             # untouched Pelican fails determinism
```

## Notes

Pelican is licensed under AGPL-3.0; it's fetched at a pinned commit rather
than included here. `repro/reference_fix.patch` modifies Pelican and is
offered under the same license.

Built with Claude Code as a coding agent under my direction. I made the design
and scoping calls and reviewed results; the code and much of the prose were
written by the agent.
