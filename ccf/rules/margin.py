import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spacy.util import registry
from traiter.pipes import add
from traiter.pylib import const as t_const
from traiter.pylib import term_util
from traiter.pylib.pattern_compiler import Compiler

from ccf.rules.base import Base

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.tokens import Span


@dataclass(eq=False)
class Margin(Base):
    # Class vars ----------
    margin_csv: ClassVar[Path] = Path(__file__).parent / "terms" / "margin_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(margin_csv, "replace")
    ent_types: ClassVar[set[str]] = {
        "margin_term", "shape", "margin_follower", "margin_leader"
    }
    # ---------------------

    margin: str = ""

    @classmethod
    def pipe(cls, nlp: Language) -> None:
        add.term_pipe(nlp, name="margin_terms", path=cls.margin_csv)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="margin_patterns",
            compiler=cls.margin_patterns(),
            overwrite=["shape"],
        )
        add.cleanup_pipe(nlp, name="margin_cleanup")

    @classmethod
    def margin_patterns(cls) -> list[Compiler]:
        return [
            Compiler(
                label="margin",
                on_match="margin_match",
                decoder={
                    "-": {"TEXT": {"IN": t_const.DASH}},
                    "margin": {"ENT_TYPE": "margin_term"},
                    "shape": {"ENT_TYPE": "shape"},
                    "leader": {"ENT_TYPE": {"IN": ["shape", "margin_leader"]}},
                    "follower": {
                        "ENT_TYPE": {"IN": ["margin_term", "margin_follower"]},
                    },
                },
                patterns=[
                    "leader* -* margin+",
                    "leader* -* margin+ -* follower*",
                    "leader* -* margin+ -* shape? follower+ shape?",
                    "shape+ -* follower+",
                ],
            ),
        ]

    @classmethod
    def margin_match(cls, ent: Span) -> Margin:
        words = []  # Dicts preserve order sets do not
        for token in ent:
            word = token.text
            if token.ent_type_ in cls.ent_types:
                word = cls.replace.get(token.lower_, token.lower_)
            words.append(word)
        margin = " ".join(words)
        margin = re.sub(rf"\s+({t_const.DASH_RE})\s+", r"\1", margin)
        margin = margin.replace(" - ", "-")
        margin = cls.replace.get(margin, margin)
        return cls.from_ent(ent, margin=margin)


@registry.misc("margin_match")
def margin_match(ent: Span) -> Margin:
    return Margin.margin_match(ent)
