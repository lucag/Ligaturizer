import shutil
import subprocess

from fontTools.ttLib import TTFont

HACK = "fonts/codeface/fonts/hack/Hack-Regular.ttf"


def test_ligaturize_produces_an_output_font(tmp_path):
    subprocess.run(
        ["ligaturize", HACK, "--output-dir", str(tmp_path), "--prefix", "Liga"],
        check=True,
    )

    [output] = list(tmp_path.glob("*.ttf"))
    assert TTFont(output)["name"].getBestFamilyName() == "Liga Hack"


def test_missing_fontforge_is_a_clear_error(tmp_path):
    result = subprocess.run(
        [shutil.which("ligaturize"), HACK, "--output-dir", str(tmp_path)],
        env={"PATH": "/usr/bin:/bin", "FONTFORGE": "/nonexistent/fontforge"},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "FONTFORGE" in result.stderr
