# Entry point for the FontForge stage.
#
# usage: fontforge -lang=py -script run.py <job.json>
#
# Runs inside FontForge's embedded Python, so it may only use the standard
# library and FontForge's own modules. The uv side writes the job file; see
# ligaturizer.fontforge.
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legacy import ligaturize_font  # noqa: E402


def main():
    with open(sys.argv[1]) as f:
        job = json.load(f)
    ligaturize_font(**job)


if __name__ == "__main__":
    main()
