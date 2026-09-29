# Catalogue of Input fonts for `ligaturize-all`: the mapping from input font
# paths to output font names, plus the batch build settings.

#### User configurable settings ####

# For the prefixed_fonts below, what word do we stick in front of the font name?
LIGATURIZED_FONT_NAME_PREFIX = "Liga"

# Where to put the generated fonts, and the variant that also copies character
# glyphs from Fira Code (ligaturize-all --copy-character-glyphs).
OUTPUT_DIR = "fonts/output/"
OUTPUT_DIR_WITH_CHARACTERS = "fonts/output-with-characters/"

# When copying character glyphs, how different in width (as a fraction of the
# Input font's Cell width) one must be to be scaled to fit rather than centered.
SCALE_CHARACTER_GLYPHS_THRESHOLD = 0.1

#### Fonts that should be prefixed with "Liga" when ligaturized. ####
# Don't put fonts licensed under UFL here, and don't put fonts licensed under
# SIL OFL here either unless they haven't specified a Reserved Font Name.

prefixed_fonts = [
    # Apache 2.0 license
    "fonts/codeface/fonts/cousine/*.ttf",
    "fonts/codeface/fonts/droid-sans-mono/*.ttf",
    "fonts/codeface/fonts/meslo/*.ttf",
    "fonts/codeface/fonts/roboto-mono/*.ttf",
    # MIT license
    "fonts/codeface/fonts/dejavu-sans-mono/*.ttf",
    "fonts/codeface/fonts/hack/*.ttf",
    # SIL OFL with no Reserved Font Name
    "fonts/codeface/fonts/edlo/*.ttf",
    "fonts/codeface/fonts/inconsolata/*.ttf",
    "fonts/spacemono/fonts/*.ttf",
]

#### Fonts that need to be renamed. ####
# These are fonts that either have name collisions with the prefixed_fonts
# above, or are released under licenses that permit modification only if we
# change the name of the modified fonts.

renamed_fonts = {
    # This doesn't have a reserved name, but if we don't rename it it'll collide
    # with its sibling Fantasque Sans Mono Normal, listed above.
    "fonts/FantasqueSansMono-Normal/*.otf": "Liga Fantasque Sans Mono",
    "fonts/FantasqueSansMono-Normal/*.ttf": "Liga Fantasque Sans Mono",
    "fonts/FantasqueSansMono-NoLoopK/*.otf": "Liga Fantasque Sans Mono NoLoopK",
    "fonts/FantasqueSansMono-NoLoopK/*.ttf": "Liga Fantasque Sans Mono NoLoopK",
    "fonts/FantasqueSansMono-LargeLineHeight/*.otf": "Liga Fantasque Sans Mono LargeLineHeight",
    "fonts/FantasqueSansMono-LargeLineHeight/*.ttf": "Liga Fantasque Sans Mono LargeLineHeight",
    "fonts/FantasqueSansMono-LargeLineHeight-NoLoopK/*.otf": "Liga Fantasque Sans Mono LargeLineHeight NoLoopK",
    "fonts/FantasqueSansMono-LargeLineHeight-NoLoopK/*.ttf": "Liga Fantasque Sans Mono LargeLineHeight NoLoopK",
    # SIL OFL with reserved name
    "fonts/codeface/fonts/anonymous-pro/*.ttf": "Liganymous",
    "fonts/plex/IBM-Plex-Mono/fonts/complete/ttf/*.ttf": "Ligalex Mono",
    "fonts/codeface/fonts/oxygen-mono/*.otf": "Liga O2 Mono",
    "fonts/codeface/fonts/source-code-pro/*.ttf": "LigaSrc Pro",
    "fonts/SourceCodeVariable*": "LigaSrc Variable",
    "fonts/Hermit/*.otf": "Ligamit",
    # UFL
    "fonts/codeface/fonts/ubuntu-mono/*.ttf": "Ubuntu Mono Ligaturized",
}

#### Fonts with glyphs named like Fira Code's (ADR 0002). ####
# Glyphs copied into fonts matching these patterns get the prefix in their names.

glyph_namespaces = {
    "fonts/FantasqueSansMono-*/*": "fira.",
}

#### Fonts we can't ligaturize. ####
# Fonts that we can't ligaturize because their licences do not permit derivative
# works of any kind.
# Individual users may still be able to make ligaturized versions for personal
# use, but we can't check them into the repo or include them in releases.

# prefixed_fonts += [
#   'CamingoCode*',
#   'SFMono*',
# ]
