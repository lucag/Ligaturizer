"""Run the FontForge stage as a subprocess.

FontForge's Python bindings can't be installed from PyPI, so nothing in the uv
environment imports them (ADR 0002). Instead, the stage's script runs inside
FontForge's embedded Python and receives its job as a JSON file.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

STAGE_SCRIPT = Path(__file__).parent / "fontforge_stage" / "run.py"


class FontForgeNotFound(RuntimeError):
    pass


def find_fontforge() -> str:
    """Locate the fontforge executable via $FONTFORGE or $PATH."""
    configured = os.environ.get("FONTFORGE")
    if configured:
        if not shutil.which(configured):
            raise FontForgeNotFound(f"$FONTFORGE is set to {configured!r}, which isn't executable")
        return configured
    found = shutil.which("fontforge")
    if not found:
        raise FontForgeNotFound(
            "fontforge not found on $PATH; install FontForge or set $FONTFORGE to its path"
        )
    return found


def run_stage(action: str, args: dict) -> None:
    """Run the FontForge stage's `action` with `args` (its keyword arguments)."""
    fontforge = find_fontforge()
    with tempfile.TemporaryDirectory() as tmp:
        job_file = Path(tmp) / "job.json"
        job_file.write_text(json.dumps({"action": action, "args": args}))
        subprocess.run(
            [fontforge, "-lang=py", "-script", str(STAGE_SCRIPT), str(job_file)],
            check=True,
        )
