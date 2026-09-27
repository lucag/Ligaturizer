# Entry point for the FontForge stage.
#
# usage: fontforge -lang=py -script run.py <job.json>
#
# Runs inside FontForge's embedded Python, so it may only use the standard
# library and FontForge's own modules. The uv side writes the job file (see
# ligaturizer.fontforge): {"action": ..., "args": {...}}.
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    with open(sys.argv[1]) as f:
        job = json.load(f)
    if job["action"] == "copy_glyphs":
        from glyphs import copy_glyphs

        copy_glyphs(**job["args"])
    else:
        sys.exit("unknown FontForge stage action {!r}".format(job["action"]))


if __name__ == "__main__":
    main()
