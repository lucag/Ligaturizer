"""Traversal of a font's compiled `calt` feature."""

from collections.abc import Iterator

from fontTools.ttLib import TTFont


def calt_lookup_indices(gsub, exclude: frozenset[int] = frozenset()) -> list[int]:
    """Indices of the lookups the calt feature applies directly, in order, less `exclude`."""
    indices: list[int] = []
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag == "calt":
            indices += [
                i for i in record.Feature.LookupListIndex if i not in indices and i not in exclude
            ]
    return indices


def reachable_lookups(gsub, exclude: frozenset[int] = frozenset()) -> list[int]:
    """calt's lookups, less `exclude`, plus every lookup their contextual rules apply, sorted."""
    return sorted(_reachable(gsub, calt_lookup_indices(gsub, exclude)))


def _reachable(gsub, start: list[int]) -> set[int]:
    lookups = gsub.LookupList.Lookup
    pending = list(start)
    seen: set[int] = set()
    while pending:
        index = pending.pop()
        if index in seen:
            continue
        seen.add(index)
        for subtable in subtables(lookups[index]):
            for records in rule_records(subtable):
                pending.extend(record.LookupListIndex for record in records)
    return seen


def subtables(lookup) -> Iterator:
    for subtable in lookup.SubTable:
        yield subtable.ExtSubTable if lookup.LookupType == 7 else subtable


def rule_records(subtable) -> Iterator[list]:
    """The substitution-record lists of a (chaining) contextual subtable."""
    if hasattr(subtable, "SubstLookupRecord"):  # format 3
        yield subtable.SubstLookupRecord
    for set_name in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
        for rule_set in getattr(subtable, set_name, None) or []:
            if rule_set is None:
                continue
            for rule in getattr(rule_set, set_name.replace("Set", ""), None) or []:
                yield rule.SubstLookupRecord


def calt_outputs(font: TTFont, exclude: frozenset[int] = frozenset()) -> set[str]:
    """Glyphs produced by the default calt feature, less its lookups in `exclude`."""
    gsub = font["GSUB"].table
    return _outputs(gsub, reachable_lookups(gsub, exclude))


def lookup_outputs(gsub, index: int) -> set[str]:
    """Glyphs produced by one lookup, including through the lookups its rules apply."""
    return _outputs(gsub, _reachable(gsub, [index]))


def _outputs(gsub, indices) -> set[str]:
    outputs: set[str] = set()
    for index in indices:
        for subtable in subtables(gsub.LookupList.Lookup[index]):
            if hasattr(subtable, "mapping"):  # single or multiple substitution
                for target in subtable.mapping.values():
                    outputs.update([target] if isinstance(target, str) else target)
            elif hasattr(subtable, "ligatures"):
                outputs.update(lig.LigGlyph for ligs in subtable.ligatures.values() for lig in ligs)
            elif hasattr(subtable, "alternates"):
                outputs.update(g for alts in subtable.alternates.values() for g in alts)
    return outputs
