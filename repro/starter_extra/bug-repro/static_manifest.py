"""Realistic plugin: write a manifest of static files in the order Pelican provides them."""
import os
from pelican import signals

def write_manifest(generator):
    out = generator.output_path
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "static-manifest.txt"), "w") as f:
        for sf in generator.staticfiles:
            f.write(sf.source_path + "\n")

def register():
    signals.static_generator_finalized.connect(write_manifest)
