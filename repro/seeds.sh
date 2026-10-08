#!/bin/sh
# Build the hidden RELATIVE_URLS site under 8 hash seeds for one plugin setup;
# print a fingerprint of the whole output tree per seed, plus where the shared
# attachment landed.  usage: seeds.sh PLUGIN_NAME|none [PELICAN_CHECKOUT]
plug="$1"
here="$(cd "$(dirname "$0")" && pwd)"
code="${2:-$here/../pilot/upstream}"
docker="$(command -v docker || echo /Applications/Docker.app/Contents/Resources/bin/docker)"
"$docker" run --rm --user "$(id -u):$(id -g)" -e PLUG="$plug" \
  -v "$code:/work/repo:ro" -v "$here:/repro:ro" -v "$here/../pilot/check:/check:ro" \
  pelican-migration-pilot sh -c '
cd /check/site_relurls
for s in 0 1 2 3 4 5 6 7; do
  if [ "$PLUG" = none ]; then
    PYTHONHASHSEED=$s python -m pelican content -s pelicanconf.py -o /tmp/o$s -q >/dev/null 2>&1
  else
    PYTHONHASHSEED=$s python -m pelican content -s pelicanconf.py -o /tmp/o$s -q \
      -e "PLUGIN_PATHS=[\"/repro/plugins\"]" "PLUGINS=[\"$PLUG\"]" >/dev/null 2>&1
  fi
  fp=$(cd /tmp/o$s && find . -type f | sort | xargs sha1sum | sha1sum | cut -c1-10)
  att=$(cd /tmp/o$s && find . -name data.txt)
  echo "seed $s: tree $fp  data.txt at $att"
done'
