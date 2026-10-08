"""Hidden check plugin: does ordinary string work on the paths Pelican hands to
plugins, the way existing third-party plugins do? Writes a JSON report.
Every check is something that works on str and fails or differs on Path."""
import json
import os

from pelican import signals

REPORT = os.environ.get("PATH_PROBE_REPORT", "/tmp/path_probe.json")
results = {}


def check(name, value):
    try:
        ok = (isinstance(value, str)
              and value.startswith(value[:1])
              and (value + "").endswith(value[-1:] if value else "")
              and "%s" % value == value
              and value.replace("/", "/") == value)
        results[name] = {"ok": bool(ok), "type": type(value).__name__}
    except Exception as e:
        results[name] = {"ok": False, "type": type(value).__name__, "error": repr(e)}


def on_initialized(pelican):
    for key in ("PATH", "OUTPUT_PATH", "THEME", "CACHE_PATH"):
        if pelican.settings.get(key) is not None:
            check(f"settings.{key}", pelican.settings[key])
    check("pelican.path", pelican.path)
    check("pelican.output_path", pelican.output_path)


def on_content_init(content):
    for attr in ("source_path", "relative_source_path", "save_as", "url"):
        v = getattr(content, attr, None)
        if v:
            check(f"content.{attr}", v)


def on_content_written(path, context):
    check("signal.content_written.path", path)


def on_static_finalized(generator):
    for sf in generator.staticfiles:
        check("static.source_path", sf.source_path)
        check("static.save_as", sf.save_as)
        break


def on_finalized(pelican):
    with open(REPORT, "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)


def register():
    signals.initialized.connect(on_initialized)
    signals.content_object_init.connect(on_content_init)
    signals.content_written.connect(on_content_written)
    signals.static_generator_finalized.connect(on_static_finalized)
    signals.finalized.connect(on_finalized)
