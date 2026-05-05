from dataclasses import dataclass
from typing import TYPE_CHECKING

from traiter.rules.base_rule import BaseRule as TraiterBase

if TYPE_CHECKING:
    from spacy.language import Language


@dataclass(eq=False)
class Base(TraiterBase):
    _paragraph: str | None = None

    @classmethod
    def pipe(cls, nlp: Language) -> None:
        del nlp
        raise NotImplementedError
