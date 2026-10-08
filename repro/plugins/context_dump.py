"""Realistic plugin: dump keys of context collections in iteration order."""
import os
from pelican import signals

def dump(pelican_obj, writer=None):
    pass

def write(generators):
    for g in generators:
        ctx = g.context
        out = g.output_path
        with open(os.path.join(out, "context-order.txt"), "w") as f:
            for key in ("static_content", "generated_content", "static_links"):
                v = ctx.get(key)
                if v is not None:
                    f.write(f"{key}: {list(v)[:50]}\n")
        break

def register():
    signals.all_generators_finalized.connect(write)
