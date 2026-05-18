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
class Surface(Base):
    # Class vars ----------
    surface_csv: ClassVar[Path] = Path(__file__).parent / "terms" / "surface_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(surface_csv, "replace")
    # ---------------------

    surface: str = ""

    @classmethod
    def pipe(cls, nlp: Language) -> None:
        add.term_pipe(nlp, name="surface_terms", path=cls.surface_csv)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(nlp, name="surface_patterns", compiler=cls.surface_patterns())
        add.cleanup_pipe(nlp, name="surface_cleanup")

    @classmethod
    def surface_patterns(cls) -> list[Compiler]:
        return [
            Compiler(
                label="surface",
                on_match="surface_match",
                decoder={
                    "-": {"TEXT": {"IN": t_const.DASH}},
                    "surface": {"ENT_TYPE": "surface_term"},
                    "leader": {"ENT_TYPE": "surface_leader"},
                },
                patterns=[
                    "           surface ",
                    " leader -? surface ",
                ],
            ),
        ]

    @classmethod
    def surface_match(cls, ent: Span) -> Surface:
        surface = {}  # Dicts preserve order sets do not
        for token in ent:
            if token.ent_type_ == "surface_term" and token.text != "-":
                word = cls.replace.get(token.lower_, token.lower_)
                surface[word] = 1
        surface = " ".join(surface)
        surface = cls.replace.get(surface, surface)
        return cls.from_ent(ent, surface=surface)


@registry.misc("surface_match")
def surface_match(ent: Span) -> Surface:
    return Surface.surface_match(ent)
