import spacy
from traiter.pylib.pipes import extensions, tokenizer

from ccf.rules.leaf_size import LeafSize
from ccf.rules.range import Range
from ccf.rules.size import Size


def build(part=""):
    extensions.add_extensions()

    nlp = spacy.load("en_core_web_md", exclude=["ner"])

    tokenizer.setup_tokenizer(nlp)

    Range.pipe(nlp)
    Size.pipe(nlp)

    if part == "leaf":
        LeafSize.pipe(nlp)

    return nlp
