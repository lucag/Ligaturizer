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
# Double-width CJK glyphs beside a 500-unit Cell width.
MPLUS = "fonts/codeface/cjk-fonts/mplus1m/mplus-1m-regular.ttf"
PLEX_MONO = "fonts/plex/IBM-Plex-Mono/fonts/complete/ttf"
PLEX_SANS = "fonts/plex/IBM-Plex-Sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf"
FIRA_REGULAR = ligature_source("Regular")


def run_ligaturize(input_font, output_dir, *args):
    return subprocess.run(
        ["ligaturize", input_font, "--output-dir", str(output_dir), *args],
        capture_output=True,
        text=True,
    )


def ligaturize(input_font, output_dir, *args):
    run = run_ligaturize(input_font, output_dir, *args)
    assert run.returncode == 0, run.stderr
    [output] = list(output_dir.glob("*.[ot]tf"))
    return output


def reported_ligature_source(input_font, output_dir, *args):
    run = run_ligaturize(input_font, output_dir, *args)
    assert run.returncode == 0, run.stderr
    [line] = [line for line in run.stdout.splitlines() if "using ligatures from" in line]
    return line.split("/")[-1]


def shaping_failures(output, ligature_source):
    coverage = {chr(c) for c in TTFont(output).getBestCmap()}
    strings = generate_test_strings(read_inventory(ligature_source), coverage=coverage)
    return mismatches(output, ligature_source, strings)


@pytest.fixture(scope="module")
def dejavu(tmp_path_factory):
    return ligaturize(DEJAVU, tmp_path_factory.mktemp("dejavu"))


def test_sequence_ligatures_render_at_any_length(dejavu):
    shaper = Shaper(dejavu)

    for text in ["->", "------>", "<====>", "#####", "__________"]:
        glyphs = shaper.glyph_names(text)
        assert all(g.endswith(".seq") or g.endswith(".spacer") for g in glyphs), (text, glyphs)


def test_output_font_matches_fira_for_every_test_string(dejavu):
    failures = shaping_failures(dejavu, FIRA_REGULAR)

    assert failures == [], f"{len(failures)} strings differ:\n" + "\n".join(failures[:20])


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


def test_proportional_input_fonts_are_rejected(tmp_path):
    run = run_ligaturize(PLEX_SANS, tmp_path)

    assert run.returncode != 0
    assert "IBMPlexSans-Regular.ttf is not monospaced" in run.stderr
    assert list(tmp_path.iterdir()) == []


def test_double_width_cjk_glyphs_are_accepted(tmp_path):
    font = TTFont(ligaturize(MPLUS, tmp_path))

    assert font["hmtx"]["ampersand_ampersand.liga"][0] == 500


@pytest.mark.parametrize(
    ("input_font", "weight"),
    [
        # Named Light*Italic*, which the PostScript-name guess used to miss.
        ("IBMPlexMono-LightItalic.ttf", "Light"),
        ("IBMPlexMono-Bold.ttf", "Bold"),
        # usWeightClass 450.
        ("IBMPlexMono-Text.ttf", "Retina"),
    ],
)
def test_ligature_source_is_the_weight_nearest_the_input_font(tmp_path, input_font, weight):
    source = ligature_source(weight)

    assert reported_ligature_source(f"{PLEX_MONO}/{input_font}", tmp_path) == source.name
    assert shaping_failures(next(tmp_path.glob("*.ttf")), source) == []


def test_weight_option_overrides_the_input_font_weight(tmp_path):
    assert reported_ligature_source(DEJAVU, tmp_path, "--weight", "Bold") == "FiraCode-Bold.otf"
