from dataclasses import dataclass

from spacy.language import Language
from traiter.rules.base import Base as TraiterBase


@dataclass(eq=False)
class Base(TraiterBase):
    _paragraph: str | None = None

    @classmethod
    def pipe(cls, nlp: Language):
        raise NotImplementedError
