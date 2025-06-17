from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pipes import add
from traiter.pylib.pattern_compiler import Compiler

from ccf.rules.base import Base


@dataclass(eq=False)
class PartColor(Base):
    # Class vars ----------
    terms: ClassVar[list[Path]] = [
        Path(__file__).parent / "terms" / "other_terms.csv",
        Path(__file__).parent / "terms" / "fruit_terms.csv",
        Path(__file__).parent / "terms" / "leaf_terms.csv",
        Path(__file__).parent / "terms" / "seed_terms.csv",
    ]
    parts: ClassVar[list[str]] = ["other_term", "fruit_part", "leaf_part", "seed_part"]
    # ---------------------

    part: str = None
    colors: list[str] = field(default_factory=list)

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="part_color_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="part_color_patterns",
            compiler=cls.part_color_patterns(),
            overwrite=[*cls.parts, "color"],
        )

        add.cleanup_pipe(nlp, name="part_color_cleanup")

    @classmethod
    def part_color_patterns(cls):
        return [
            Compiler(
                label="part_color",
                on_match="part_color_match",
                decoder={
                    "color": {"ENT_TYPE": "color"},
                    "part": {"ENT_TYPE": {"IN": cls.parts}},
                },
                patterns=[
                    "color+ part+",
                ],
            ),
        ]

    @classmethod
    def part_color_match(cls, ent):
        colors = []
        part = ""

        for e in ent.ents:
            if e.label_ == "color":
                colors.append(e.text.lower())

            elif e.label_ in cls.parts:
                part = e.text.lower()

        colors = " ".join(colors)

        trait = cls.from_ent(ent, part=part, colors=colors)
        return trait


@registry.misc("part_color_match")
def part_color_match(ent):
    return PartColor.part_color_match(ent)
