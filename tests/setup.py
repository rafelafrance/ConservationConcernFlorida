from ccf.pylib import pipeline

PIPELINE = pipeline.build()
LEAF_PIPELINE = pipeline.build("leaf")


def parse(text: str, part="") -> list:
    text = " ".join(text.split())
    doc = LEAF_PIPELINE(text) if part == "leaf" else PIPELINE(text)

    traits = [e._.trait for e in doc.ents]

    # from pprint import pp
    #
    # pp(traits)

    return traits
