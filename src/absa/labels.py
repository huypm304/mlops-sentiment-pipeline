"""Label definitions for Vietnamese ABSA — extracted verbatim from train/train.py.

Do NOT change the order of ASPECTS, BIO labels, or sentiment IDs.
Any change breaks checkpoint compatibility.
"""

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
N_SENT = 3

SENT_ID2LABEL = {0: "NEG", 1: "POS", 2: "NEU"}
SENT_LABEL2ID = {"NEG": 0, "POS": 1, "NEU": 2}


def build_bio_labels():
    labels = ["O"]
    for aspect in ASPECTS:
        labels.extend([f"B-{aspect}", f"I-{aspect}"])
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio_labels()
N_BIO = len(BIO_LABELS)
