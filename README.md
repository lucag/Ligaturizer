# Ligaturizer #

![](images/banner.png)

**Add ligatures to any coding font!**

This script copies the ligatures (glyphs and rendering information) from [Fira Code](https://github.com/tonsky/FiraCode) into any other TrueType or OpenType font. (Note that the ligatures are scale-corrected, but otherwise copied as is from Fira Code; it doesn't create new ligature graphics based on the font you're modifying.)

This repo contains a Python package with a `ligaturize` command that you can use to add the Fira Code ligatures to any font, as well as submodules for some popular coding fonts and a `ligaturize-all` command for ligaturizing all of them at once.

Pre-ligaturized versions are available under [releases](https://github.com/ToxicFrog/Ligaturizer/releases).

Here's a couple examples of the fonts generated: SF Mono & Menlo with ligatures (note the `!=` and `->`):
![](images/sf-mono.png)
![](images/menlo.png)

## Requirements ##
**This Repo**: You'll need the repo and its submodules, so `git clone` with `--recurse-submodules`.

**Using the Fonts**: See the [FiraCode README](https://github.com/tonsky/FiraCode) for a list of supported editors.

**Script**: The project is managed with [uv](https://docs.astral.sh/uv/); run `uv sync` to set it up. It also requires FontForge, which is run as a separate program: it must be on your `PATH`, or `$FONTFORGE` must point at it. For Debian/Ubuntu it is available in the `fontforge` package; for macOS, via brew (`brew install fontforge`).

## Using the Script ##
### Automatic ###

Use automatic mode to easily convert 1 or more font(s).

1.  Put the font(s) you want into `fonts/`.
1.  Edit `fonts.toml` to add your new font(s) to the `prefixed` list. It supports globbing, so if (e.g.) you want to ligaturize all the different weights of FooFont you can add `"fonts/FooFont*"` to the list. Fonts whose license forbids distributing derivatives go in `personal` instead: they're built into `fonts/output-personal/`, which releases never include.
1.  Run `make`.
1.  Retrieve the ligaturized fonts from `fonts/output/`.
1.  The output fonts will be renamed with the prefix "Liga".

`make with-characters` builds a second variant into `fonts/output-with-characters/`, which also takes Fira Code's glyphs for common punctuation (listed under `copy_characters` in `selection.toml`) so it matches the ligatures more closely. `make release` builds and packs both.

### Manual ###

1.  Move/copy the font you want to ligaturize into `fonts/` (or somewhere else convenient).
1.  Run the script:

    ```
    $ uv run ligaturize path/to/input/font.ttf
        --output-dir=path/to/output/dir/ \
        --output-name='Name of Ligaturized Font'
    ```
    e.g.

    ```
    $ uv run ligaturize fonts/Cousine-Regular.ttf
        --output-dir='fonts/output/' \
        --output-name='Ligaturized Cousine'
    ```

    Which will produce `fonts/output/LigaturizedCousine-Regular.ttf`.

The font weight will be inherited from the original file; the font name will be replaced with whatever you specified in `--output-name`. You can also use `--prefix` instead, in which case the original name will be preserved and whatever you put in `--prefix` will be prepended to it.

Ligatures are copied from the Fira Code weight nearest the input font's declared weight (its `usWeightClass`); if that's wrong for your font, pick one with `--weight` (e.g. `--weight Light`).

Every Fira Code ligature is copied except those excluded in `selection.toml`: by default, Fira's text ligatures (`fi`, `fj`, `Fl`, `Il`, `Tl`), which would override the input font's own typography. Edit it to exclude more, or to `require` ligatures the build must find. `ligature-snapshot.toml` records the ligatures the pinned Fira Code has; after moving the `fonts/fira` pin, run `make ligature-snapshot` to refresh it.

With `--copy-character-glyphs`, `ligaturize` also copies Fira Code's glyphs for the characters listed under `copy_characters` in `selection.toml`. A copied glyph whose width differs from the input font's by 10% or more is scaled to fit, and one closer is centered; `--scale-character-glyphs-threshold` changes that 10%.

`ligaturize` supports some additional command line options to (e.g.) change which font ligatures are copied from; run `uv run ligaturize --help` to list them.

## Misc. ##
### Credit ###
This script was originally written by [IlyaSkriblovsky](https://github.com/IlyaSkriblovsky) for adding ligatures to DejaVuSans Mono ([dv-code-font](https://github.com/IlyaSkriblovsky/dv-code-font)). [Navid Rojiani](https://github.com/rojiani) made a few changes to generalize the script so that it works for any font. [ToxicFrog](https://github.com/ToxicFrog) has made a large number of contributions.

### Contributions ###
Contributions always welcome! Please submit a Pull Request, or create an Issue if you have an idea for a feature/enhancement (or bug).

### Related Projects ###
For more awesome programming fonts with ligatures, check out:
1. [FiraCode](https://github.com/tonsky/FiraCode)
2. [Hasklig](https://github.com/i-tu/Hasklig)
