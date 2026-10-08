"""Hidden checks for the reproducibility task (pilot).

    python3 check_repro.py CANDIDATE_REPO

  visible        Pelican's own suite
  det_relurls    hidden RELATIVE_URLS site + early_url plugin, 6 hash seeds -> distinct outputs (want 1)
  det_sample     sample EN and FR sites + static_manifest + early_url, 6 seeds -> distinct outputs (want 1 each)
  det_library    the same relurls build run in-process through the Python API, 6 seeds (want 1)
  unchanged      plugin-free builds of sample EN, FR and the relurls site == original Pelican's output
  api            Generator.get_files() still returns a set that supports set operations
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = os.path.join(HERE, "..", "pilot", "upstream")
CHECK = os.path.join(HERE, "..", "pilot", "check")
DOCKER = shutil.which("docker") or "/Applications/Docker.app/Contents/Resources/bin/docker"

SCRIPT = r'''
set -u
fp() { (cd "$1" 2>/dev/null && find . -type f | sort | xargs sha1sum | sha1sum | cut -c1-12) || echo MISSING; }
P='PLUGIN_PATHS=["/hp"]'
seeds="0 1 2 3 4 5"
# det_relurls
for s in $seeds; do (cd /check/site_relurls && PYTHONHASHSEED=$s python -m pelican content -s pelicanconf.py -o /w/rel$s -q -e "$P" 'PLUGINS=["early_url"]' >/dev/null 2>&1); echo "det_relurls $(fp /w/rel$s)"; done
# det_sample
for c in pelican.conf.py pelican.conf_FR.py; do for s in $seeds; do PYTHONHASHSEED=$s python -m pelican samples/content -s samples/$c -o /w/$c$s -q -e "$P" 'PLUGINS=["static_manifest","early_url"]' >/dev/null 2>&1; echo "det_sample_$c $(fp /w/$c$s)"; done; done
# det_library: in-process via the API, no CLI
for s in $seeds; do (cd /check/site_relurls && PYTHONHASHSEED=$s python -c "
from pelican import Pelican
from pelican.settings import read_settings
s = read_settings('pelicanconf.py', override={'OUTPUT_PATH': '/w/lib$s', 'PLUGIN_PATHS': ['/hp'], 'PLUGINS': ['early_url']})
Pelican(s).run()" >/dev/null 2>&1); echo "det_library $(fp /w/lib$s)"; done
# unchanged: plugin-free builds, candidate vs original, seed 0
for who in orig new; do code=/work/repo; [ $who = orig ] && code=/orig
  (cd $code && PYTHONHASHSEED=0 PYTHONPATH=$code python -m pelican samples/content -s samples/pelican.conf.py -o /w/u_en_$who -q >/dev/null 2>&1)
  (cd $code && PYTHONHASHSEED=0 PYTHONPATH=$code python -m pelican samples/content -s samples/pelican.conf_FR.py -o /w/u_fr_$who -q >/dev/null 2>&1)
  (cd /check/site_relurls && PYTHONHASHSEED=0 PYTHONPATH=$code python -m pelican content -s pelicanconf.py -o /w/u_rel_$who -q >/dev/null 2>&1)
done
for x in en fr rel; do [ "$(fp /w/u_${x}_orig)" = "$(fp /w/u_${x}_new)" ] && echo "unchanged_$x same" || echo "unchanged_$x DIFFERENT"; done
# api
(cd /check/site_relurls && API_PROBE_REPORT=/w/api.json python -m pelican content -s pelicanconf.py -o /w/api_out -q -e "$P" 'PLUGINS=["api_probe"]' >/dev/null 2>&1)
echo "api $(cat /w/api.json 2>/dev/null | tr -d ' ' || echo '{"ok":false,"error":"no-report"}')"
# visible
echo "visible $(python -m pytest -q -n 4 -p no:cacheprovider pelican/tests --ignore=pelican/tests/build_test 2>&1 | tail -1 | tr ' ' '_')"
'''


def main():
    cand = os.path.abspath(sys.argv[1])
    work = cand.rstrip("/") + "_repro_check"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    r = subprocess.run([DOCKER, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
                        "-v", f"{cand}:/work/repo:ro", "-v", f"{os.path.abspath(UPSTREAM)}:/orig:ro",
                        "-v", f"{os.path.abspath(CHECK)}:/check:ro", "-v", f"{HERE}/hidden_plugins:/hp:ro",
                        "-v", f"{work}:/w", "pelican-migration-pilot", "sh", "-c", SCRIPT],
                       capture_output=True, text=True)
    seen, out = {}, {}
    for line in r.stdout.splitlines():
        key, val = line.split(" ", 1)
        seen.setdefault(key, set()).add(val)
    for key, vals in seen.items():
        if key.startswith("det_"):
            out[key] = {"distinct_outputs": len(vals), "ok": len(vals) == 1 and "MISSING" not in vals}
        elif key.startswith("unchanged_"):
            out[key] = {"ok": vals == {"same"}}
        elif key == "api":
            out[key] = json.loads(next(iter(vals)))
        elif key == "visible":
            out[key] = next(iter(vals)).replace("_", " ")
    out["all_hidden_ok"] = all(v["ok"] for k, v in out.items() if isinstance(v, dict))
    print(json.dumps(out, indent=2))
    json.dump(out, open(os.path.join(work, "summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
