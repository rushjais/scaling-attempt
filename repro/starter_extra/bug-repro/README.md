# Repro: output differs between builds

We build our site in CI and diff the output against the previous build. With
our static-manifest plugin enabled, the output changes from build to build even
when nothing in the content or settings changed.

```bash
for i in 1 2 3; do
  python -m pelican samples/content -s samples/pelican.conf.py -o /tmp/out$i -q \
    -e 'PLUGIN_PATHS=["bug-repro"]' 'PLUGINS=["static_manifest"]'
done
diff /tmp/out1/static-manifest.txt /tmp/out2/static-manifest.txt
diff /tmp/out2/static-manifest.txt /tmp/out3/static-manifest.txt
```

Usually at least one of the diffs is non-empty.
