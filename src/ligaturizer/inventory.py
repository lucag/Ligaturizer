"""The Ligature inventory: what a Ligature source's `calt` feature can do.

Reads the compiled `calt` lookups of a built Fira Code OTF (ADR 0001) and
generates the test strings the Shaping check runs. Needs only fontTools.
"""

import random
import re
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont

_PIECE = re.compile(r"^(?P<family>.+)_(start|middle|end)\.seq$")
# Characters placed next to each Fixed ligature, besides the ligature
# characters, to exercise the contexts where Fira suppresses a ligature.
_EXTRA_NEIGHBOURS = ("a", "1", " ")
_LONGEST_RUN = 10
_LONGEST_RANDOM = 12


@dataclass(frozen=True)
class Inventory:
    # Text of each Fixed ligature -> its glyph name, e.g. "!=" -> "exclam_equal.liga".
    fixed: dict[str, str]
    # Base character of each Sequence ligature family -> the decorations that can
    # join its runs, e.g. "-" -> {"<", "<<", ">", ">>", "|", "||"}.
    sequence_families: dict[str, frozenset[str]]
    # Characters that Fixed and Sequence ligatures are made of.
    ligature_characters: frozenset[str]
    # Fixed ligature glyphs and Pieces calt can produce.
    ligature_glyphs: frozenset[str]


def read_inventory(ligature_source: Path) -> Inventory:
    font = TTFont(ligature_source)
    outputs = _calt_outputs(font)

    char_of = {}
    for codepoint, name in sorted(font.getBestCmap().items()):
        char_of.setdefault(name, chr(codepoint))

    def text_of(names):
        return "".join(char_of[n] for n in names)

    fixed = {}
    families: dict[str, set[str]] = {}
    for glyph in sorted(outputs):
        if glyph.endswith(".liga"):
            fixed[text_of(glyph.removesuffix(".liga").split("_"))] = glyph
        elif m := _PIECE.match(glyph):
            *decoration, base = m["family"].split("_")
            decorations = families.setdefault(char_of[base], set())
            if decoration:
                decorations.add(text_of(decoration))

    return Inventory(
        fixed=fixed,
        sequence_families={base: frozenset(d) for base, d in families.items()},
        ligature_characters=frozenset(
            "".join(fixed) + "".join(families) + "".join("".join(d) for d in families.values())
        ),
        ligature_glyphs=frozenset(g for g in outputs if g.endswith((".liga", ".seq"))),
    )


def generate_test_strings(
    inventory: Inventory,
    *,
    coverage: frozenset[str] | set[str] | None = None,
    seed: int = 0,
    random_count: int = 2000,
) -> list[str]:
    """Strings for the Shaping check, in a stable order and without duplicates.

    Covers every Fixed ligature alone and next to each neighbouring character,
    every Sequence ligature family at run lengths 2-10 with each decoration at
    its start, middle and end, and `random_count` random strings from `seed`.
    Strings with characters outside `coverage` (when given) are dropped.
    """
    strings = []

    neighbours = sorted(inventory.ligature_characters) + list(_EXTRA_NEIGHBOURS)
    for text in inventory.fixed:
        strings.append(text)
        for n in neighbours:
            strings += [n + text, text + n]

    for base, decorations in inventory.sequence_families.items():
        ends = ["", *sorted(decorations)]
        for left in ends:
            for right in ends:
                for run in range(1, _LONGEST_RUN + 1):
                    strings.append(left + base * run + right)
                for middle in decorations:
                    for a in range(1, 4):
                        for b in range(1, 4):
                            strings.append(left + base * a + middle + base * b + right)

    rng = random.Random(seed)
    alphabet = sorted(inventory.ligature_characters) + list(_EXTRA_NEIGHBOURS)
    for _ in range(random_count):
        length = rng.randint(1, _LONGEST_RANDOM)
        strings.append("".join(rng.choice(alphabet) for _ in range(length)))

    strings = [s for s in strings if len(s) >= 2]
    if coverage is not None:
        strings = [s for s in strings if set(s) <= coverage]
    return list(dict.fromkeys(strings))


def _calt_outputs(font: TTFont) -> set[str]:
    """Glyphs produced by the default calt feature, following nested lookups."""
    gsub = font["GSUB"].table
    lookups = gsub.LookupList.Lookup
    pending = [
        index
        for record in gsub.FeatureList.FeatureRecord
        if record.FeatureTag == "calt"
        for index in record.Feature.LookupListIndex
    ]
    seen: set[int] = set()
    outputs: set[str] = set()
    while pending:
        index = pending.pop()
        if index in seen:
            continue
        seen.add(index)
        lookup = lookups[index]
        for subtable in lookup.SubTable:
            if lookup.LookupType == 7:
                subtable = subtable.ExtSubTable
            if hasattr(subtable, "mapping"):  # single or multiple substitution
                for target in subtable.mapping.values():
                    outputs.update([target] if isinstance(target, str) else target)
            elif hasattr(subtable, "ligatures"):
                outputs.update(lig.LigGlyph for ligs in subtable.ligatures.values() for lig in ligs)
            elif hasattr(subtable, "alternates"):
                outputs.update(g for alts in subtable.alternates.values() for g in alts)
            else:  # contextual: follow the lookups it applies
                for rule_set in _rule_sets(subtable):
                    pending.extend(record.LookupListIndex for record in rule_set)
    return outputs


def _rule_sets(subtable):
    """The substitution-record lists of a (chaining) contextual subtable."""
    if hasattr(subtable, "SubstLookupRecord"):  # format 3
        yield subtable.SubstLookupRecord
    for set_name in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
        for rule_set in getattr(subtable, set_name, None) or []:
            if rule_set is None:
                continue
            for rule in getattr(rule_set, set_name.replace("Set", ""), None) or []:
                yield rule.SubstLookupRecord
