**Bug: site output isn't reproducible between builds**

We build our site in CI and diff the generated output against the previous
build to see what changed. With some plugins enabled, the output changes from
one build to the next even when the content and settings are identical. A
minimal reproduction is in `bug-repro/` (a small plugin we use, plus steps).

Please fix this in Pelican (not in the plugin): building the same content with
the same settings and plugins should always produce identical output.

Requirements:

- Sites whose output is already reproducible must not change.
- No changes to the public plugin or theme API.
- The fix must hold however Pelican is run (the `pelican` command or as a
  library) and must not depend on environment variables.
- Pelican supports Python 3.11 and later.
- The existing test suite must still pass. It is not exhaustive.

Run the tests with `python -m pytest pelican/tests -n 4`.
