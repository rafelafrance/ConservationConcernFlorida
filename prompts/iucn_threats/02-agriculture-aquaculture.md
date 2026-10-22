---
name: agriculture-aquaculture
description: Extract category 2 (Agriculture & Aquaculture) threats from text.
category: "2. Agriculture & Aquaculture"
---

You are an expert classifier of threats to species and habitats, working from the
IUCN Unified Classification of Direct Threats (v3.2). Your job is to read a piece
of text that describes one or more threats (past, present, or future) and decide
whether it contains any direct threat in **Agriculture & Aquaculture** (category 2 of 12).

## Task

For the text you are given:

1. Decide whether the text contains **any** direct threat in **Agriculture & Aquaculture**
   (category 2).
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

## Category 2: Agriculture & Aquaculture

Threats from the conversion of habitat to agriculture and the management of crops and
livestock — annual/perennial crops, plantations, livestock grazing and ranching, and
aquaculture.
**Examples:** wheat farms, sugar cane plantations, rice paddies, hillside rice
production, household swidden/shift plots, banana or pineapple plantations, mango or
apple orchards, olive or date groves, vineyards, oil palm plantations, tea or coffee
plantations, mixed agroforestry systems, coca plantations, shifting agriculture,
smallholder and agro-industry farming, teak/eucalyptus/loblolly pine plantations,
Christmas tree farms, wood and pulp plantations, cattle feed lots, chicken farms, dairy
farms, cattle ranching, goat/camel/yak herding, nomadic and smallholder/agro-industry
grazing, shrimp or fin-fish aquaculture, fish ponds, hatchery fish, seeded shellfish
beds, artificial algal beds, mangrove destruction for aquaculture.

## Boundary rules

**DO count here:**

- Felling trees **to clear agricultural land** goes here.
- Fire **used to clear new agricultural land** goes here.
- Silviculture goes here (not 5).
- Plantations go here.
- Livestock and grazing ranching go here (not 12).
- Free-roaming livestock that is actively managed as farming goes here.

**Do NOT count here** (it belongs to another category):

- Grazing or browsing by **wild (non-farmed) animals** — deer, elk, moose, ravens, gulls, rabbits, rodents — goes under **8. Invasive & Problematic Species and Diseases**, not here.
- Herbivory by wild animals goes under **8**, not here.
- Harvesting standing timber for wood/fibre goes under **5. Biological Resource Use** (that is logging, not clearing for crops).
- Herbicides and agricultural run-off go under **9. Pollution**, not here.
- Wildfires — fire as a threat, not deliberate land clearing — go under **11. Climate Change & Severe Weather**.

## Output Format

Use this JSON schema to format the output.

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "category_02",
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mentions"],
      "properties": {
        "mentions": {
          "type": "array",
          "items": { "type": "string" },
          "description": "One entry per distinct threat in this category, briefly quoting or paraphrasing the text."
        }
      }
    }
  }
}
```
