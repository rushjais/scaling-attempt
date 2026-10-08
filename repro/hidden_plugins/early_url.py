"""Realistic plugin: record the URL of the first static file at generation time
(e.g. to inject a preload hint). Reading .url marks the location as referenced."""
from pelican import signals

FIRST = {}

def remember(generator):
    if generator.staticfiles:
        FIRST["url"] = generator.staticfiles[0].url

def register():
    signals.static_generator_finalized.connect(remember)
