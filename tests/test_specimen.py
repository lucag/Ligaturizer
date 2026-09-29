"""The test pattern and the Specimen, both taken from the Ligature inventory.

These need no FontForge: Fira Code stands in for an Output font.
"""

import re
import subprocess

from ligaturizer.fira import ligature_source
from ligaturizer.inventory import read_inventory
from ligaturizer.selection import Selection, read_selection
from ligaturizer.specimen import specimen_lines, write_specimen
from ligaturizer.testpattern import pattern, table

FIRA_REGULAR = ligature_source("Regular")
_ROW = re.compile(r"^\|(?: [ -~]{6}){8} \|$")


def test_testpattern_prints_the_table_format():
    run = subprocess.run(
        ["python", "-m", "ligaturizer.testpattern"], capture_output=True, text=True, check=True
    )

    rows = run.stdout.splitlines()
    assert rows
    for row in rows:
        assert _ROW.match(row), row


def test_the_pattern_has_every_fixed_ligature_and_each_sequence_family():
    inventory = read_inventory(FIRA_REGULAR)

    texts = pattern(inventory, Selection())

    assert set(inventory.fixed) <= set(texts)
    for base in inventory.sequence_families:
        assert base * 3 in texts
    assert "<==" in texts and "==>" in texts


def test_the_pattern_leaves_out_excluded_sequences():
    inventory = read_inventory(FIRA_REGULAR)

    texts = pattern(inventory, Selection(exclude=("www", "&&")))

    assert "www" not in texts and "&&" not in texts


def test_the_committed_testpattern_file_is_up_to_date():
    expected = table(pattern(read_inventory(FIRA_REGULAR), read_selection()))

    with open("testpattern") as f:
        committed = [line.rstrip("\n") for line in f if line.startswith("|")]

    assert committed == expected


def test_the_specimen_is_self_contained_and_shows_each_line_in_both_fonts(tmp_path):
    lines = specimen_lines(read_inventory(FIRA_REGULAR), read_selection())
    page = tmp_path / "specimen.html"

    write_specimen(FIRA_REGULAR, FIRA_REGULAR, lines, page)

    text = page.read_text()
    assert text.count("src: url(data:font/otf;base64,") == 2
    assert not re.search(r"(src|href)=\"https?:", text)
    assert text.count('<div class="fira">&lt;!--') == text.count('<div class="output">&lt;!--')
    assert text.count('<div class="output">') == len(lines)
