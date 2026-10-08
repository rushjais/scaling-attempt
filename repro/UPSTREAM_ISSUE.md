# Draft: upstream issue for getpelican/pelican (not yet filed)

**Title:** Output order of static files depends on `PYTHONHASHSEED`, making builds non-reproducible with some plugins

**Body:**

`Generator.get_files()` returns a `set`, and the generators iterate it
directly. `StaticGenerator.generate_context()` also iterates the union
`linked_files | found_files`. Iteration order of a set of strings depends on
the interpreter's hash seed, so the order of `generator.staticfiles` (and the
order in which files are processed) changes from one build to the next.

Pelican's own output isn't affected in a default build, but anything that
depends on that order is. Two examples:

- A plugin that writes the static files in the order Pelican provides them
  (for example a manifest) produces a different file on each build.
- A plugin that reads a static file's `url` during generation marks its output
  location as referenced, which stops a later `{attach}` link from relocating
  it. Which file gets frozen depends on iteration order, so a shared
  attachment can end up in different places on different builds.

**Reproduction** (Pelican at 3c69dc6, Python 3.11, Linux):

```python
# manifest.py
import os
from pelican import signals

def write_manifest(generator):
    with open(os.path.join(generator.output_path, "static-manifest.txt"), "w") as f:
        for sf in generator.staticfiles:
            f.write(sf.source_path + "\n")

def register():
    signals.static_generator_finalized.connect(write_manifest)
```

```bash
for s in 0 1 2 3 4 5; do
  PYTHONHASHSEED=$s pelican samples/content -s samples/pelican.conf.py -o /tmp/out$s -q \
    -e 'PLUGIN_PATHS=["."]' 'PLUGINS=["manifest"]'
done
for s in 1 2 3 4 5; do diff -q /tmp/out0/static-manifest.txt /tmp/out$s/static-manifest.txt; done
```

With both the manifest plugin and a plugin that reads the first static file's
URL, the sample site produced 5 distinct output trees across 6 seeds.

**Suggested fix:** iterate in sorted order where the generators consume
`get_files()`, at minimum `for f in sorted(linked_files | found_files):` in
`StaticGenerator.generate_context()`, and for consistency the article, page,
and disabled-reader loops. `get_files()` itself can keep returning a set, so
plugins that use set operations on it are unaffected. With this change, the
same builds are byte-identical across seeds, plugin-free output is unchanged,
and the test suite passes. Happy to open a PR.
