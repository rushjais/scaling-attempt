"""Crude pilot checker for one migrated Pelican checkout (not the final grader).

    python3 check.py REPO [--baseline]

Runs in the pilot Docker image:
  1. visible suite (pelican/tests, minus the unrelated packaging test)
  2. builds: two sample sites (EN, FR) and the hidden RELATIVE_URLS site, with
     the path-probe plugin loaded
  3. compares each build with the baseline (untouched Pelican at the pin)
  4. reads the probe report (do plugins still get str paths?)
  5. migration completeness: os.path uses left in the source, and how many of
     them carry an explanatory comment
--baseline builds the reference outputs from REPO (use the untouched checkout).
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "baseline")
DOCKER = shutil.which("docker") or "/Applications/Docker.app/Contents/Resources/bin/docker"
IMAGE = "pelican-migration-pilot"

BUILD = """
set -u
plug='-e PLUGIN_PATHS=["/check/probe_plugin"] PLUGINS=["path_probe"]'
python -m pelican samples/content -s samples/pelican.conf.py -o /out/en -q $plug >/out/en.log 2>&1 || echo build-failed-en
python -m pelican samples/content -s samples/pelican.conf_FR.py -o /out/fr -q >/out/fr.log 2>&1 || echo build-failed-fr
cd /check/site_relurls && PATH_PROBE_REPORT=/out/probe_relurls.json \
  python -m pelican content -s pelicanconf.py -o /out/relurls -q $plug >/out/relurls.log 2>&1 || echo build-failed-relurls
"""


def docker(repo, out, script):
    return subprocess.run(
        [DOCKER, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
         "-v", f"{os.path.abspath(repo)}:/work/repo", "-v", f"{out}:/out",
         "-v", f"{HERE}:/check:ro", "-e", "PATH_PROBE_REPORT=/out/probe_en.json",
         IMAGE, "sh", "-c", script],
        capture_output=True, text=True)


def diff_count(a, b):
    if not (os.path.isdir(a) and os.path.isdir(b)):
        return None
    r = subprocess.run(["diff", "-rq", a, b], capture_output=True, text=True)
    return len([l for l in r.stdout.splitlines() if l.strip()])


def completeness(repo):
    left, commented = 0, 0
    for dp, _, fs in os.walk(os.path.join(repo, "pelican")):
        if "/tests" in dp:
            continue
        for f in fs:
            if not f.endswith(".py"):
                continue
            lines = open(os.path.join(dp, f), errors="ignore").read().splitlines()
            for i, line in enumerate(lines):
                if re.search(r"\bos\.path\.", line):
                    left += 1
                    if "#" in line or (i and lines[i - 1].strip().startswith("#")):
                        commented += 1
    return {"os_path_left": left, "os_path_left_with_comment": commented}


def main():
    repo = sys.argv[1]
    if "--baseline" in sys.argv:
        shutil.rmtree(BASE, ignore_errors=True)
        os.makedirs(BASE)
        print(docker(repo, BASE, BUILD).stdout or "baseline built")
        print(json.dumps(completeness(repo)))
        return
    out = os.path.join(os.path.abspath(repo) + "_check")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    tests = docker(repo, out, "python -m pytest -q -n 4 -p no:cacheprovider pelican/tests "
                              "--ignore=pelican/tests/build_test 2>&1 | tail -1").stdout.strip()
    build = docker(repo, out, BUILD).stdout.strip()
    probe = {}
    for name in ("probe_en.json", "probe_relurls.json"):
        p = os.path.join(out, name)
        if os.path.exists(p):
            for k, v in json.load(open(p)).items():
                probe[k] = probe.get(k, True) and v["ok"]
    summary = {
        "visible_tests": tests,
        "build_problems": build or None,
        "files_differing": {s: diff_count(os.path.join(BASE, s), os.path.join(out, s))
                            for s in ("en", "fr", "relurls")},
        "plugin_values_not_str": sorted(k for k, ok in probe.items() if not ok),
        **completeness(repo),
    }
    print(json.dumps(summary, indent=2))
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
