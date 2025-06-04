import spacy
from traiter.pipes import delete, extensions, tokenizer

from ccf.rules.fruit_size import FruitSize
from ccf.rules.fruit_type import FruitType
from ccf.rules.leaf_duration import LeafDuration
from ccf.rules.leaf_size import LeafSize
from ccf.rules.other_size import OtherSize
from ccf.rules.range import Range
from ccf.rules.seed_size import SeedSize
from ccf.rules.shape import Shape
from ccf.rules.size import Size


def build():
    extensions.add_extensions()

    nlp = spacy.load("en_core_web_md", exclude=["ner"])

    tokenizer.setup_tokenizer(nlp)

    Shape.pipe(nlp)
    LeafDuration.pipe(nlp)
    FruitType.pipe(nlp)

    Range.pipe(nlp)
    Size.pipe(nlp)

    OtherSize.pipe(nlp)
    LeafSize.pipe(nlp)
    SeedSize.pipe(nlp)
    FruitSize.pipe(nlp)

    delete.pipe(nlp, traits=["other_size"])

    return nlp
