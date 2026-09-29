"""Seam 2: the Ligature inventory and the test strings generated from it.

These tests need only fontTools and uharfbuzz, never FontForge.
"""

import uharfbuzz as hb

from ligaturizer.fira import WEIGHTS, ligature_source
from ligaturizer.inventory import generate_test_strings, read_inventory
from ligaturizer.selection import missing_from_snapshot, read_selection

FIRA_REGULAR = ligature_source("Regular")


def _inventory():
    return read_inventory(FIRA_REGULAR)


def test_fixed_ligatures_are_listed_by_their_text():
    fixed = _inventory().fixed

    assert fixed["!="] == "exclam_equal.liga"
    assert fixed["&&"] == "ampersand_ampersand.liga"
    assert fixed["<!--"] == "less_exclam_hyphen_hyphen.liga"
    assert fixed["www"] == "w_w_w.liga"


def test_arrows_are_sequence_ligatures_not_fixed_ones():
    inventory = _inventory()

    assert "->" not in inventory.fixed
    assert set(inventory.sequence_families) == {"-", "=", "#", "_"}
    assert {"<", "<<", ">", ">>", "|", "||"} <= inventory.sequence_families["-"]


def test_ligature_characters_are_those_ligatures_are_made_of():
    characters = _inventory().ligature_characters

    assert {"-", "=", "<", ">", "|", "&", "#", "_", "w"} <= characters
    assert not {"a", "9", "Α"} & characters


def test_strings_cover_every_sequence_family_at_lengths_2_to_10():
    strings = generate_test_strings(_inventory())

    for base in "-=#_":
        lengths = {len(s) for s in strings if s == base * len(s)}
        assert set(range(2, 11)) <= lengths, base
    assert "<------>" in strings
    assert "<<====>>" in strings


def test_strings_include_fixed_ligatures_and_their_neighbours():
    strings = set(generate_test_strings(_inventory()))

    assert {"!=", "a!=", "!=a", "|||", "<!--"} <= strings


def test_strings_are_filtered_by_coverage():
    inventory = _inventory()
    coverage = inventory.ligature_characters - {"#"}

    strings = generate_test_strings(inventory, coverage=coverage)

    assert strings
    assert not any("#" in s for s in strings)


def test_random_strings_are_deterministic_for_a_seed():
    inventory = _inventory()

    assert generate_test_strings(inventory, seed=1) == generate_test_strings(inventory, seed=1)
    assert generate_test_strings(inventory, seed=1) != generate_test_strings(inventory, seed=2)


def test_shaping_the_strings_with_fira_reaches_every_ligature_glyph():
    """The strings exercise every glyph Fira's calt can produce."""
    inventory = _inventory()
    blob = hb.Blob.from_file_path(str(FIRA_REGULAR))
    font = hb.Font(hb.Face(blob))
    reached = set()
    for text in generate_test_strings(inventory):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, {"calt": True})
        reached.update(font.glyph_to_string(info.codepoint) for info in buf.glyph_infos)

    assert inventory.ligature_glyphs - reached == set()


def test_test_strings_leave_out_excluded_sequences():
    strings = generate_test_strings(_inventory(), exclude=("www",))

    assert not [s for s in strings if "www" in s]
    assert [s for s in strings if "ww" in s]


def test_every_fira_weight_has_the_snapshot_ligatures():
    selection = read_selection()

    for weight in WEIGHTS:
        assert missing_from_snapshot(read_inventory(ligature_source(weight)), selection) == [], (
            weight
        )
