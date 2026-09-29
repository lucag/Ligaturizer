"""The Ligature selection: ligatures required or excluded on top of Fira Code's calt.

Read from `selection.toml`. Fira Code makes several sequences with one lookup
(e.g. one lowers the dot of i and j after f), so an exclusion leaves out every
calt lookup that makes it (ADR 0005). Leaving out a lookup that also makes a
sequence nobody excluded is an error, found by shaping text with the Ligature
source with and without the excluded lookups.

The Ligature snapshot, `ligature-snapshot.toml`, records the ligatures the
pinned Fira Code has, so the build can warn when one disappears. Refresh it with
`make ligature-snapshot` after moving the pin.
"""

import io
import itertools
import json
import string
import subprocess
import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from ligaturizer.calt import calt_lookup_indices, lookup_outputs
from ligaturizer.fira import FIRA_OTF_DIR, ligature_source
from ligaturizer.inventory import Inventory, generate_test_strings, read_inventory

# Relative to the repository root, like the paths in the font catalogue.
SELECTION_FILE = Path("selection.toml")
SNAPSHOT_FILE = Path("ligature-snapshot.toml")
FIRA_SUBMODULE = FIRA_OTF_DIR.parents[2]


class SelectionError(ValueError):
    pass


@dataclass(frozen=True)
class Selection:
    # Sequences the Ligature source must ligate; the build fails otherwise.
    require: tuple[str, ...] = ()
    # Sequences that must not be ligated.
    exclude: tuple[str, ...] = ()


def read_selection(path: Path = SELECTION_FILE) -> Selection:
    data = tomllib.loads(Path(path).read_text())
    if unknown := set(data) - {"require", "exclude"}:
        raise SelectionError(f"{path}: unknown keys {sorted(unknown)}")
    selection = Selection(tuple(data.get("require", [])), tuple(data.get("exclude", [])))
    if both := sorted(set(selection.require) & set(selection.exclude)):
        raise SelectionError(f"{path}: {both} both required and excluded")
    return selection


def resolve(selection: Selection, source_file: Path) -> tuple[frozenset[int], list[str]]:
    """The Ligature source's calt lookups to leave out, and warnings to show.

    Raises SelectionError if a required sequence isn't ligated, or if leaving
    out the lookups would also change a sequence that isn't excluded.
    """
    return _resolve(selection, Path(source_file).resolve())


@cache
def _resolve(selection: Selection, source_file: Path) -> tuple[frozenset[int], list[str]]:
    source = _Shaped(source_file)
    name = source_file.name

    for text in selection.require:
        if not source.changed_glyphs(text):
            raise SelectionError(f"{name} doesn't ligate {text!r}, which the selection requires")

    warnings = []
    exclude: set[int] = set()
    for text in selection.exclude:
        lookups = source.lookups_making(text)
        if not lookups:
            warnings.append(f"{name} doesn't ligate {text!r}; nothing to exclude")
        exclude |= lookups
    if not exclude:
        return frozenset(), warnings

    also = source.also_changed(frozenset(exclude), selection.exclude)
    if also:
        shown = ", ".join(repr(s) for s in also[:10]) + (", …" if len(also) > 10 else "")
        raise SelectionError(
            f"excluding {list(selection.exclude)} leaves out {name}'s calt rules that also"
            f" make {shown}; exclude those too or keep the rules"
        )
    return frozenset(exclude), warnings


class _Shaped:
    """A Ligature source, shaped with HarfBuzz."""

    def __init__(self, path: Path):
        self.path = path
        font = TTFont(path)
        gsub = font["GSUB"].table
        self.cmap = font.getBestCmap()
        self.hb_font = _hb_font(path.read_bytes())
        self.top_outputs = {i: lookup_outputs(gsub, i) for i in calt_lookup_indices(gsub)}

    def changed_glyphs(self, text: str) -> set[str]:
        """Glyphs calt puts in `text` in place of the characters' own."""
        return set(_shape(self.hb_font, text)) - {self.cmap.get(ord(c)) for c in text}

    def lookups_making(self, text: str) -> set[int]:
        """Top-level calt lookups that make `text`'s ligature glyphs.

        Spacers are ignored: Fixed ligatures and Sequence families share them.
        """
        made = {g for g in self.changed_glyphs(text) if not g.endswith(".spacer")}
        return {i for i, outputs in self.top_outputs.items() if outputs & made}

    def also_changed(self, exclude: frozenset[int], excluded: tuple[str, ...]) -> list[str]:
        """Sequences, not containing an excluded one, that change without `exclude`."""
        without = _hb_font(_glyph_choice_font(self.path, exclude))
        candidates = generate_test_strings(read_inventory(self.path))
        candidates += ["".join(p) for p in itertools.product(string.ascii_letters, repeat=2)]
        return sorted(
            {
                text
                for text in candidates
                if not any(x in text for x in excluded)
                and _glyph_ids(self.hb_font, text) != _glyph_ids(without, text)
            },
            key=lambda s: (len(s), s),
        )


# The tables HarfBuzz needs to choose glyphs; leaving out the outlines makes
# the font quick to compile.
_GLYPH_CHOICE_TABLES = {"head", "hhea", "maxp", "cmap", "hmtx", "GDEF", "GSUB"}


def _glyph_choice_font(path: Path, exclude: frozenset[int]) -> bytes:
    """The font at `path`, cut down to choosing glyphs, with calt leaving out `exclude`."""
    font = TTFont(path)
    font.getGlyphOrder()  # before the table that names the glyphs goes
    for tag in set(font.keys()) - _GLYPH_CHOICE_TABLES - {"GlyphOrder"}:
        del font[tag]
    for record in font["GSUB"].table.FeatureList.FeatureRecord:
        if record.FeatureTag == "calt":
            kept = [i for i in record.Feature.LookupListIndex if i not in exclude]
            record.Feature.LookupListIndex = kept
            record.Feature.LookupCount = len(kept)
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def _hb_font(data: bytes) -> hb.Font:
    return hb.Font(hb.Face(data))


def _shape(font: hb.Font, text: str) -> tuple[str, ...]:
    return tuple(font.glyph_to_string(g) for g in _glyph_ids(font, text))


def _glyph_ids(font: hb.Font, text: str) -> tuple[int, ...]:
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    return tuple(info.codepoint for info in buffer.glyph_infos)


def missing_from_snapshot(
    inventory: Inventory, selection: Selection, snapshot: Path = SNAPSHOT_FILE
) -> list[str]:
    """Ligatures the Ligature snapshot records that `inventory` lacks, unless excluded."""
    data = tomllib.loads(Path(snapshot).read_text())
    fixed = [t for t in data["fixed"] if t not in inventory.fixed]
    families = [b for b in data["sequence_families"] if b not in inventory.sequence_families]
    return [t for t in fixed + families if t not in selection.exclude]


def write_snapshot(ligature_source_file: Path, snapshot: Path = SNAPSHOT_FILE) -> None:
    inventory = read_inventory(ligature_source_file)
    commit = subprocess.run(
        ["git", "-C", str(FIRA_SUBMODULE), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    def toml_list(items) -> str:
        return "[\n" + "".join(f"    {json.dumps(i, ensure_ascii=False)},\n" for i in items) + "]"

    Path(snapshot).write_text(
        "# The Ligature snapshot: the ligatures the pinned Fira Code has. The build warns\n"
        "# about any the Ligature source lacks. Generated by `make ligature-snapshot`;\n"
        "# refresh it after moving the fonts/fira pin, once the changes are understood.\n"
        f'fira = "{commit}"\n'
        f"fixed = {toml_list(sorted(inventory.fixed))}\n"
        f"sequence_families = {toml_list(sorted(inventory.sequence_families))}\n"
    )


if __name__ == "__main__":
    write_snapshot(ligature_source("Regular"))
    print(f"wrote {SNAPSHOT_FILE}")
