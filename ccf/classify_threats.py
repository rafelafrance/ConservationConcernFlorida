#!/usr/bin/env python3
"""
IUCN Direct Threat classifier (v3.2, 12 major categories).

Applies data/threats/threat_classification_prompt.md to free-text descriptions of
threats and returns a list of threat entries. Each entry is:
    {category_id, category_name, threat, evidence, reasoning: [str, ...]}

This is a deterministic, keyword/lexicon-based classifier intended to reproduce the
behaviour of the LLM prompt for batch processing. It is a heuristic, not a guarantee
of correctness.
"""

from __future__ import annotations

import json
import re

# category_id -> (category_name, [keywords/patterns])
# Order matters for disambiguation; matched by regex search on lowercased text.
CATS = {
    1: (
        "Residential & Commercial Development",
        [
            r"develop",
            r"\burban\b",
            r"\bsubur",
            r"\btown",
            r"village",
            r"settlement",
            r"construction",
            r"build",
            r"residential",
            r"commercial (?:area|zone|development)",
            r"housing",
            r"land reclamation",
            r"shipp?ing lane",
            r"airport",
            r"landfill",
            r"resort",
            r"hotel",
            r"shopping",
            r"land-use conversion",
            r"habitat conversion",
            r"habitat loss",
            r"habitat destruction",
            r"habitat fragmentation",
            r"land use",
            r"land use altering",
            r"land-use",
            r"habitat removal",
            r"habitat alteration",
            r"loss of (?:savanna|pineland|wet|habitat|forest)",
            r"habitat loss",
        ],
    ),
    2: (
        "Agriculture & Aquaculture",
        [
            r"agricult",
            r"crop",
            r"plantat",
            r"orchard",
            r"ranch",
            r"pasture",
            r"farm",
            r"grazing",
            r"graze",
            r"livestock",
            r"cattle",
            r"sheep",
            r"goat",
            r"horse",
            r"stock",
            r"aquaculture",
            r"fish farm",
            r"shrimp",
            r"rangeland",
            r"irrigat",
            r"crop conversion",
        ],
    ),
    3: (
        "Energy Production & Mining",
        [
            r"oil",
            r"gas (?:drill|well|production)",
            r"frack",
            r"mining",
            r"mine",
            r"quarry",
            r"petroleum",
            r"coal",
            r"solar farm",
            r"wind farm",
            r"geothermal",
            r"nuclear",
        ],
    ),
    4: (
        "Transportation & Service Corridors",
        [
            r"\broad\b",
            r"highway",
            r"roadkill",
            r"road kill",
            r"railroad",
            r"railway",
            r"pipeline",
            r"aqueduct",
            r"utility line",
            r"power line",
            r"transit",
            r"transport corridor",
            r"flight path",
            r"shipping lane",
            r"canal",
            r"bridge",
            r"causeway",
        ],
    ),
    5: (
        "Biological Resource Use",
        [
            r"logging",
            r"wood harvest",
            r"\bharvest\b",
            r"harvesting",
            r"trapp",
            r"hunt",
            r"poach",
            r"fishery",
            r"fishing",
            r"bycatch",
            r"overgrazing",
            r"overfishing",
            r"overharvest",
            r"over-harvest",
            r"seaweed collect",
            r"shellfish collect",
            r"coral collect",
            r"\bcollect\b",
            r"collecting",
            r"collector",
            r"overcollect",
            r"collection",
            r"persecut",
            r"pest control",
            r"woodland management",
            r"forest management",
            r"forestry",
            r"increased demand",
            r"commercial demand",
        ],
    ),
    6: (
        "Human Intrusions & Disturbance",
        [
            r"trampling",
            r"trample",
            r"off-road vehicle",
            r"motorboat",
            r"jet ski",
            r"snowmobile",
            r"whale watch",
            r"birdwatch",
            r"scuba",
            r"recreation",
            r"tourism",
            r"visitor",
            r"human intrusion",
            r"disturbance",
            r"vandalism",
            r"military",
            r"armed conflict",
            r"\bhiker",
            r"\bhiking\b",
            r"off-trail",
            r"rock-?climb",
            r"\bvehicle",
            r"human activity",
            r"human presence",
            r"\bweeds?\b",
            r"\bpigs?\b",
            r"\bgoats?\b",
            r"\bdeer\b",
            r"trail maintenance",
            r"trail\b",
            r"proximity",
            r"foot traffic",
            r"dirt bike",
            r"\batv\b",
            r"all-?terrain vehicle",
            r"boulder hop",
            r"\borv\b",
            r"off-road (?:vehicle|vehicle)",
            r"navy activities",
            r"human activities",
            r"human use",
            r"human related activities",
            r"anthropogenic",
        ],
    ),
    7: (
        "Natural System Modifications",
        [
            r"\bfire\b",
            r"fire suppression",
            r"fire management",
            r"burning",
            r"wildfire",
            r"fuel reduction",
            r"prescribed fire",
            r"hydrolog",
            r"\bdam\b",
            r"dam construction",
            r"levee",
            r"dike",
            r"diversion",
            r"channelization",
            r"ditching",
            r"water flow",
            r"sedimentation",
            r"salinity",
            r"groundwater",
            r"water table",
            r"drainage",
            r"\bsuccession\b",
            r"successional",
            r"water project",
            r"water management",
            r"brush control",
            r"dredging",
            r"\bclearing\b",
            r"reforestation",
        ],
    ),
    8: (
        "Invasive & Problematic Species and Diseases",
        [
            r"invasive",
            r"non-native",
            r"nonnative",
            r"alien (?:species|plant|animal|vegetation|weed|species)",
            r"\balien\b",
            r"exotic",
            r"feral",
            r"introduced (?:species|plant|animal|weed|plant)",
            r"\bintroduced\b",
            r"\bhybrid",
            r"out-of-balance",
            r"problematic",
            r"chytrid",
            r"disease",
            r"pathogen",
            r"miconia",
            r"zebra mussel",
            r"knapweed",
            r"bromus",
            r"euphorbia",
            r"\bweed\b",
            r"overshading",
            r"\bschinus\b",
            r"chestnut blight",
            r"\brats?\b",
            r"\bungulate",
            r"garlic mustard",
            r"ash borer",
        ],
    ),
    9: (
        "Pollution",
        [
            r"pollut",
            r"sewage",
            r"wastewater",
            r"effluent",
            r"runoff",
            r"run-off",
            r"nutrient",
            r"eutroph",
            r"toxic",
            r"chemical",
            r"herbicide",
            r"pesticide",
            r"fertilizer",
            r"heavy metal",
            r"oil spill",
            r"garbage",
            r"waste",
            r"litter",
            r"debris",
            r"contaminat",
        ],
    ),
    10: (
        "Geological Events",
        [
            r"volcan",
            r"earthquake",
            r"tsunami",
            r"seismic",
            r"geological",
            r"shifting sand",
            r"sand drift",
            r"erosion",
        ],
    ),
    11: (
        "Climate Change & Severe Weather",
        [
            r"climate change",
            r"global warming",
            r"sea-level rise",
            r"sea level rise",
            r"desertif",
            r"tundra thaw",
            r"coral bleach",
            r"drought",
            r"heat wave",
            r"cold spell",
            r"temperature",
            r"glacier",
            r"sea ice",
            r"tropical storm",
            r"hurricane",
            r"cyclone",
            r"tornado",
            r"hailstorm",
            r"ice storm",
            r"blizzard",
            r"dust storm",
            r"flooding",
            r"flood",
            r"storm",
            r"weather",
        ],
    ),
    12: ("Other", []),  # fallback only
}

# Specific phrases that indicate the text is NOT describing threats
NON_THREAT_RE = re.compile(
    r"threats?\s+(?:are\s+|is\s+)?(?:unknown|none|not\s+(?:known|identified|present))|"
    r"no\s+threats?",
    re.I,
)


def _find_threat_clauses(text: str):
    """Split text into clauses and return [(clause, matched_category_ids)]
    for clauses that contain at least one threat keyword.

    Clauses split on sentence boundaries and commas, BUT a "threat lead-in"
    phrase ("threats include", "threatened by", "threat from/of/to", "threats to")
    keeps the rest of the sentence together as a single unit so that comma lists
    of threats are classified as one threat rather than split fragments.
    """
    text = text.lower()
    lead_in = re.compile(
        r"threats? (?:include|comprise|consist of|from|of|to|impacts? are?|impacts?)"
        r"|threatened by|threat from|threat of|threats? to"
    )

    # First, grab any lead-in span and keep the whole sentence as one clause.
    lead_sentences = []
    for m in lead_in.finditer(text):
        s_start = max(text.rfind(c, 0, m.start()) for c in ".!?;")
        s_start = s_start + 1 if s_start != -1 else 0
        ends = [text.find(c, m.end()) for c in ".!?" if text.find(c, m.end()) != -1]
        s_end = min(ends) if ends else len(text)
        lead_sentences.append(text[s_start:s_end].strip())

    # Also split the rest of the text into normal clauses (sentence + comma split),
    # but skip fragments that fall inside an already-captured lead-in sentence
    # (they would just duplicate the whole-sentence clause).
    rest_clauses = re.split(r"[.!?;:]\s+|,(?=\s+)", text)
    clauses = list(lead_sentences)
    for clause in rest_clauses:
        clause = clause.strip()
        if not clause:
            continue
        if any(clause in ls for ls in lead_sentences):
            continue  # sub-clause of a lead-in sentence; already captured
        clauses.append(clause)

    results = []
    seen = set()
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        matched = []
        for cid, (name, pats) in CATS.items():
            if cid == 12:
                continue
            for p in pats:
                if re.search(p, clause):
                    matched.append(cid)
                    break
        if matched:
            norm = clause.rstrip(".,;:")
            if norm not in seen:
                seen.add(norm)
                results.append((clause, matched))
    return results


def _pick_category(clause: str, matched: list[int]) -> int:
    """Disambiguate when a clause matches multiple categories."""
    if len(matched) == 1:
        return matched[0]
    c = set(matched)
    cl = clause.lower()
    # Rule: grazing / trampling by livestock -> 2 (agriculture), not 6 (intrusions)
    if (
        2 in c
        and 6 in c
        and re.search(r"graz|trample|cattle|horse|livestock|stock", cl)
    ):
        return 2
    # Rule: roadkill / transport -> 4
    if 4 in c and re.search(r"road|highway|transit|transport|pipeline|utility", cl):
        return 4
    # Rule: invasive species -> 8
    if 8 in c and re.search(
        r"invasive|non-native|nonnative|feral|exotic|introduced|hybridis", cl
    ):
        return 8
    # Rule: pollution -> 9
    if 9 in c and re.search(
        r"pollut|sewage|runoff|toxic|herbicide|pesticide|chemical|waste", cl
    ):
        return 9
    # Rule: fire / hydrology -> 7
    if 7 in c and re.search(
        r"\bfire\b|hydrolog|\bdam\b|levee|drainage|groundwater", cl
    ):
        return 7
    # Rule: climate -> 11
    if 11 in c and re.search(
        r"climate|drought|flood|hurricane|sea level|temperature|weather", cl
    ):
        return 11
    # Rule: development -> 1 (most common in habitat-loss text)
    if 1 in c and re.search(r"develop|urban|residential|construction|build", cl):
        return 1
    # Default: lowest category id
    return min(c)


def classify(text: str) -> list[dict]:
    """Classify a free-text description of threats.

    Returns a list of threat entries (may be empty).
    """
    if not text or not text.strip():
        return []
    text = text.strip()

    # If the text explicitly says threats are unknown/none, return empty
    if NON_THREAT_RE.search(text):
        return []

    clauses = _find_threat_clauses(text)

    # Category 12 fallback: if the text names a concrete threat cause
    # ("threats include X", "threatened by X", "threat from/of X") but none of
    # the 11 specific categories matched any clause, emit a single category-12
    # entry so the threat is not silently dropped.
    if not clauses:
        m = re.search(
            r"(threats? (?:include|comprise|consist of|from|of|to)|threatened by|threat from)\b\s*(.{1,120})",
            text,
            re.I,
        )
        if m and not re.search(
            r"\b(?:unknown|none|low|few|minimal|stable|secure|not (?:known|identified|documented|evaluated|well understood)|are low|is low|considered to be low|thought to be low|apparently secure|very secure)\b",
            m.group(2),
            re.I,
        ):
            cause = re.sub(r"\s+\(.*", "", m.group(2)).rstrip(".,;")
            # Only treat as a real cause if it's not just a pronoun / bare noun phrase
            # referring back to the species itself (e.g., "threats to this species").
            cause_core = re.sub(r"^(?:to|of|from|by)\s+", "", cause, flags=re.I).strip(
                " ,.;"
            )
            # Strip a leading species-reference so "threats to this species" does not
            # count as a specific cause. After stripping, what remains must be a real
            # noun phrase (>=2 words) to qualify.
            cause_core = re.sub(
                r"^(?:the\s+|this\s+|that\s+|its\s+|their\s+)?\s*"
                r"(?:species|taxon|plant|population|populations|it|them)\b[,.\s]*",
                "",
                cause_core,
                flags=re.I,
            ).strip(" ,.;")
            # Require at least a couple of meaningful words to call it a specific cause.
            if len(cause_core.split()) >= 2:
                return [
                    {
                        "category_id": 12,
                        "category_name": "Other",
                        "threat": cause_core,
                        "evidence": m.group(0).strip(),
                        "reasoning": [
                            "Text names a specific threat cause, but it does not match any of "
                            "the 11 specific IUCN categories, so it is recorded under category "
                            "12 (Other).",
                        ],
                    }
                ]
        return []

    entries = []
    seen = {}  # (category_id, normalized_threat) -> entry
    for clause, cats in clauses:
        cid = _pick_category(clause, cats)
        name = CATS[cid][0]
        # Normalize the threat phrase: strip leading connectors
        threat = re.sub(
            r"^(and|or|including|e\.g\.|such as|from|due to|by|with|in)\s+",
            "",
            clause.strip(),
        )
        threat = threat.rstrip(".,;")
        key = (cid, threat.lower())
        if key in seen:
            existing = seen[key]
            if len(existing["reasoning"]) < 3:  # cap
                existing["reasoning"].append(
                    "Also mentioned in a separate clause in the text."
                )
        else:
            reasoning = [f"Matched category {cid} ({name}) lexicon in the clause."]
            if len(cats) > 1:
                reasoning.append(
                    f"Clause also matched categories {sorted(set(cats) - {cid})}; "
                    f"{name} chosen as the most specific/proximate."
                )
            entry = {
                "category_id": cid,
                "category_name": name,
                "threat": threat,
                "evidence": clause.strip(),
                "reasoning": reasoning,
            }
            seen[key] = entry
            entries.append(entry)

    entries.sort(key=lambda e: e["category_id"])
    return entries


if __name__ == "__main__":
    tests = [
        "Paronychia baldwinii ssp. riparia is a perennial herb that is endemic to the "
        "southeastern United States. Threats and trends are unknown.",
        "Atriplex parishii occurs in Riverside County, California. Threats include "
        "development, agriculture conversion and grazing.",
        "Residential and transportation related development caused severe habitat loss "
        "and fragmentation. Lack of fire or dominance of nonnative invasive plant species "
        "could both extremely and negatively impact populations.",
        "The natural landscape of the type locale has been thoroughly altered by "
        "agricultural conversion and rangeland grazing practices, including a century of "
        "overgrazing: virtually no unaltered habitats were observed. Predominate threats "
        "are impacts from grazing and trampling by cattle and horses.",
        "Fewer than ten occurrences, which potentially face threats from development, "
        "road maintenance, logging, hydrological alteration, and invasive species.",
    ]
    for t in tests:
        print("=" * 70)
        print(t[:120])
        print(json.dumps(classify(t), indent=2))
