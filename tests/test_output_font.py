"""Seam 1: the Output font built by `ligaturize`, checked against its Ligature source."""

import subprocess

import pytest
from fontTools.ttLib import TTFont

from ligaturizer.fira import ligature_source
from ligaturizer.inventory import generate_test_strings, read_inventory

from .shaping import Shaper, mismatches

DEJAVU = "fonts/codeface/fonts/dejavu-sans-mono/DejaVuSansMono.ttf"
# Its GSUB has only a `hebr` script, so Latin text falls back to DFLT.
COUSINE = "fonts/codeface/fonts/cousine/Cousine-Regular.ttf"
FIRA_REGULAR = ligature_source("Regular")


def ligaturize(input_font, output_dir, *args):
    subprocess.run(
        ["ligaturize", input_font, "--output-dir", str(output_dir), *args],
        check=True,
    )
    [output] = list(output_dir.glob("*.[ot]tf"))
    return output


@pytest.fixture(scope="module")
def dejavu(tmp_path_factory):
    return ligaturize(DEJAVU, tmp_path_factory.mktemp("dejavu"))


def test_sequence_ligatures_render_at_any_length(dejavu):
    shaper = Shaper(dejavu)

    for text in ["->", "------>", "<====>", "#####", "__________"]:
        glyphs = shaper.glyph_names(text)
        assert all(g.endswith(".seq") or g.endswith(".spacer") for g in glyphs), (text, glyphs)


def test_output_font_matches_fira_for_every_test_string(dejavu):
    coverage = {chr(c) for c in TTFont(dejavu).getBestCmap()}
    strings = generate_test_strings(read_inventory(FIRA_REGULAR), coverage=coverage)

    failures = mismatches(dejavu, FIRA_REGULAR, strings)

    assert failures == [], f"{len(failures)} of {len(strings)} strings differ:\n" + "\n".join(
        failures[:20]
    )


def test_transplanted_glyphs_advance_one_cell_width(dejavu):
    font = TTFont(dejavu)
    cell_width = font["hmtx"][font.getBestCmap()[ord("m")]][0]
    transplanted = [g for g in font.getGlyphOrder() if g.endswith((".liga", ".seq", ".spacer"))]

    assert transplanted
    assert {font["hmtx"][g][0] for g in transplanted} == {cell_width}


def test_calt_applies_when_the_input_font_has_no_latin_script(tmp_path):
    shaper = Shaper(ligaturize(COUSINE, tmp_path))

    assert shaper.glyph_names("&&") == ["ampersand.spacer", "ampersand_ampersand.liga"]


def test_output_font_compiles_without_fonttools_warnings(dejavu, caplog):
    font = TTFont(dejavu)
    font["GSUB"].compile(font)

    assert caplog.records == []
