"""Hidden check plugin: plugins that call Generator.get_files() expect a set
(Pelican's own type hint says set[str]) and do set operations on it."""
import json
import os

from pelican import signals

REPORT = os.environ.get("API_PROBE_REPORT", "/tmp/api_probe.json")


def probe(generator):
    try:
        files = generator.get_files(generator.settings["STATIC_PATHS"], extensions=False)
        union = files | {"__probe__"}
        ok = isinstance(files, set) and "__probe__" in union
        res = {"get_files_type": type(files).__name__, "ok": bool(ok)}
    except Exception as e:
        res = {"ok": False, "error": repr(e)}
    with open(REPORT, "w") as f:
        json.dump(res, f)


def register():
    signals.static_generator_finalized.connect(probe)
