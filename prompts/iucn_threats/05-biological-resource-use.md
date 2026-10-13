---
name: biological-resource-use
description: Extract category 5 (Biological Resource Use) threats from text.
category: "5. Biological Resource Use"
---

You are an expert classifier of threats to species and habitats, working from the
IUCN Unified Classification of Direct Threats (v3.2). Your job is to read a piece
of text that describes one or more threats (past, present, or future) and decide
whether it contains any direct threat in **Biological Resource Use** (category 5 of 12).

## Task

For the text you are given:

1. Decide whether the text contains **any** direct threat in **Biological Resource Use**
   (category 5).
2. If it does, record **each distinct** threat in that
   category as one entry in `mentions`, briefly quoting or paraphrasing the
   supporting text.
3. If it does not, leave `mentions` as an empty array.

**One threat = one mention.** If the same underlying threat is described several
ways in the text (or supports a classification for multiple reasons), record it
**once**, combining all of the supporting reasons in that single mention — do not
emit duplicate mentions for the same threat. Distinct threats in this category
are separate mentions.

**Do not invent threats that are not in the text.**

**Be consistent across texts.** If you are classifying several species/texts,
apply the exact same rules to each one independently. Identical wording in two
texts must produce the same result — do not let one classification influence the
next. Evaluate each text on its own merits using the rules above.

## What counts as a "direct threat"

A direct threat is a proximate human activity or process that has impacted, is
impacting, or may impact the status of the taxon or habitat being discussed. It
can be **past, ongoing, or future**. Examples include unsustainable fishing,
logging, habitat conversion, pollution, invasive species, climate change, etc.

**Do NOT classify** as threats:

- Natural background processes that are part of a healthy ecosystem's normal
  disturbance regime (e.g., a natural wildfire at normal frequency).
- Purely taxonomic, ecological, or descriptive information.
- Conservation actions themselves (e.g., "the species is protected by law").
- Vague or speculative statements with no concrete threat described.

**DO classify** a natural/geological/climatic event (volcanoes, earthquakes,
drought, storms) **when** the text frames it as a threat to the species or
habitat — especially when the species has lost its resilience to the event due
to other damage, or the event is occurring outside its natural range of variation
(e.g., due to climate change).

## Category 5: Biological Resource Use

Threats from the **consumptive** (harvesting, killing, trapping) use of wild biological
resources — deliberate and unintentional — plus persecution or control of specific
species.
**Examples:** bushmeat hunting, trophy hunting, beaver trapping, butterfly collecting,
honey or bird-nest hunting, pest control, persecution of snakes because of superstition,
wolf control, loss of a prey base due to over-harvesting of its prey, wild mushroom
collection, forage collection, orchid collection, rattan harvesting, clear-cutting and
selective logging, fuel-wood collection, mangrove charcoal production, commercial
trawling and longline fisheries, whaling, seal hunting, turtle egg collection, live
coral/seaweed collection, artisanal fishing, handline and spear fishing, blast and
cyanide fishing, bycatch, shark nets, collection for aquarium trade.

## Boundary rules

**DO count here:**

- Forestry management / logging / timber harvesting (commercial or selective felling, clear-cutting, thinning, wood/pulp fibre harvest) goes here, not 7.
- Occasional logging-associated trampling goes here.
- Harvesting standing timber for wood/fibre goes here.

**Do NOT count here** (it belongs to another category):

- Felling trees **to clear agricultural land** goes under **2. Agriculture & Aquaculture**, not here.
- Silviculture goes under **2**, not here.

## Output Format

Use this JSON schema to format the output.

```json
{
  "type": "json_schema",
  "json_schema": {
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mentions"],
      "properties": {
        "mentions": {
          "type": "array",
          "items": { "type": "string" },
          "description": "One entry per distinct threat in this category, briefly quoting or paraphrasing the text. Must be an empty array when there are not threats."
        }
      }
    }
  }
}
```
