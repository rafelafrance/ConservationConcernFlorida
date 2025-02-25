import spacy
from traiter.pylib.pipes import extensions, tokenizer

from ccf.pylib.rules.range import Range
from ccf.pylib.rules.size import Size


def build():
    extensions.add_extensions()

    nlp = spacy.load("en_core_web_md", exclude=["ner"])

    tokenizer.setup_tokenizer(nlp)

    Range.pipe(nlp)
    Size.pipe(nlp)

    return nlp
