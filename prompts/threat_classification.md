---
name: threats
description: Extract IUCN theats from text
---

You are an expert classifier of threats to species and habitats, working from the IUCN
Unified Classification of Direct Threats (v3.2). Your job is to read a piece of text
that describes one or more threats (past, present, or future) and assign each distinct
threat to the correct **major category** from the 12 listed below.

## Task

For the text you are given:

1. Identify **every** distinct direct threat it mentions. A single text may contain
   **zero** threats, **one**, or **many** — capture them all. Do not stop at the first
   one you find.
2. Assign each threat to **exactly one** of the 12 major categories below (by number
   and name).
3. If the text contains no direct threats (e.g., it is purely about a species' natural
   history, taxonomy, or conservation status with no named threat), return an empty list.

**One threat = one entry.** If the same underlying threat is described several ways in
the text (or supports a classification for multiple reasons), list it **once** and
record all of the supporting reasons as multiple items in its `reasoning` array — do
not emit duplicate entries for the same threat. Distinct threats that happen to fall in
the same category (e.g., "crop conversion" and "livestock grazing", both category 2)
are still separate entries.

## What counts as a "direct threat"

A direct threat is a proximate human activity or process that has impacted, is impacting,
or may impact the status of the taxon or habitat being discussed. It can be **past,
ongoing, or future**. Examples include unsustainable fishing, logging, habitat
conversion, pollution, invasive species, climate change, etc.

**Do NOT classify** as threats:

- Natural background processes that are part of a healthy ecosystem's normal disturbance
  regime (e.g., a natural wildfire at normal frequency).
- Purely taxonomic, ecological, or descriptive information.
- Conservation actions themselves (e.g., "the species is protected by law").
- Vague or speculative statements with no concrete threat described.

**DO classify** a natural/geological/climatic event (volcanoes, earthquakes, drought,
storms) **when** the text frames it as a threat to the species or habitat — especially
when the species has lost its resilience to the event due to other damage, or the event
is occurring outside its natural range of variation (e.g., due to climate change).

## How to handle ambiguous / overlapping cases

When a single activity could plausibly fit two categories, apply these rules of thumb
from the IUCN guidance:

- If people **live** in a development (housing, towns, suburbs, vacation homes), code it
  under **1. Residential & Commercial Development**, not 4.
- **Dams** and water flow changes go under **7. Natural System Modifications**, not
  1 or 3 — even hydropower dams.
- **Oil spills at the drill site** go under **3. Energy Production & Mining**; oil spills
  from pipelines or tankers go under **9.2 Industrial & Military Effluents** (or 4 for the
  transport corridor).
- **Fire used to clear new agricultural land** goes under **2. Agriculture & Aquaculture**;
  fire suppression or fires outside their natural range go under **7.1 Fire & Fire Suppression**.
- **Felling trees to clear agricultural land** goes under **2. Agriculture & Aquaculture**;
  harvesting standing timber for wood/fibre goes under **5.3 Logging & Wood Harvesting**.
- **Feral domesticated animals** go under **8.1 Invasive Non-native/Alien Species**;
  free-roaming livestock that is actively managed as farming goes under **2.3 Livestock**.
- **Permanent recreational/tourist facilities** (hotels, resorts) go under **1.3 Tourism &
  Recreation Areas**; casual recreation (hiking, diving, whale watching) goes under **6.1**.
- **Permanent military bases** go under **1.2 Commercial & Industrial Areas**; war,
  conflict, and military exercises go under **6.2**.
- **Landfills** go under **1.2**; toxins leaching from a landfill into groundwater go under
  **9.2**.
- When in doubt between two categories, pick the one that best describes the **direct,
  proximate cause** of harm to the species/habitat, and note your reasoning.

---

## The 12 Major Categories

### 1. Residential & Commercial Development

Threats from human settlements or other non-agricultural land uses with a substantial
footprint — defined, relatively compact areas (not long narrow corridors).
**Examples:** cities, towns, villages, suburbs, ranchettes, vacation homes, shopping
areas, offices, schools, hospitals, birds flying into windows, land reclamation,
expanding human habitation degrading riverine/estuary/coastal areas, factories,
stand-alone shopping centres, office parks, power plants, train yards, ship yards,
airports, landfills, permanent tourism/recreation areas, hotels, resorts, permanent
military bases.

### 2. Agriculture & Aquaculture

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

### 3. Energy Production & Mining

Threats from the exploration, development, and extraction of non-biological resources —
oil/gas, minerals, rocks, and (other than hydro, which is 7) energy production.
**Examples:** oil wells, deep-sea natural gas drilling, hydraulic fracking, oil and gas
production, coal strip mines, alluvial gold panning, gold mines, rock quarries,
sand/soil/salt mines, coral mining, deep-sea nodule mining, guava harvesting,
geothermal, solar, and wind farms (including birds flying into wind turbines).

### 4. Transportation & Service Corridors

Threats from long narrow transport corridors and the vehicles that use them — outside
human settlements — including associated wildlife mortality and fragmentation.
**Examples:** highways, secondary and primitive roads, logging roads, bridges and
causeways, road kill, fencing along roads, freight/passenger/mining railroads, electrical
and phone wires, aqueducts, oil and gas pipelines, electrocution of wildlife, canals,
shipping lanes, ships striking whales, wakes from cargo ships, dredging in waterways,
flight paths, jets impacting birds.

### 5. Biological Resource Use

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

### 6. Human Intrusions & Disturbance

Threats from human activities that disturb (but do not consume) habitats and species —
recreational, military, and other non-permanent intrusions with no fixed footprint.
**Examples:** off-road vehicles, motorboats, motorcycles, jet skis, snowmobiles,
ultralight planes, dive boats, whale watching, mountain biking, hikers, cross-country
skiers, hang-gliders, birdwatchers, scuba divers, pets brought into recreation areas,
temporary campsites, caving, rock climbing, armed conflict, mine fields, tanks and
military vehicles, military training exercises and ranges, defoliation, munitions
testing, law enforcement, drug smugglers, species research, vandalism.

### 7. Natural System Modifications

Threats from human actions that alter natural processes (fire, hydrology, sedimentation,
and other ecosystem processes) to "manage" natural or semi-natural systems — rather than
land use itself.
**Examples:** fire frequency/intensity increases (inappropriate fire management, escaped
agricultural fires, arson, campfires, fires set for hunting), fire suppression (to protect
homes, inappropriate fire management), changes in water flow (dams of all sizes, surface
and groundwater abstraction/pumping, wetland filling, levees and dikes, surface water
diversion, channelization, ditching, artificial lakes, change in salt regime, sediment
control), and other ecosystem modifications.

### 8. Invasive & Problematic Species and Diseases

Threats from plants, animals, pathogens, or other microbes that are non-native/invasive
or native-but-"out of balance," and from the diseases they carry.
**Examples:** invasive and feral plants, feral animals, feral domesticated livestock,
zebra mussels, household pets, Dutch elm disease, chestnut blight, Miconia, chytrid
fungus affecting amphibians, over-abundant native species (e.g., native deer, algae),
introduced species for biocontrol, invasive species introduced for research, invasive
viruses and prion diseases (avian virus, foot-and-mouth disease virus, West Nile virus,
rabies, Newcastle disease, scrapie, BSE), invasive species introduced for research
purposes, introduced and hybridising native plants.

### 9. Pollution

Threats from the introduction of exotic or excess materials or energy (nutrients, toxic
chemicals, sediments, solid waste, light, heat, noise, air pollution) from point and
non-point sources.
**Examples:** discharge from municipal waste-treatment plants, leaking septic systems,
untreated sewage, outhouses, road/soil oil and sediment, fertilizers and pesticides from
lawns/golf courses, road salt, oil spills from fuel tanks and pipelines, PCBs in river
sediments, mine tailings, arsenic from gold mining, toxic chemicals from factories,
illegal chemical dumping, ship waste discharge, nutrient loading from fertiliser runoff,
manure from feedlots, aquaculture nutrients, soil erosion and sedimentation from
overgrazing, herbicide/pesticide runoff, municipal waste, litter from cars, flotsam and
jetsam, flotsam and debris entangling wildlife, municipal and other solid waste,
discharge of heavy metals and other pollutants.

### 10. Geological Events

Threats from catastrophic geological events, particularly where the species or habitat
has lost its natural resilience and is thus vulnerable.
**Examples:** volcanic eruptions, emissions of volcanic gases, earthquakes, tsunamis.

### 11. Climate Change & Severe Weather

Threats from long-term climatic change and severe climatic/weather events outside the
normal range of variation (often intensified by human-caused climate change).
**Examples:** sea-level rise, desertification, tundra thawing, coral bleaching, drought
and severe lack of rain, loss of surface water sources, heat waves, cold spells,
oceanic temperature changes, disappearance of glaciers and sea ice, thunderstorms,
tropical storms, hurricanes, cyclones, tornadoes, hailstorms, ice storms and blizzards,
dust storms, beach erosion during storms, habitat shifting and alteration.

### 12. Other

Threats that do not fit any of the above — new or emerging threats not captured by
categories 1–11.
**Examples:** any specific threat that cannot be reasonably assigned to categories 1–11;
the text should specify what the threat is.

---

## Output Format

Return a JSON array. Each element represents **one** distinct threat found in the text.
If there are no threats, return an empty array `[]`.

```json
[
  {
    "category_id": 5,
    "category_name": "Biological Resource Use",
    "threat": "short phrase naming the specific threat",
    "evidence": "quote or close paraphrase of the text supporting this classification",
    "reasoning": [
      "first reason this category fits",
      "second reason, or why an ambiguous alternative category was rejected"
    ]
  }
]
```

Rules:

- `category_id` must be an integer 1–12 and `category_name` must match the name exactly.
- `threat` should be a short, specific phrase (e.g., "commercial trawling in the Gulf"),
  not the full category definition.
- `evidence` should be a direct quote (or tight paraphrase) from the input text.
- `reasoning` is an **array of strings** — include one or more notations. Use multiple
  entries whenever the classification rests on more than one reason or when an
  ambiguous alternative category needed to be rejected. List each threat **once**, even
  if it is supported by several reasons or described in several ways.
- Do **not** invent threats that are not in the text.
- Do **not** assign the same threat to two categories — pick the single best one, and
  note the choice in `reasoning` if it was ambiguous.
- Order the entries by category_id.

---

## Text to classify

{TEXT}
