import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

from ccf.pylib import pipeline
from ccf.pylib.dimension import Dimension
from ccf.pylib.str_util import clean
from ccf.rules.size import Size

PIPELINE = pipeline.build()

SHAPES = set()
FRUIT_TYPES = set()
DURATION = set()


def parse_treatment(record, treatment):
    used = set()

    for key, text in treatment.items():
        if funcs := PARSE.get(key):
            for func in funcs:
                if func not in used and func(key, text, record):
                    used.add(func)  # Only parse a trait once


def init_record(page):
    taxon = page.stem.replace("_", " ")
    taxon = taxon[0].upper() + taxon[1:]
    taxon = clean(taxon).replace("×", "x ")
    record = {"taxon": taxon}
    return record


def find_treatment(soup):
    treatment = soup.find("span", class_="statement")
    if not treatment:
        return {}

    text = str(treatment).replace("<i>", "").replace("</i>", "")
    text = re.sub(r"(Perennials|Annuals|Biennials);", r"<b>\1</b>", text)
    text = clean(text)

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    treatment = dict(zip(parts[0::2], parts[1::2], strict=True))
    return treatment


def has_value(dim):
    return any(getattr(dim, k) is not None for k in ("min", "low", "high", "max"))


def plant_height(_key, text, record):
    size = get_size_trait(text, "", "")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, ["length", "height"])

    record["plant_height_min_cm"] = length.min
    record["plant_height_low_cm"] = length.low
    record["plant_height_high_cm"] = length.high
    record["plant_height_max_cm"] = length.max

    return has_value(length)


def plant_deciduousness(key, text, record):
    record["deciduousness"] = vocab_hits(text, DURATION, key)
    return bool(record["deciduousness"])


def leaf_size(_key, text, record):
    size = get_size_trait(text, "leaf_size", "leaf")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")
    width = get_size_dim(size, "width")
    thickness = get_size_dim(size, "thickness")

    record["leaf_length_min_cm"] = length.min
    record["leaf_length_low_cm"] = length.low
    record["leaf_length_high_cm"] = length.high
    record["leaf_length_max_cm"] = length.max

    record["leaf_width_min_cm"] = width.min
    record["leaf_width_low_cm"] = width.low
    record["leaf_width_high_cm"] = width.high
    record["leaf_width_max_cm"] = width.max

    record["leaf_thickness_min_cm"] = thickness.min
    record["leaf_thickness_low_cm"] = thickness.low
    record["leaf_thickness_high_cm"] = thickness.high
    record["leaf_thickness_max_cm"] = thickness.max

    return has_value(length) or has_value(width) or has_value(thickness)


def leaf_shape(_key, text, record):
    record["leaf_shape"] = vocab_hits(text.lower(), SHAPES)
    return bool(record["leaf_shape"])


def seed_size(_key, text, record):
    size = get_size_trait(text, "seed_size", "seed")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")
    width = get_size_dim(size, "width")
    diameter = get_size_dim(size, "diameter")

    record["seed_length_min_cm"] = length.min
    record["seed_length_low_cm"] = length.low
    record["seed_length_high_cm"] = length.high
    record["seed_length_max_cm"] = length.max

    record["seed_width_min_cm"] = width.min
    record["seed_width_low_cm"] = width.low
    record["seed_width_high_cm"] = width.high
    record["seed_width_max_cm"] = width.max

    record["seed_diameter_min_cm"] = diameter.min
    record["seed_diameter_low_cm"] = diameter.low
    record["seed_diameter_high_cm"] = diameter.high
    record["seed_diameter_max_cm"] = diameter.max

    return has_value(length) or has_value(width)


def fruit_type(key, text, record):
    record["fruit_type"] = vocab_hits(text.lower(), FRUIT_TYPES, key.lower())
    return bool(record["fruit_type"])


def fruit_size(_key, text, record):
    size = get_size_trait(text, "fruit_size", "fruit")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, ["length", "height"])
    width = get_size_dim(size, "width")
    diameter = get_size_dim(size, "diameter")

    record["fruit_length_min_cm"] = length.min
    record["fruit_length_low_cm"] = length.low
    record["fruit_length_high_cm"] = length.high
    record["fruit_length_max_cm"] = length.max

    record["fruit_width_min_cm"] = width.min
    record["fruit_width_low_cm"] = width.low
    record["fruit_width_high_cm"] = width.high
    record["fruit_width_max_cm"] = width.max

    record["fruit_diameter_min_cm"] = diameter.min
    record["fruit_diameter_low_cm"] = diameter.low
    record["fruit_diameter_high_cm"] = diameter.high
    record["fruit_diameter_max_cm"] = diameter.max

    return has_value(length) or has_value(width)


def get_size_trait(text: str, label: str, part: str) -> Size:
    doc = PIPELINE(text)
    ent = next(
        (e._.trait for e in doc.ents if e.label_ == label and e._.trait.part == part),
        None,
    )
    if not ent:
        ent = next((e._.trait for e in doc.ents if e.label_ == "size"), Size())
    return ent


def get_size_dim(size, dim: str | list[str] = "length") -> Dimension:
    dims = dim if isinstance(dim, list) else [dim]
    if not size:
        return Dimension()
    dim_ = next((d for d in size.dims if d.dim in dims), Dimension())
    return dim_


def vocab_hits(text, vocab, key=None):
    hits = {key: 1} if key and key.lower() in vocab else {}
    hits |= {w: 1 for w in re.split(r"\W+", text) if w.lower() in vocab}
    return " | ".join(hits.keys())


def get_info(soup):
    info = soup.find("div", class_="treatment-info")
    if not info:
        return None
    info = info.find_all(string=True)
    info = [clean(x) for i in info if (x := i.strip()) and i.find(":") > -1]
    info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in info}
    return info


def parse_info(info, record):
    phenology(info, record)
    habitat(info, record)
    elevation(info, record)


def phenology(info, record):
    record["flowering_time"] = info.get("Phenology", "")


def habitat(info, record):
    record["habitat"] = info.get("Habitat", "")


def elevation(info, record):
    text = info.get("Elevation", "")
    size = get_size_trait(text, "", "")
    elev = get_size_dim(size, "length")

    record["elevation_min_m"] = elev.low
    record["elevation_max_m"] = elev.high


def get_terms():
    shape_file = Path(__file__).parent.parent / "rules" / "terms" / "shape_terms.csv"
    fruit_file = Path(__file__).parent.parent / "rules" / "terms" / "fruit_terms.csv"
    dur_file = Path(__file__).parent.parent / "rules" / "terms" / "leaf_terms.csv"

    with shape_file.open() as f:
        shapes = {r["pattern"] for r in csv.DictReader(f)}

    with fruit_file.open() as f:
        fruit_types = {
            r["pattern"] for r in csv.DictReader(f) if r["label"] == "fruit_type"
        }
    fruit_types -= {"fruit", "fruits"}

    with dur_file.open() as f:
        duration = {
            r["pattern"] for r in csv.DictReader(f) if r["label"] == "leaf_duration"
        }

    return shapes, fruit_types, duration


PARSE = {
    # Plants
    "Culm": (plant_height, plant_deciduousness),
    "Culms": (plant_height, plant_deciduousness),
    "Annual": (plant_height, plant_deciduousness),
    "Annual,": (plant_height, plant_deciduousness),
    "Annuals": (plant_height, plant_deciduousness),
    "Annuals,": (plant_height, plant_deciduousness),
    "Annuals.": (plant_height, plant_deciduousness),
    "Biennial": (plant_height, plant_deciduousness),
    "Biennials": (plant_height, plant_deciduousness),
    "Biennials,": (plant_height, plant_deciduousness),
    "Herb": (plant_height, plant_deciduousness),
    "Herb,": (plant_height, plant_deciduousness),
    "Herbage": (plant_height, plant_deciduousness),
    "Herbs": (plant_height, plant_deciduousness),
    "Herbs,": (plant_height, plant_deciduousness),
    "Herbs.": (plant_height, plant_deciduousness),
    "Herbs:": (plant_height, plant_deciduousness),
    "Perennial": (plant_height, plant_deciduousness),
    "Perennials": (plant_height, plant_deciduousness),
    "Perennials,": (plant_height, plant_deciduousness),
    "Perennials.": (plant_height, plant_deciduousness),
    "Plant": (plant_height, plant_deciduousness),
    "Plants": (plant_height, plant_deciduousness),
    "Shrubs": (plant_height, plant_deciduousness),
    "Shrubs,": (plant_height, plant_deciduousness),
    "Subshrubs": (plant_height, plant_deciduousness),
    "Subshrubs,": (plant_height, plant_deciduousness),
    "Subshrubs.": (plant_height, plant_deciduousness),
    "Trees": (plant_height, plant_deciduousness),
    "Trees,": (plant_height, plant_deciduousness),
    "Vines": (plant_height, plant_deciduousness),
    "Vines,": (plant_height, plant_deciduousness),
    "Winter": (plant_height, plant_deciduousness),
    # Leaves
    "Blades": (leaf_size, leaf_shape),
    "Sheaths": (leaf_size, leaf_shape),
    "Leaf": (leaf_size, leaf_shape),
    "Leaf-": (leaf_size, leaf_shape),
    "Leaf-blade": (leaf_size, leaf_shape),
    "Leaves": (leaf_size, leaf_shape),
    "Leaves:": (leaf_size, leaf_shape),
    "Foliage": (leaf_size, leaf_shape),
    "Cauline": (leaf_size, leaf_shape),
    "Fronds": (leaf_size, leaf_shape),
    "Topknots": (leaf_size, leaf_shape),
    # Fruits
    "Fruits": (fruit_size, fruit_type),
    "Fruiting": (fruit_size, fruit_type),
    "Acorns": (fruit_size, fruit_type),
    "Achene": (fruit_size, fruit_type),
    "Achenes": (fruit_size, fruit_type),
    "Berries": (fruit_size, fruit_type),
    "Capsules": (fruit_size, fruit_type),
    "Capules": (fruit_size, fruit_type),
    "Caryopses": (fruit_size, fruit_type),
    "Cypselae": (fruit_size, fruit_type),
    "Drupes": (fruit_size, fruit_type),
    "Follicles": (fruit_size, fruit_type),
    "Loments": (fruit_size, fruit_type),
    "Legumes": (fruit_size, fruit_type),
    "Mericarps": (fruit_size, fruit_type),
    "Pappi": (fruit_size, fruit_type),
    "Pomes": (fruit_size, fruit_type),
    "Schizocarps": (fruit_size, fruit_type),
    "Utricles": (fruit_size, fruit_type),
    # Seeds
    "Seed": (seed_size,),
    "Seeds": (seed_size,),
    # Unused
    "2n": None,
    "Aerial": None,
    "Anthers": None,
    "Anthesis": None,
    "Arrays": None,
    "Bark": None,
    "Barneby": None,
    "Basal": None,
    "Bisexual": None,
    "Both": None,
    "Bracteoles": None,
    "Bracts": None,
    "Buds": None,
    "Bulb": None,
    "Bulbs": None,
    "Burs": None,
    "Callus": None,
    "Calluses": None,
    "Calyces": None,
    "Calyculi": None,
    "Cataphylls": None,
    "Central": None,
    "Chasmogamous": None,
    "Chromosome": None,
    "Cialdella": None,
    "Cleistogamous": None,
    "Corms": None,
    "Corollas": None,
    "Coty": None,
    "Cotyledons": None,
    "Cyathia": None,
    "Cyathial": None,
    "Dietrich": None,
    "Dioecious.": None,
    "Disc": None,
    "Discs": None,
    "Duffield": None,
    "Fertile": None,
    "Fla": None,
    "Floral": None,
    "Florets": None,
    "Flow": None,
    "Flowers": None,
    "Fol": None,
    "Friesner": None,
    "Functionally": None,
    "Glomes": None,
    "Glumes": None,
    "Green": None,
    "Heads": None,
    "Hips": None,
    "In": None,
    "Inflo": None,
    "Inflores": None,
    "Inflorescence": None,
    "Inflorescences": None,
    "Inflorescnecs": None,
    "Infructescences": None,
    "Inner": None,
    "Innermost": None,
    "Internodes": None,
    "Involucellar": None,
    "Involucre": None,
    "Involucres": None,
    "Irwin": None,
    "Lateral": None,
    "Latex": None,
    "Leaflets": None,
    "Lemmas": None,
    "Lianas": None,
    "Ligules": None,
    "Lower": None,
    "Marazzi": None,
    "Mature": None,
    "Oenothera": None,
    "Outer": None,
    "Ovaries": None,
    "Paleae": None,
    "Panicles": None,
    "Pedi": None,
    "Pedicellate": None,
    "Pedicels": None,
    "Peduncle": None,
    "Peduncles": None,
    "Perigynia": None,
    "Petioles": None,
    "Phyllaries": None,
    "Phyllary": None,
    "Pistillate": None,
    "Primary": None,
    "Principal": None,
    "Proximal": None,
    "Pseudobulbs": None,
    "Racemes": None,
    "Rames": None,
    "Ray": None,
    "Rays": None,
    "Receptacles": None,
    "Receptacular": None,
    "Rhizomal": None,
    "Rhizome": None,
    "Rhizomes": None,
    "Roots": None,
    "Scales": None,
    "Scape": None,
    "Scapes": None,
    "Senna": None,
    "Sessile": None,
    "Spathe": None,
    "Spike": None,
    "Spikelets": None,
    "Spikes": None,
    "Stamens": None,
    "Stamimate": None,
    "Staminate": None,
    "Stem": None,
    "Stems": None,
    "Stigmas": None,
    "Stipes": None,
    "Stolons": None,
    "Style": None,
    "Subspecies": None,
    "Subterranean": None,
    "Taproots": None,
    "Terminal": None,
    "The": None,
    "Three": None,
    "Thyrses": None,
    "Tubercles": None,
    "Tubers": None,
    "Twigs": None,
    "Umbel": None,
    "Umbels": None,
    "Upper": None,
    "Variety": None,
    "Wagner": None,
    "Weak": None,
    "Wipff": None,
    "Woody": None,
    "Xylopodium:": None,
}
