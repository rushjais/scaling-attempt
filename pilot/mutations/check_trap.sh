#!/bin/sh
# For one mutation: does Pelican's visible suite catch it, and does it change
# the generated sample sites? Usage: check_trap.sh WORKDIR MUTATION
# WORKDIR must not exist yet; it's left in place for inspection.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
work="$1"; mut="$2"
docker="$(command -v docker || echo /Applications/Docker.app/Contents/Resources/bin/docker)"
mkdir "$work"
cp -R "$here/../upstream" "$work/base"
cp -R "$here/../upstream" "$work/mut"
python3 "$here/apply.py" "$work/mut" "$mut" >/dev/null
build='python -m pelican samples/content -s samples/pelican.conf.py -o /o/en -q >/dev/null 2>&1;
       python -m pelican samples/content -s samples/pelican.conf_FR.py -o /o/fr -q >/dev/null 2>&1'
mkdir "$work/out_base" "$work/out_mut"
"$docker" run --rm --user "$(id -u):$(id -g)" -v "$work/base:/work/repo" -v "$work/out_base:/o" pelican-migration-pilot sh -c "$build"
tests=$("$docker" run --rm --user "$(id -u):$(id -g)" -v "$work/mut:/work/repo" -v "$work/out_mut:/o" pelican-migration-pilot sh -c \
  "python -m pytest -q -n 4 -p no:cacheprovider pelican/tests --ignore=pelican/tests/build_test 2>&1 | tail -1; $build")
en=$(diff -rq "$work/out_base/en" "$work/out_mut/en" 2>/dev/null | wc -l | tr -d ' ')
fr=$(diff -rq "$work/out_base/fr" "$work/out_mut/fr" 2>/dev/null | wc -l | tr -d ' ')
printf '%-24s visible tests: %-38s | sample-site files changed: EN %s, FR %s\n' "$mut" "$tests" "$en" "$fr"
