"""The GSUB stage: transplant a Ligature source's calt feature into an Output font.

The FontForge stage has already copied the glyphs calt produces (ADR 0002).
This stage replaces the Output font's own calt with the Ligature source's
lookups (ADR 0003), renaming glyphs as it goes: encoded glyphs by code point,
copied glyphs by the name map. References to glyphs the Output font lacks are
pruned, which is safe because such glyphs can never appear in shaped text.
"""

import copy
from pathlib import Path

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot

from ligaturizer.calt import calt_lookup_indices, calt_outputs, reachable_lookups, subtables


def plan_glyphs(source: TTFont, namespace: str = "") -> dict[str, str]:
    """Glyphs to copy from the Ligature source: {source name: Output font name}.

    These are the unencoded glyphs calt produces: Fixed ligatures, Pieces,
    Spacers and contextual alternates. Encoded ones map to the Input font's own.
    """
    encoded = set(source.getBestCmap().values())
    return {g: namespace + g for g in sorted(calt_outputs(source)) if g not in encoded}


def transplant_calt(output_file: Path, source_file: Path, copied: dict[str, str]) -> set[str]:
    """Replace the Output font's calt with the Ligature source's, in place.

    Returns the characters the Ligature source's rules mention that the Output
    font lacks; references to them were dropped.
    """
    source = TTFont(source_file)
    output = TTFont(output_file)
    renamer = _Renamer(source, output, copied)

    if "GSUB" not in output:
        output["GSUB"] = _empty_gsub()
    gsub = output["GSUB"].table
    source_gsub = source["GSUB"].table

    reach = reachable_lookups(source_gsub)
    new_index = {old: len(gsub.LookupList.Lookup) + i for i, old in enumerate(reach)}
    for old in reach:
        gsub.LookupList.Lookup.append(
            _convert_lookup(source_gsub.LookupList.Lookup[old], renamer, new_index)
        )
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

    _replace_calt_feature(gsub, [new_index[i] for i in calt_lookup_indices(source_gsub)])

    output.save(output_file)
    return renamer.missing


class _Renamer:
    def __init__(self, source: TTFont, output: TTFont, copied: dict[str, str]):
        self.copied = copied
        self.output = output
        self.output_glyph = output.getBestCmap()
        self.source_codepoint = {}
        for codepoint, name in sorted(source.getBestCmap().items()):
            self.source_codepoint.setdefault(name, codepoint)
        self.missing: set[str] = set()

    def __call__(self, name: str) -> str | None:
        """The Output font's name for a Ligature source glyph, or None if it has none."""
        if name in self.copied:
            return self.copied[name]
        codepoint = self.source_codepoint.get(name)
        if codepoint is None:
            return None  # unencoded, and calt never produces it
        if codepoint not in self.output_glyph:
            self.missing.add(chr(codepoint))
            return None
        return self.output_glyph[codepoint]

    def all(self, names) -> list[str] | None:
        """Rename every glyph in a sequence, or None if any is missing."""
        renamed = [self(n) for n in names]
        return None if None in renamed else renamed

    def coverage(self, names) -> ot.Coverage | None:
        """A coverage of the renamed glyphs that exist, or None if none do."""
        glyphs = {n for n in map(self, names) if n is not None}
        if not glyphs:
            return None
        coverage = ot.Coverage()
        coverage.glyphs = sorted(glyphs, key=self.output.getGlyphID)
        return coverage


def _convert_lookup(lookup, rename: _Renamer, new_index: dict[int, int]):
    converted = ot.Lookup()
    converted.LookupType = lookup.LookupType if lookup.LookupType != 7 else None
    converted.LookupFlag = lookup.LookupFlag
    converted.SubTable = []
    for subtable in subtables(lookup):
        converted.LookupType = subtable.LookupType
        converted.SubTable += _convert_subtable(subtable, rename, new_index)
    if converted.LookupType is None:
        converted.LookupType = lookup.LookupType
    converted.SubTableCount = len(converted.SubTable)
    return converted


def _convert_subtable(subtable, rename: _Renamer, new_index: dict[int, int]) -> list:
    match subtable:
        case ot.SingleSubst():
            mapping = {}
            for source, target in subtable.mapping.items():
                source, target = rename(source), rename(target)
                if source is not None and target is not None:
                    mapping[source] = target
            return [_with(ot.SingleSubst(), mapping=mapping)] if mapping else []
        case ot.MultipleSubst():
            mapping = {}
            for source, targets in subtable.mapping.items():
                source, targets = rename(source), rename.all(targets)
                if source is not None and targets is not None:
                    mapping[source] = targets
            return [_with(ot.MultipleSubst(), mapping=mapping)] if mapping else []
        case ot.ChainContextSubst(Format=3):
            converted = _chain_rule(
                rename,
                new_index,
                [c.glyphs for c in subtable.BacktrackCoverage],
                [c.glyphs for c in subtable.InputCoverage],
                [c.glyphs for c in subtable.LookAheadCoverage],
                subtable.SubstLookupRecord,
            )
            return [converted] if converted else []
        case ot.ChainContextSubst(Format=1):
            # One format 3 subtable per rule, in order: same behavior, and the
            # coverage no longer has to stay aligned with the rule sets.
            converted = []
            for first, rule_set in zip(
                subtable.Coverage.glyphs, subtable.ChainSubRuleSet, strict=True
            ):
                for rule in rule_set.ChainSubRule if rule_set else []:
                    one = _chain_rule(
                        rename,
                        new_index,
                        [[g] for g in rule.Backtrack],
                        [[first]] + [[g] for g in rule.Input],
                        [[g] for g in rule.LookAhead],
                        rule.SubstLookupRecord,
                    )
                    if one:
                        converted.append(one)
            return converted
    raise NotImplementedError(
        f"calt uses an unsupported subtable: {type(subtable).__name__}"
        f" format {getattr(subtable, 'Format', '?')}"
    )


def _chain_rule(rename, new_index, backtrack, inputs, lookahead, records):
    """A format 3 chaining rule, or None if some position can no longer match."""
    coverages = [
        [rename.coverage(glyphs) for glyphs in part] for part in (backtrack, inputs, lookahead)
    ]
    if any(c is None for part in coverages for c in part):
        return None
    rule = ot.ChainContextSubst()
    rule.Format = 3
    rule.BacktrackCoverage, rule.InputCoverage, rule.LookAheadCoverage = coverages
    rule.SubstLookupRecord = []
    for record in records:
        copied = ot.SubstLookupRecord()
        copied.SequenceIndex = record.SequenceIndex
        copied.LookupListIndex = new_index[record.LookupListIndex]
        rule.SubstLookupRecord.append(copied)
    return rule


def _with(subtable, **attributes):
    for name, value in attributes.items():
        setattr(subtable, name, value)
    return subtable


def _replace_calt_feature(gsub, lookup_indices: list[int]) -> None:
    """Point calt at `lookup_indices` in every script and language system."""
    records = gsub.FeatureList.FeatureRecord
    calt_features = [i for i, r in enumerate(records) if r.FeatureTag == "calt"]
    for i in calt_features:
        records[i].Feature.LookupListIndex = list(lookup_indices)
        records[i].Feature.LookupCount = len(lookup_indices)

    # Text in a script the font doesn't list (often Latin) is shaped with DFLT.
    # Without one, HarfBuzz falls back to dflt, then latn, so the new DFLT
    # starts from that script's features to keep them applying.
    scripts = gsub.ScriptList.ScriptRecord
    if not any(s.ScriptTag == "DFLT" for s in scripts):
        fallback = next(
            (
                s.Script.DefaultLangSys
                for tag in ("dflt", "latn")
                for s in scripts
                if s.ScriptTag == tag and s.Script.DefaultLangSys is not None
            ),
            None,
        )
        script = ot.ScriptRecord()
        script.ScriptTag = "DFLT"
        script.Script = ot.Script()
        script.Script.DefaultLangSys = copy.deepcopy(fallback) if fallback else _lang_sys()
        script.Script.LangSysRecord = []
        scripts.insert(0, script)  # uppercase, so it sorts before every other tag
        gsub.ScriptList.ScriptCount = len(scripts)

    shared = None  # a calt feature for language systems that have none
    for script in gsub.ScriptList.ScriptRecord:
        lang_systems = [r.LangSys for r in script.Script.LangSysRecord]
        if script.Script.DefaultLangSys is not None:
            lang_systems.append(script.Script.DefaultLangSys)
        for lang_sys in lang_systems:
            if not set(lang_sys.FeatureIndex) & set(calt_features):
                if shared is None:
                    shared = _add_feature(gsub, "calt", lookup_indices)
                lang_sys.FeatureIndex.append(shared)
                lang_sys.FeatureCount = len(lang_sys.FeatureIndex)
    _sort_features(gsub)


def _lang_sys() -> ot.LangSys:
    lang_sys = ot.LangSys()
    lang_sys.LookupOrder = None
    lang_sys.ReqFeatureIndex = 0xFFFF
    lang_sys.FeatureIndex = []
    lang_sys.FeatureCount = 0
    return lang_sys


def _add_feature(gsub, tag: str, lookup_indices: list[int]) -> int:
    record = ot.FeatureRecord()
    record.FeatureTag = tag
    record.Feature = ot.Feature()
    record.Feature.FeatureParams = None
    record.Feature.LookupListIndex = list(lookup_indices)
    record.Feature.LookupCount = len(lookup_indices)
    gsub.FeatureList.FeatureRecord.append(record)
    gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
    return len(gsub.FeatureList.FeatureRecord) - 1


def _sort_features(gsub) -> None:
    """Keep FeatureRecords sorted by tag, as the spec requires, remapping indices."""
    records = gsub.FeatureList.FeatureRecord
    order = sorted(range(len(records)), key=lambda i: records[i].FeatureTag)
    remap = {old: new for new, old in enumerate(order)}
    gsub.FeatureList.FeatureRecord = [records[i] for i in order]
    for script in gsub.ScriptList.ScriptRecord:
        lang_systems = [r.LangSys for r in script.Script.LangSysRecord]
        if script.Script.DefaultLangSys is not None:
            lang_systems.append(script.Script.DefaultLangSys)
        for lang_sys in lang_systems:
            lang_sys.FeatureIndex = sorted(remap[i] for i in lang_sys.FeatureIndex)
            if lang_sys.ReqFeatureIndex != 0xFFFF:
                lang_sys.ReqFeatureIndex = remap[lang_sys.ReqFeatureIndex]


def _empty_gsub():
    table = newTable("GSUB")
    table.table = ot.GSUB()
    table.table.Version = 0x00010000
    table.table.ScriptList = ot.ScriptList()
    table.table.ScriptList.ScriptRecord = []
    table.table.FeatureList = ot.FeatureList()
    table.table.FeatureList.FeatureRecord = []
    table.table.LookupList = ot.LookupList()
    table.table.LookupList.Lookup = []
    return table
