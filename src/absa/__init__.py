# src/absa — core ABSA modules extracted from training script
from .labels import (
    ASPECTS,
    N_SENT,
    SENT_ID2LABEL,
    SENT_LABEL2ID,
    BIO_LABELS,
    BIO_L2I,
    BIO_I2L,
    N_BIO,
    build_bio_labels,
)

__all__ = [
    "ASPECTS",
    "N_SENT",
    "SENT_ID2LABEL",
    "SENT_LABEL2ID",
    "BIO_LABELS",
    "BIO_L2I",
    "BIO_I2L",
    "N_BIO",
    "build_bio_labels",
]
