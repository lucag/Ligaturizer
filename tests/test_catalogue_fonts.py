"""Seam 1 over the font catalogue: the Shaping check and structural checks.

Each Output font is built as the catalogue says, in both variants (with and
without --copy-character-glyphs). By default this runs on a representative
set of catalogue fonts; `pytest -m slow` (`make test-catalogue`) runs it on
every font in the catalogue.
"""

import subprocess

import pytest
from fontTools.ttLib import TTFont

from ligaturizer.build import cell_width
from ligaturizer.catalog import read_catalogue
from ligaturizer.fira import ligature_source, nearest_weight
from ligaturizer.inventory import generate_test_strings, read_inventory
from ligaturizer.selection import read_selection, resolve
from ligaturizer.transplant import plan_glyphs

from .shaping import Shaper, mismatches

CATALOGUE = read_catalogue()
BUILDS = {b.input_font_file: b for b in CATALOGUE.builds()}
SELECTION = read_selection()

# One catalogue font for each risk the pipeline has to handle.
REPRESENTATIVE = {
    # Its own calt, and glyphs named like Fira's (so a glyph namespace).
    "cff-otf": "fonts/FantasqueSansMono-Normal/FantasqueSansMono-Regular.otf",
    "truetype-ttf": "fonts/codeface/fonts/dejavu-sans-mono/DejaVuSansMono.ttf",
    # Its own calt turns -> into an arrow; it lacks Greek.
    "own-calt-no-greek": "fonts/spacemono/fonts/SpaceMono-Regular.ttf",
    # A Cell width of half an em, the narrowest in the catalogue.
    "narrow-cell": "fonts/codeface/fonts/inconsolata/Inconsolata-Regular.ttf",
    # usWeightClass 100 and 900.
    "lightest": "fonts/plex/IBM-Plex-Mono/fonts/complete/ttf/IBMPlexMono-Thin.ttf",
    "heaviest": "fonts/codeface/fonts/source-code-pro/SourceCodePro-Black.ttf",
}

VARIANTS = [
    pytest.param(False, id="plain"),
    pytest.param(True, id="with-characters"),
]


def _build(font, output_dir, with_characters):
    """Build one catalogue font the way `ligaturize-all` does."""
    args = ["--output-dir", str(output_dir), "--prefix", font.prefix or ""]
    if font.output_name:
        args += ["--output-name", font.output_name]
    if font.glyph_namespace:
        args += ["--glyph-namespace", font.glyph_namespace]
    if with_characters:
        threshold = CATALOGUE.settings.scale_character_glyphs_threshold
        args += ["--copy-character-glyphs", "--scale-character-glyphs-threshold", str(threshold)]
    run = subprocess.run(
        ["ligaturize", font.input_font_file, *args], capture_output=True, text=True
    )
    assert run.returncode == 0, run.stderr
    [output] = list(output_dir.glob("*.[ot]tf"))
    return output


def _check(font, output, with_characters):
    input_font, output_font = TTFont(font.input_font_file), TTFont(output)
    width = cell_width(input_font)
    source = ligature_source(nearest_weight(input_font["OS/2"].usWeightClass))

    # Structural checks: the font compiles, every glyph the build copied from
    # the Ligature source is one Cell wide, and the Input font's glyphs keep
    # their advances.
    output_font["GSUB"].compile(output_font)
    excluded, _ = resolve(SELECTION, source)
    transplanted = set(plan_glyphs(TTFont(source), font.glyph_namespace, excluded).values())
    assert transplanted <= set(output_font.getGlyphOrder())
    assert {output_font["hmtx"][g][0] for g in transplanted} == {width}
    cmap = output_font.getBestCmap()
    copied = {cmap[ord(c)] for c in SELECTION.copy_characters if ord(c) in cmap}
    kept = [g for g in input_font.getGlyphOrder() if not (with_characters and g in copied)]
    assert [output_font["hmtx"][g][0] for g in kept] == [input_font["hmtx"][g][0] for g in kept]
    if with_characters:
        assert copied
        assert {output_font["hmtx"][g][0] for g in copied} == {width}

    # Required ligatures are there, and excluded ones aren't.
    shaper = Shaper(output)
    encoded = set(output_font.getBestCmap().values())
    for text in SELECTION.require:
        assert not set(shaper.glyph_names(text)) <= encoded, text
    for text in SELECTION.exclude:
        if set(text) <= set(map(chr, output_font.getBestCmap())):
            assert not set(shaper.glyph_names(text)) & transplanted, text

    # The Shaping check, against the Ligature source the build used.
    coverage = {chr(c) for c in output_font.getBestCmap()}
    strings = generate_test_strings(
        read_inventory(source), coverage=coverage, exclude=SELECTION.exclude
    )
    failures = mismatches(output, source, strings, font.glyph_namespace)
    assert failures == [], f"{len(failures)} strings differ:\n" + "\n".join(failures[:20])


@pytest.mark.parametrize("with_characters", VARIANTS)
@pytest.mark.parametrize(
    "font", [pytest.param(BUILDS[f], id=role) for role, f in REPRESENTATIVE.items()]
)
def test_representative_output_fonts(tmp_path, font, with_characters):
    _check(font, _build(font, tmp_path, with_characters), with_characters)


@pytest.mark.slow
@pytest.mark.parametrize("with_characters", VARIANTS)
@pytest.mark.parametrize("font", [pytest.param(b, id=f) for f, b in BUILDS.items()])
def test_catalogue_output_fonts(tmp_path, font, with_characters):
    _check(font, _build(font, tmp_path, with_characters), with_characters)
