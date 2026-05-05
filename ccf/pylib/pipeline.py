from typing import TYPE_CHECKING

import spacy
from traiter.pipes import extensions, tokenizer

from ccf.rules.margin import Margin
from ccf.rules.shape import Shape
from ccf.rules.surface import Surface

if TYPE_CHECKING:
    from spacy.language import Language


def build() -> Language:
    extensions.add_extensions()

    nlp = spacy.load("en_core_web_md", exclude=["ner"])

    tokenizer.setup_tokenizer(nlp)

    Shape.pipe(nlp)
    Margin.pipe(nlp)
    Surface.pipe(nlp)

    return nlp
