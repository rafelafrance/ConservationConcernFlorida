import re
from dataclasses import dataclass

from spacy import registry
from spacy.language import Language
from traiter.pipes import add
from traiter.pylib import const as t_const
from traiter.pylib.pattern_compiler import Compiler
from traiter.rules.base import Base


@dataclass(eq=False)
class Range(Base):
    min: float = None
    low: float = None
    high: float = None
    max: float = None

    @classmethod
    def pipe(cls, nlp: Language):
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(nlp, name="range_patterns", compiler=cls.range_patterns())

    @classmethod
    def range_patterns(cls):
        decoder = {
            "(": {"TEXT": {"IN": t_const.OPEN}},
            ")": {"TEXT": {"IN": t_const.CLOSE}},
            "-": {"TEXT": {"IN": t_const.DASH}, "OP": "+"},
            "9.9": {"TEXT": {"REGEX": r"\d+(\.\d*)?"}},
            "[+]": {"TEXT": {"IN": t_const.PLUS}},
        }
        return [
            Compiler(
                label="range.low",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " 9.9 ",
                ],
            ),
            Compiler(
                label="range.min.low",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " ( 9.9 -* ) 9.9 ",
                ],
            ),
            Compiler(
                label="range.low.high",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " 9.9 - 9.9 [+]? ",
                ],
            ),
            Compiler(
                label="range.low.max",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " 9.9 ( -* 9.9 [+]? ) ",
                ],
            ),
            Compiler(
                label="range.min.low.high",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " ( 9.9 -* ) 9.9 - 9.9 [+]? ",
                ],
            ),
            Compiler(
                label="range.min.low.max",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " ( 9.9 -* ) 9.9 - ( -* 9.9 [+]? ) ",
                ],
            ),
            Compiler(
                label="range.low.high.max",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " 9.9 - 9.9 ( -* 9.9 [+]? ) ",
                ],
            ),
            Compiler(
                label="range.min.low.high.max",
                on_match="range_match",
                decoder=decoder,
                patterns=[
                    " ( 9.9 -* ) 9.9 - 9.9 [+]? ( -* 9.9 [+]? ) ",
                    " ( 9.9 -* ) 9.9 - 9.9 [+]? ( -* 9.9 [+]? ) ( -* 9.9 [+]? ) ",
                ],
            ),
        ]

    @classmethod
    def range_match(cls, ent):
        nums = []
        for token in ent:
            nums += re.findall(r"\d*\.?\d+", token.text)

        keys = ent.label_.split(".")[1:]
        kwargs = dict(zip(keys, nums, strict=False))

        ent._.relabel = "range"

        trait = cls.from_ent(ent, **kwargs)

        return trait


@registry.misc("range_match")
def range_match(ent):
    return Range.range_match(ent)
