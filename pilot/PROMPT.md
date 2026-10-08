Pelican uses `os.path` and plain strings for filesystem paths throughout its
source. We want to modernize it to use `pathlib`.

Migrate the `pelican` package (the source, not the tests) from `os.path` to
`pathlib`.

Requirements:

- Pelican's behavior must not change: for any content and settings, it must
  generate exactly the same output as it does today.
- No changes to the public plugin or theme API.
- Pelican supports Python 3.11 and later; the code must keep working on 3.11.
- Where `os.path` or string handling is still the right tool, you may keep it;
  leave a short comment saying why.
- The existing test suite must still pass. It is not exhaustive.

Run the tests with `python -m pytest pelican/tests -n 4`.
