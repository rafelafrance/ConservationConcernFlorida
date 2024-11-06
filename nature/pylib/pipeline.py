import spacy
from traiter.pylib.pipes import extensions, sentence, tokenizer
from traiter.pylib.rules.date_ import Date
from traiter.pylib.rules.elevation import Elevation
from traiter.pylib.rules.habitat import Habitat
from traiter.pylib.rules.lat_long import LatLong

# from traiter.pylib.pipes import debug


def build():
    extensions.add_extensions()

    nlp = spacy.load("en_core_web_md", exclude=["ner"])

    tokenizer.setup_tokenizer(nlp)

    config = {"base_model": "en_core_web_md"}
    nlp.add_pipe(sentence.SENTENCES, config=config, before="parser")

    Date.pipe(nlp)

    Elevation.pipe(nlp)
    LatLong.pipe(nlp)

    Habitat.pipe(nlp)

    return nlp
