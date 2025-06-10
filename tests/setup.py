from ccf.pylib import pipeline
from ccf.pylib.str_util import clean

PIPELINE = pipeline.build()


def parse(text: str) -> list:
    text = " ".join(text.split())
    text = clean(text)
    doc = PIPELINE(text)

    traits = [e._.trait for e in doc.ents]

    from pprint import pp

    pp(traits)

    return traits
