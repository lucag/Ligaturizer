"""The Specimen: an Output font and its Ligature source side by side, for review.

`make specimen` writes one self-contained HTML page per Output font, with both
fonts embedded, showing the same text in each: a keyboard's worth of
characters, the test pattern, and Sequence ligatures at growing lengths. It's
for a human to look at (e.g. for ligatures sitting too high or low); it never
passes or fails.
"""

import base64
import html
from argparse import ArgumentParser
from pathlib import Path

from fontTools.ttLib import TTFont

from ligaturizer.catalog import read_catalogue
from ligaturizer.fira import ligature_source, nearest_weight
from ligaturizer.inventory import Inventory, read_inventory
from ligaturizer.selection import Selection, read_selection
from ligaturizer.testpattern import pattern, table

SPECIMEN_DIR = Path("fonts/specimen")

KEYBOARD = [
    "~!@#$%^&*()_+ `1234567890-=",
    "QWERTYUIOP{}| qwertyuiop[]\\",
    "ASDFGHJKL:\"   asdfghjkl;'",
    "ZXCVBNM< >?   zxcvbnm,./",
]
_RUNS = range(2, 7)


def specimen_lines(inventory: Inventory, selection: Selection) -> list[str]:
    lines = [*KEYBOARD, "", *table(pattern(inventory, selection)), ""]
    for base, decorations in sorted(inventory.sequence_families.items()):
        lines.append(" ".join(base * n for n in _RUNS))
        for d in sorted(decorations):
            lines.append(" ".join(d + base * n for n in _RUNS))
            lines.append(" ".join(base * n + d for n in _RUNS))
    return [line if not any(x in line for x in selection.exclude) else "" for line in lines]


def write_specimen(output_font: Path, source: Path, lines: list[str], path: Path) -> None:
    name = TTFont(output_font)["name"].getBestFullName()
    rows = "\n".join(
        f'<div class="fira">{html.escape(line) or "&nbsp;"}</div>'
        f'<div class="output">{html.escape(line) or "&nbsp;"}</div>'
        for line in lines
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _PAGE.format(
            title=html.escape(f"Specimen: {name}"),
            name=html.escape(name),
            source=html.escape(source.name),
            output_file=html.escape(output_font.name),
            fira_font=_font_face("Fira", source),
            output_font=_font_face("Output", output_font),
            rows=rows,
        )
    )


def _font_face(family: str, path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    kind = "opentype" if path.suffix.lower() == ".otf" else "truetype"
    return (
        f'@font-face {{ font-family: "{family}";'
        f' src: url(data:font/{path.suffix[1:].lower()};base64,{data}) format("{kind}"); }}'
    )


_PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{fira_font}
{output_font}
:root {{ --bg: #fff; --fg: #1a1a1a; --muted: #666; --rule: #ddd; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #16161a; --fg: #e8e8e8; --muted: #999; --rule: #333; }}
}}
body {{ margin: 0; padding: 24px 16px; background: var(--bg); color: var(--fg);
  font: 14px/1.4 system-ui, sans-serif; }}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
p {{ margin: 0 0 20px; color: var(--muted); }}
.grid {{ display: grid; grid-template-columns: max-content max-content; gap: 0 48px;
  font-size: 18px; line-height: 1.5; white-space: pre; overflow-x: auto; }}
.head {{ font: 600 13px system-ui, sans-serif; color: var(--muted);
  border-bottom: 1px solid var(--rule); margin-bottom: 8px; padding-bottom: 4px; }}
.fira {{ font-family: "Fira", monospace; }}
.output {{ font-family: "Output", monospace; }}
</style>
<h1>{name}</h1>
<p>{output_file}, beside its Ligature source {source}. For review by eye; not a test.</p>
<div class="grid">
<div class="head">{source}</div><div class="head">{output_file}</div>
{rows}
</div>
</html>
"""


def _index(pages: list[Path]) -> str:
    links = "\n".join(
        f'<li><a href="{html.escape(p.relative_to(SPECIMEN_DIR).as_posix())}">'
        f"{html.escape(p.relative_to(SPECIMEN_DIR).as_posix())}</a></li>"
        for p in pages
    )
    return (
        '<!doctype html>\n<meta charset="utf-8">\n<title>Specimens</title>\n'
        f"<h1>Specimens</h1>\n<ul>\n{links}\n</ul>\n"
    )


def main() -> None:
    parser = ArgumentParser(description="Write a Specimen for each Output font.")
    parser.add_argument(
        "output_fonts",
        nargs="*",
        type=Path,
        help="Output fonts to show (default: every font in the catalogue's output directories).",
    )
    args = parser.parse_args()

    fonts = args.output_fonts
    if not fonts:
        settings = read_catalogue().settings
        dirs = [
            settings.output_dir,
            settings.output_dir_with_characters,
            settings.personal_output_dir,
            settings.personal_output_dir_with_characters,
        ]
        fonts = sorted(f for d in dirs for f in Path(d).glob("*.[ot]tf"))

    selection = read_selection()
    pages = []
    for font in fonts:
        source = ligature_source(nearest_weight(TTFont(font)["OS/2"].usWeightClass))
        page = SPECIMEN_DIR / font.parent.name / f"{font.stem}.html"
        write_specimen(font, source, specimen_lines(read_inventory(source), selection), page)
        pages.append(page)
        print(f"wrote {page}")
    if pages:
        (SPECIMEN_DIR / "index.html").write_text(_index(pages))
        print(f"wrote {SPECIMEN_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
