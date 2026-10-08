# Task 2: choosing the codebase and migration

**Goal:** a second RL task at real scale: a behavior-preserving migration
inside a sizable existing codebase, with the same grading rigor and failure
analysis as task 1 (`what-agents-dont-test`).

## Criteria

From the task-1 lessons and review notes:

1. **Real and sizable:** several thousand lines or more, many modules, its own
   conventions and tech debt.
2. **Cross-cutting change:** the migration touches 10+ files and crosses module
   boundaries.
3. **Not done upstream:** no merged migration a model could have seen (task 1's
   v1 was solved by recall).
4. **Codebase-specific traps:** places where *this* code relies on edge-case
   behavior of the old library, not just famous library trivia.
5. **A clean, deterministic behavior boundary:** CLI output or generated
   files that can be compared exactly, with no network.
6. **"Did it migrate?" is checkable separately:** old dependency gone from
   imports, new one actually used, so "change nothing" can't score.
7. **Containerizable and fast to grade:** pinned dependencies, the suite
   runs in minutes.

## Measured candidates (cloned 2026-10-07)

| Project | Source LOC | Test LOC | `os.path` uses (files) | Other | License |
|---|---|---|---|---|---|
| nikola | 29,092 | 5,694 | 458 (56) | static site generator | MIT |
| beets | 50,784 | 36,173 | 201 (43) | CLI on `optparse` (71 uses) | MIT |
| pelican | 8,736 | 8,283 | 225 (14) | static site generator, golden-output tests | AGPL-3.0 |
| mkdocs | 7,111 | 12,013 | 90 (15) | config on PyYAML (9 files) | MIT |
| jrnl | 5,901 | 2,745 | 34 (8) | | GPL-3.0 |
| yamllint | 4,870 | 11,121 | 21 (2) | built on PyYAML internals | GPL-3.0 |
| cookiecutter, twine, pydocstyle | < 4,000 | | | too small | MIT |

## Shortlist

### 1. Pelican: `os.path` → `pathlib` (recommended)

- **Scale:** 8.7k source lines; 225 `os.path` call sites across 14 modules
  (generators, utils, contents, settings, readers, tools).
- **Not done upstream:** no pathlib migration issue or PR found.
- **Codebase-specific traps already exist.** `contents.py` deliberately uses
  `os.path.join` on *URLs* to get `../a.html` for relative links, and its
  comments explain the tradeoff against `urljoin`. A naive port to `Path`
  (which normalizes, drops trailing slashes, and isn't for URLs) breaks
  relative-link generation in ways the README won't mention. `urlwrappers.py`
  uses `os.path.splitext` on URL patterns. More such spots are likely in
  `utils.py` and `generators.py`.
- **Behavior boundary:** the generated site. Pelican already ships golden
  output trees (`tests/output/basic`, `custom`, `custom_locale`, 193 files)
  compared with a directory diff, so a differential grader on many generated
  content sets extends an existing pattern.
- **Did it migrate:** count `os.path` and `import os.path` in non-test source;
  require `pathlib` in the touched modules.
- **Risks:** pathlib's general differences are well known, so the traps must
  lean on Pelican's own reliance (URLs built with path functions, settings
  that accept strings, plugins that receive paths). AGPL is fine for a public
  repo.

### 2. Nikola: `os.path` → `pathlib` (bigger scale)

- **Scale:** 29k source lines; 458 call sites across 56 files. Clearly "at
  scale."
- **Not done upstream:** no pathlib migration found.
- **Boundary:** built demo sites.
- **Risks:** many optional dependencies (image, markup and theme plugins),
  slower builds, possible timestamps in output, and agent runs that may not
  finish in 3 hours. Higher chance of a half-finished task.

### 3. beets: `optparse` → `click`

- **Scale:** 50k source lines; the CLI and its plugins are built on
  `optparse`.
- **Not done upstream:** open since 2015 (issue #1442, "Replace optparse with
  Click"). Discussed, never implemented, so there's no solution to recall.
- **Traps:** real parsing differences (optparse accepts abbreviated long
  options and interspersed arguments; click doesn't by default; different exit
  codes and errors), spread across many plugins.
- **Risks:** large and complex: plugin system, interactive prompts, music-file
  fixtures. The grading boundary (CLI behavior over a fixture library) is
  harder to define cleanly. Most likely to overrun.

### 4. mkdocs: PyYAML → ruamel.yaml (smaller)

- **Boundary:** parsed config and built site; custom YAML tags (`!ENV`,
  `!relative`).
- **Risks:** only 9 files use YAML, so it's narrow. The main differences (YAML
  1.1 `yes`/`no` booleans) are famous trivia, and ruamel has a 1.1 mode that
  makes the port nearly mechanical. Probably too small and too recallable.

## Recommendation

**Pelican, `os.path` → `pathlib`.** It meets every criterion, its traps are
specific to its own code rather than library trivia, and it already has a
golden-output comparison to build the grader on. Nikola is the fallback if
Pelican turns out too small; beets is the most ambitious option.

## Next step: a pilot before building infrastructure

Per the review notes: 1–2 days, crude, before any harness work.
1. Pin a Pelican commit, write a rough prompt, plant 2–3 candidate traps (or
   identify existing ones like the relative-URL join).
2. Run a frontier model a few times; check results by hand against the golden
   output plus a few extra content sets.
3. Decide:
   - catches every trap easily → traps are too well known; find subtler,
     Pelican-specific ones;
   - fails for boring reasons (environment, unclear prompt) → fix the setup;
   - passes the visible suite, claims success, breaks a hidden behavior → a
     real target; build the full grader.
