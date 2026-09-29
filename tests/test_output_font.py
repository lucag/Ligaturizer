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
# Its own calt turns `->`, `<-`, `|>` etc. into arrows; its liga makes fi and fl.
SPACE_MONO = "fonts/spacemono/fonts/SpaceMono-Regular.ttf"
# Its own glyphs are named like Fira Code's, e.g. `equal_equal.liga`.
FANTASQUE = "fonts/FantasqueSansMono-Normal/FantasqueSansMono-Regular.ttf"
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


def shaping_failures(output, ligature_source, namespace=""):
    coverage = {chr(c) for c in TTFont(output).getBestCmap()}
    strings = generate_test_strings(read_inventory(ligature_source), coverage=coverage)
    return mismatches(output, ligature_source, strings, namespace)


@pytest.fixture(scope="module")
def dejavu(tmp_path_factory):
    return ligaturize(DEJAVU, tmp_path_factory.mktemp("dejavu"))


@pytest.fixture(scope="module")
def space_mono(tmp_path_factory):
    """Space Mono's Output font, and what `ligaturize --verbose` printed building it."""
    output_dir = tmp_path_factory.mktemp("space-mono")
    run = run_ligaturize(SPACE_MONO, output_dir, "--verbose")
    assert run.returncode == 0, run.stderr
    [output] = list(output_dir.glob("*.ttf"))
    return output, run.stdout


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


def test_input_font_calt_is_replaced(space_mono):
    output, _ = space_mono
    shaper = Shaper(output)

    assert shaper.glyph_names("->") == ["hyphen_start.seq", "greater_hyphen_end.seq"]
    assert shaper.glyph_names("|>") == ["bar.spacer", "bar_greater.liga"]
    assert shaping_failures(output, FIRA_REGULAR) == []


def test_input_font_liga_is_kept(space_mono):
    shaper = Shaper(space_mono[0])

    assert shaper.glyph_names("fi") == ["fi"]
    assert shaper.glyph_names("fl") == ["fl"]


def test_input_font_features_still_apply_to_scripts_it_does_not_list(tmp_path):
    # With no DFLT script, HarfBuzz shapes unlisted scripts with latn's features.
    font = TTFont(SPACE_MONO)
    scripts = font["GSUB"].table.ScriptList
    scripts.ScriptRecord = [s for s in scripts.ScriptRecord if s.ScriptTag == "latn"]
    scripts.ScriptCount = len(scripts.ScriptRecord)
    font.save(tmp_path / "SpaceMono-Regular.ttf")

    shaper = Shaper(ligaturize(tmp_path / "SpaceMono-Regular.ttf", tmp_path / "out"))

    assert shaper.glyph_names("fi", script="Cyrl") == ["fi"]
    assert shaper.glyph_names("->", script="Cyrl") == ["hyphen_start.seq", "greater_hyphen_end.seq"]


def test_dropped_references_are_summarized_by_script(tmp_path):
    stdout = run_ligaturize(DEJAVU, tmp_path).stdout

    lines = stdout.splitlines()
    [i] = [i for i, line in enumerate(lines) if "dropped calt references" in line]
    assert lines[i + 1].strip().startswith("Cyrillic ")
    assert lines[i + 1].endswith("(--verbose lists them)")
    assert "U+" not in stdout


def test_verbose_names_each_dropped_reference(space_mono):
    output, stdout = space_mono

    # Space Mono has no Greek.
    assert "U+03B1 GREEK SMALL LETTER ALPHA" in stdout
    assert "U+0416 CYRILLIC CAPITAL LETTER ZHE" in stdout
    assert 0x03B1 not in TTFont(output).getBestCmap()


def test_glyph_name_clash_fails_the_build(tmp_path):
    run = run_ligaturize(FANTASQUE, tmp_path)

    assert run.returncode != 0
    assert "--glyph-namespace" in run.stderr
    assert list(tmp_path.iterdir()) == []


def test_glyph_namespace_prefixes_transplanted_glyphs(tmp_path):
    output = ligaturize(FANTASQUE, tmp_path, "--glyph-namespace", "fira.")
    shaper = Shaper(output)

    assert shaper.glyph_names("==") == ["fira.equal.spacer", "fira.equal_equal.liga"]
    assert shaping_failures(output, FIRA_REGULAR, namespace="fira.") == []
