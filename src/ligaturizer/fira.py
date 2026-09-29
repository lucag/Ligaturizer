"""Where the Ligature source lives: Fira Code's OTFs built from the submodule."""

from pathlib import Path

# Relative to the repository root, like the paths in the font catalogue.
FIRA_OTF_DIR = Path("fonts/fira/distr/otf/Fira Code")

# Fira Code's weights and their OS/2 weight classes.
WEIGHTS = {
    "Light": 300,
    "Regular": 400,
    "Retina": 450,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
}


def ligature_source(weight: str) -> Path:
    """Path to the Ligature source OTF for one of Fira Code's WEIGHTS."""
    if weight not in WEIGHTS:
        raise ValueError(f"unknown Fira Code weight {weight!r}; expected one of {list(WEIGHTS)}")
    return FIRA_OTF_DIR / f"FiraCode-{weight}.otf"


def nearest_weight(weight_class: int) -> str:
    """The one of Fira Code's WEIGHTS nearest `weight_class`; ties go to the lighter."""
    return min(WEIGHTS, key=lambda w: (abs(WEIGHTS[w] - weight_class), WEIGHTS[w]))
