"""Hidden-contract checks: behavior that reading the old code won't reveal.

    python3 contracts.py CANDIDATE_REPO [CANDIDATE_REPO ...]

Each scenario runs the same build sequence with the original Pelican (the
pinned checkout) and with the candidate, in one container, and compares the
final output trees and exit codes:

  theme        theme templates doing string ops on path values
               (article.source_path.endswith, save_as|length, ...)
  incremental  build with the content cache, edit one article, rebuild
  old_cache    original Pelican writes the cache; the candidate rebuilds from it
  fs_edges     a broken symlink and an unreadable folder in the content dir
"""

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.dirname(os.path.dirname(HERE))
UPSTREAM = os.path.join(PILOT, "upstream")
DOCKER = shutil.which("docker") or "/Applications/Docker.app/Contents/Resources/bin/docker"

SCRIPT = r"""
set -u
export PYTHONHASHSEED=0
SITE=/check/site_relurls/content
CONF=/check/contracts/pelicanconf_contracts.py
build() {  # build CODE WORKDIR -> exit code; output in WORKDIR/output
  (cd "$2" && PYTHONPATH="$1" python -m pelican content -s $CONF -o output -q >log.txt 2>&1); echo $?
}
fresh() { rm -rf "$1"; mkdir -p "$1"; cp -rp $SITE "$1/content"; }
edit() { printf '\n\nEdited paragraph.\n' >> "$1/content/sub/nested.md"; touch -d '2024-02-01' "$1/content/sub/nested.md"; }

for who in orig new; do code=/$who
  # theme
  fresh /w/$who/theme; e1=$(build $code /w/$who/theme)
  # incremental: build, edit, rebuild with the same code
  fresh /w/$who/inc; build $code /w/$who/inc >/dev/null; edit /w/$who/inc; e2=$(build $code /w/$who/inc)
  # old_cache: ORIGINAL writes the cache, then $who rebuilds from it
  fresh /w/$who/oc; build /orig /w/$who/oc >/dev/null; edit /w/$who/oc; e3=$(build $code /w/$who/oc)
  # fs_edges: broken symlink + unreadable folder
  fresh /w/$who/fs; ln -s missing.md /w/$who/fs/content/ghost.md
  mkdir -p /w/$who/fs/content/secret && printf 'Title: Secret\nDate: 2024-01-05\n\nhidden\n' > /w/$who/fs/content/secret/s.md && chmod 000 /w/$who/fs/content/secret
  e4=$(build $code /w/$who/fs); chmod 755 /w/$who/fs/content/secret
  echo "$who theme=$e1 incremental=$e2 old_cache=$e3 fs_edges=$e4"
done
"""


def check(candidate):
    work = os.path.abspath(candidate) + "_contracts"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    r = subprocess.run(
        [DOCKER, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
         "-v", f"{UPSTREAM}:/orig:ro", "-v", f"{os.path.abspath(candidate)}:/new:ro",
         "-v", f"{os.path.dirname(HERE)}:/check:ro", "-v", f"{work}:/w",
         "pelican-migration-pilot", "sh", "-c", SCRIPT],
        capture_output=True, text=True)
    codes = {}
    for line in r.stdout.splitlines():
        who, *pairs = line.split()
        codes[who] = dict(p.split("=") for p in pairs)
    result = {}
    for sc in ("theme", "incremental", "old_cache", "fs_edges"):
        a, b = os.path.join(work, "orig", sc, "output"), os.path.join(work, "new", sc, "output")
        d = subprocess.run(["diff", "-rq", a, b], capture_output=True, text=True).stdout
        result[sc] = {"exit_orig": codes.get("orig", {}).get(sc), "exit_new": codes.get("new", {}).get(sc),
                      "files_differing": len([l for l in d.splitlines() if l.strip()])}
    return result


if __name__ == "__main__":
    for c in sys.argv[1:]:
        print(os.path.basename(os.path.dirname(c)) or c, json.dumps(check(c)))
