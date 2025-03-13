from dataclasses import dataclass


@dataclass
class Traits:
    plant_height: str = ""
    leaf_shape: str = ""
    leaf_length: str = ""
    leaf_width: str = ""
    leaf_thickness: str = ""
    fruit_type: str = ""
    fruit_length: str = ""
    fruit_width: str = ""
    seed_length: str = ""
    seed_width: str = ""
    deciduousness: str = ""
    flowering_time: str = ""
    habitat: str = ""
    elevation: str = ""


@dataclass
class Example(Traits):
    taxon: str = ""
    text: str = ""
