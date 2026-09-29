"""The font catalogue: `ligaturize-all` builds what `fonts.toml` lists, where it says."""

import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont

from ligaturizer.catalog import read_catalogue

HACK = "fonts/codeface/fonts/hack/Hack-Regular.ttf"
DEJAVU = "fonts/codeface/fonts/dejavu-sans-mono/DejaVuSansMono.ttf"
COUSINE = "fonts/codeface/fonts/cousine/Cousine-Regular.ttf"


def _catalogue(tmp_path, fonts: str) -> Path:
    path = tmp_path / "fonts.toml"
    path.write_text(
        fonts
        + f"""
[settings]
name_prefix = "Lig"
scale_character_glyphs_threshold = 0.1
output_dir = "{tmp_path}/release"
output_dir_with_characters = "{tmp_path}/release-chars"
personal_output_dir = "{tmp_path}/personal"
personal_output_dir_with_characters = "{tmp_path}/personal-chars"
"""
    )
    return path


def _ligaturize_all(catalogue, *args):
    return subprocess.run(
        ["ligaturize-all", "--catalogue", str(catalogue), *args],
        capture_output=True,
        text=True,
    )


def _families(directory: Path) -> set[str]:
    if not directory.exists():
        return set()
    return {TTFont(f)["name"].getBestFamilyName() for f in directory.iterdir()}


def test_ligaturize_all_builds_exactly_the_catalogue_fonts(tmp_path):
    catalogue = _catalogue(
        tmp_path,
        f'''
prefixed = ["{HACK}"]
personal = ["{COUSINE}", "fonts/NoSuchFont/*.otf"]

[renamed]
"{DEJAVU}" = "Test Mono"
''',
    )

    run = _ligaturize_all(catalogue)

    assert run.returncode == 0, run.stderr
    assert _families(tmp_path / "release") == {"Lig Hack", "Test Mono"}
    assert _families(tmp_path / "personal") == {"Lig Cousine"}


def test_the_with_characters_variant_has_its_own_directories(tmp_path):
    catalogue = _catalogue(tmp_path, f'personal = ["{COUSINE}"]\n')

    run = _ligaturize_all(catalogue, "--copy-character-glyphs")

    assert run.returncode == 0, run.stderr
    assert _families(tmp_path / "personal-chars") == {"Lig Cousine"}
    assert not (tmp_path / "personal").exists()


def test_a_pattern_matching_nothing_is_an_error(tmp_path):
    catalogue = _catalogue(tmp_path, 'prefixed = ["fonts/NoSuchFont/*.ttf"]\n')

    run = _ligaturize_all(catalogue)

    assert run.returncode != 0
    assert "'fonts/NoSuchFont/*.ttf' didn't match any files" in run.stderr


def test_operator_mono_is_a_personal_use_font():
    catalogue = read_catalogue()

    [entry] = [e for e in catalogue.entries if "Operator-Mono" in e.pattern]
    assert entry.personal
    assert entry.prefix == "Liga"


def test_releases_never_include_personal_use_fonts():
    settings = read_catalogue().settings
    pack = subprocess.run(["make", "-n", "pack"], capture_output=True, text=True, check=True).stdout

    for release in [settings.output_dir, settings.output_dir_with_characters]:
        assert release in pack
    for personal in [settings.personal_output_dir, settings.personal_output_dir_with_characters]:
        assert personal not in pack
        assert not personal.startswith((settings.output_dir, settings.output_dir_with_characters))
