#!/bin/sh
# Sample sites (EN, FR) with both order-sensitive plugins, 8 seeds; tree fingerprint per seed.
# usage: seeds_sample.sh PELICAN_CHECKOUT
here="$(cd "$(dirname "$0")" && pwd)"
docker="$(command -v docker || echo /Applications/Docker.app/Contents/Resources/bin/docker)"
"$docker" run --rm --user "$(id -u):$(id -g)" -v "$1:/work/repo:ro" -v "$here:/repro:ro" pelican-migration-pilot sh -c '
for conf in pelican.conf.py pelican.conf_FR.py; do
  for s in 0 1 2 3 4 5 6 7; do
    PYTHONHASHSEED=$s python -m pelican samples/content -s samples/$conf -o /tmp/$conf$s -q \
      -e "PLUGIN_PATHS=[\"/repro/plugins\"]" "PLUGINS=[\"static_manifest\",\"early_url\"]" >/dev/null 2>&1
    (cd /tmp/$conf$s && echo "$conf $(find . -type f | sort | xargs sha1sum | sha1sum | cut -c1-10)")
  done
done'
