"""Traversal of a font's compiled `calt` feature."""

from collections.abc import Iterator

from fontTools.ttLib import TTFont


def calt_lookup_indices(gsub) -> list[int]:
    """Indices of the lookups the calt feature applies directly, in order."""
    indices: list[int] = []
    for record in gsub.FeatureList.FeatureRecord:
        if record.FeatureTag == "calt":
            indices += [i for i in record.Feature.LookupListIndex if i not in indices]
    return indices


def reachable_lookups(gsub) -> list[int]:
    """calt's lookups plus every lookup its contextual rules apply, sorted."""
    lookups = gsub.LookupList.Lookup
    pending = calt_lookup_indices(gsub)
    seen: set[int] = set()
    while pending:
        index = pending.pop()
        if index in seen:
            continue
        seen.add(index)
        for subtable in subtables(lookups[index]):
            for records in rule_records(subtable):
                pending.extend(record.LookupListIndex for record in records)
    return sorted(seen)


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


def calt_outputs(font: TTFont) -> set[str]:
    """Glyphs produced by the default calt feature."""
    gsub = font["GSUB"].table
    outputs: set[str] = set()
    for index in reachable_lookups(gsub):
        for subtable in subtables(gsub.LookupList.Lookup[index]):
            if hasattr(subtable, "mapping"):  # single or multiple substitution
                for target in subtable.mapping.values():
                    outputs.update([target] if isinstance(target, str) else target)
            elif hasattr(subtable, "ligatures"):
                outputs.update(lig.LigGlyph for ligs in subtable.ligatures.values() for lig in ligs)
            elif hasattr(subtable, "alternates"):
                outputs.update(g for alts in subtable.alternates.values() for g in alts)
    return outputs
