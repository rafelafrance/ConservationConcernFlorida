import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

FIELDS = [
    "Reasons",
    "Threat Comments",
    "Long-term Trend Comments",
    "Short-term Trend Comments",
]

# Input columns from args.in_csv
IN_COLUMNS = [
    "Scientific Name",
    "Order",
    "Family",
    "Genus",
    "NatureServe Unique Identifier",
    "Global Status",
    "Global Status (Rounded)",
    *FIELDS,
]

# Output columns to args.out_csv
OUT_COLUMNS = [
    "status",
    *IN_COLUMNS,
    "threat_status",
    "threat_categories",
    "threat_category_count",
    "threat_mentions",
    "threat_categories_revised",
    "threat_category_count_revised",
    "threat_mentions_revised",
    "threat_category_changed",
    "grazing_flag",
    "ORVs_flag",
    "trampling_flag",
    "trail_flag",
    "succession_flag",
    "erosion_flag",
    "fire_flag",
    "target",
]

BUFFER_COLUMNS = [
    "status",
    "Scientific Name",
    "category",
    "mentions",
]

CATEGORIES = [
    "1. Residential & Commercial Development",
    "2. Agriculture & Aquaculture",
    "3. Energy Production & Mining",
    "4. Transportation & Service Corridors",
    "5. Biological Resource Use",
    "6. Human Intrusions & Disturbance",
    "7. Natural System Modifications",
    "8. Invasive & Problematic Species and Diseases",
    "9. Pollution",
    "10. Geological Events",
    "11. Climate Change & Severe Weather",
    "12. Other",
]

FLAGS = {
    "accidentally set fire": "fire_flag",
    "accidentally set fires": "fire_flag",
    "all terrain vehicle": "ORVs_flag",
    "all terrain vehicles": "ORVs_flag",
    "all-terrain vehicle": "ORVs_flag",
    "all-terrain vehicles": "ORVs_flag",
    "atv use": "ORVs_flag",
    "atv": "ORVs_flag",
    "atvs": "ORVs_flag",
    "burro trampling": "trampling_flag",
    "cattle graze": "grazing_flag",
    "cattle grazing": "grazing_flag",
    "cattle trampling": "trampling_flag",
    "coastal erosion": "erosion_flag",
    "dune succession": "succession_flag",
    "erode": "erosion_flag",
    "eroded": "erosion_flag",
    "erosion bluffs": "erosion_flag",
    "erosion": "erosion_flag",
    "fire": "fire_flag",
    "fires": "fire_flag",
    "forest succession": "succession_flag",
    "graze": "grazing_flag",
    "grazed": "grazing_flag",
    "grazing pressure": "grazing_flag",
    "grazing": "grazing_flag",
    "grazing/trampling": "trampling_flag",
    "habitat succession": "succession_flag",
    "horse trampling": "trampling_flag",
    "human ignited fire": "fire_flag",
    "human ignited fires": "fire_flag",
    "human-ignited fires": "fire_flag",
    "lack of fire": "fire_flag",
    "livestock grazed": "grazing_flag",
    "livestock grazing": "grazing_flag",
    "mega fire": "fire_flag",
    "mega fires": "fire_flag",
    "mega-fire": "fire_flag",
    "mega-fires": "fire_flag",
    "megafire": "fire_flag",
    "megafires": "fire_flag",
    "motorized recreation": "ORVs_flag",
    "motorized trail": "trail_flag",
    "motorized trails": "trail_flag",
    "off highway vehicle use": "ORVs_flag",
    "off highway vehicle uses": "ORVs_flag",
    "off highway vehicle": "ORVs_flag",
    "off highway vehicles": "ORVs_flag",
    "off road buggies": "ORVs_flag",
    "off road recreational vehicle": "ORVs_flag",
    "off road recreational vehicles": "ORVs_flag",
    "off road vehicle": "ORVs_flag",
    "off road vehicles": "ORVs_flag",
    "off road vehicular use": "ORVs_flag",
    "off road vehicular uses": "ORVs_flag",
    "off road": "ORVs_flag",
    "off roading": "ORVs_flag",
    "off-highway vehicle use": "ORVs_flag",
    "off-highway vehicle uses": "ORVs_flag",
    "off-highway vehicle": "ORVs_flag",
    "off-highway vehicles": "ORVs_flag",
    "off-road buggies": "ORVs_flag",
    "off-road recreational vehicle": "ORVs_flag",
    "off-road recreational vehicles": "ORVs_flag",
    "off-road vehicle": "ORVs_flag",
    "off-road vehicles": "ORVs_flag",
    "off-road vehicular use": "ORVs_flag",
    "off-road vehicular uses": "ORVs_flag",
    "off-road": "ORVs_flag",
    "off-roading": "ORVs_flag",
    "orv": "ORVs_flag",
    "orvs": "ORVs_flag",
    "overgraze": "grazing_flag",
    "overgrazed": "grazing_flag",
    "overgrazing": "grazing_flag",
    "prescribed fire": "fire_flag",
    "prescribed fires": "fire_flag",
    "recreation vehicle": "ORVs_flag",
    "recreational vehicles": "ORVs_flag",
    "set fires": "fire_flag",
    "soil erosion": "erosion_flag",
    "succession": "succession_flag",
    "successive": "succession_flag",
    "trail": "trail_flag",
    "trails": "trail_flag",
    "trample": "trampling_flag",
    "trampled": "trampling_flag",
    "trampling": "trampling_flag",
    "trampling/grazing": "trampling_flag",
    "wildfire": "fire_flag",
    "wildfires": "fire_flag",
}

MENTION_RE = re.compile(
    r"^(\d+)\.\s*([^:]+?)\s*:\s*(.+)\s*$", flags=re.DOTALL | re.MULTILINE
)


@dataclass
class Prompt:
    name: str
    prompt: str
    json_schema: object


def load_prompt(prompt_path: Path) -> Prompt:
    text = prompt_path.read_text()
    front = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    name = re.search(r"^name:\s*(.+?)\s*$", front.group(1), flags=re.MULTILINE)
    name = name.group(1).strip().strip('"')
    body = re.sub(r"^---$.*^---$", "", text, flags=re.MULTILINE | re.DOTALL).strip()
    schema = re.search(r"```json(.+)```", body, flags=re.DOTALL)
    prompt = Prompt(name, body, json.loads(schema.group(1).strip()))
    return prompt


def set_flags(in_data: dict) -> None:
    targets = set(FLAGS.keys())
    for row in in_data:
        words = set(row["target"].lower().split())
        for flag in words & targets:
            row[FLAGS[flag]] = "1"
