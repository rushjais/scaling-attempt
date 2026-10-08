"""Apply one naive-pathlib "mutation" to a Pelican checkout, simulating what a
careless migration would do at a single site. Used to check whether a trap is
caught by Pelican's visible tests and whether it changes generated output.

    python3 apply.py REPO MUTATION
"""
import sys

MUTATIONS = {
    # A: the RELATIVE_URLS joiner (os.path.join on URLs) ported to Path
    "A_relative_url_join": (
        "pelican/contents.py",
        "            joiner = os.path.join\n",
        "            joiner = lambda a, b: str(__import__('pathlib').Path(a) / b)\n",
    ),
    # B: attach_to's relpath ported to Path.relative_to (no walk-up on 3.11)
    "B_attach_relative_to": (
        "pelican/contents.py",
        "        tail_path = os.path.relpath(self.source_path, linking_source_dir)\n"
        "        if tail_path.startswith(os.pardir + os.sep):\n"
        "            tail_path = os.path.basename(tail_path)\n",
        "        from pathlib import Path as _P\n"
        "        try:\n"
        "            tail_path = str(_P(self.source_path).relative_to(linking_source_dir))\n"
        "        except ValueError:\n"
        "            tail_path = _P(self.source_path).name\n",
    ),
    # C: relative_dir's dirname ported to Path.parent ('' becomes '.')
    "C_relative_dir_parent": (
        "pelican/contents.py",
        "            os.path.dirname(\n"
        "                os.path.relpath(\n"
        "                    os.path.abspath(self.source_path),\n"
        '                    os.path.abspath(self.settings["PATH"]),\n'
        "                )\n"
        "            )\n",
        "            str(__import__('pathlib').Path(\n"
        "                os.path.relpath(\n"
        "                    os.path.abspath(self.source_path),\n"
        '                    os.path.abspath(self.settings["PATH"]),\n'
        "                )\n"
        "            ).parent)\n",
    ),
    # D1: plugin boundary: content_written signal now sends a Path
    "D1_signal_path": (
        "pelican/writers.py",
        "            signals.content_written.send(path, context=localcontext)\n",
        "            signals.content_written.send(__import__('pathlib').Path(path), context=localcontext)\n",
    ),
    # D2: plugin boundary: PATH/OUTPUT_PATH/THEME/CACHE_PATH settings become Path
    "D2_settings_paths": (
        "pelican/settings.py",
        "            return os.path.abspath(\n"
        "                os.path.normpath(\n"
        "                    os.path.join(os.path.dirname(base_path), maybe_relative)\n"
        "                )\n"
        "            )\n",
        "            return __import__('pathlib').Path(os.path.abspath(\n"
        "                os.path.normpath(\n"
        "                    os.path.join(os.path.dirname(base_path), maybe_relative)\n"
        "                )\n"
        "            ))\n",
    ),

}

if __name__ == "__main__":
    repo, name = sys.argv[1], sys.argv[2]
    path, old, new = MUTATIONS[name]
    p = f"{repo}/{path}"
    s = open(p).read()
    assert s.count(old) == 1, f"{name}: anchor not found exactly once"
    open(p, "w").write(s.replace(old, new))
    print(f"applied {name}")
