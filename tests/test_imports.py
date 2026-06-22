"""Test that all ml.inference modules import correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_labels_import():
    from ml.inference.labels import (
        ASPECTS, N_SENT, N_BIO,
        SENT_ID2LABEL, SENT_LABEL2ID,
        BIO_LABELS, BIO_L2I, BIO_I2L,
        build_bio_labels,
    )
    assert ASPECTS == ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
    assert N_SENT == 3
    assert SENT_ID2LABEL == {0: "NEG", 1: "POS", 2: "NEU"}
    assert SENT_LABEL2ID == {"NEG": 0, "POS": 1, "NEU": 2}
    assert BIO_LABELS[0] == "O"
    assert BIO_LABELS[1] == "B-Fashion"
    assert N_BIO == 1 + 2 * 7  # O + B/I per aspect


def test_utils_import():
    from ml.inference.utils import (
        nfc, set_seed, is_gold_contrast, autocast_context,
        get_device, ensure_dir, md5_file, load_json, save_json,
        load_jsonl, save_jsonl, REPO_ROOT,
    )
    assert REPO_ROOT.is_dir()


def test_dataset_import():
    from ml.inference.dataset import (
        ABSADataset,
        extract_spans,
        build_gold_span_targets,
        build_predicted_span_inputs,
        build_predicted_span_labels,
        compute_clause_position,
        compute_clause_aware_window,
        collect_valid_ops,
        TOKENIZE_BATCH_SIZE,
    )
    assert TOKENIZE_BATCH_SIZE == 512


def test_model_import():
    from ml.inference.model import ABSAModel, extract_contrast_feature
    from ml.inference.utils import CONTRAST_WORDS
    assert "nhưng" in CONTRAST_WORDS


def test_losses_import():
    from ml.inference.losses import (
        focal_loss, smoothed_cross_entropy, smoothed_ce_per_sample,
        smooth_values_for_targets, symmetric_kl_loss,
        contrast_loss_fn, LBTWWeighter,
    )


def test_metrics_import():
    from ml.inference.metrics import (
        confusion_payload, label_names_for_sentiment,
        prf_macro, prf_per_class, span_prf, tas_prf,
        per_aspect_sent_f1, per_aspect_span_f1,
    )
    assert label_names_for_sentiment() == ["NEG", "POS", "NEU"]


def test_evaluation_import():
    from ml.inference.evaluation import (
        evaluate, format_eval_metrics,
        print_eval_metrics_line, save_eval_report,
    )


def test_postprocess_import():
    from ml.inference.postprocess import (
        PostprocessConfig, postprocess_predictions,
        dedupe_overlapping_spans, reconcile_global_sentiment,
    )
    cfg = PostprocessConfig()
    assert cfg.sentiment_confidence_threshold == 0.55
    assert cfg.min_aspect_confidence == 0.45


def test_inference_import():
    from ml.inference.inference import (
        load_tokenizer, load_model, predict_one, predict_batch,
        MODEL_VERSION,
    )
    assert MODEL_VERSION == "absa-v2b"


def test_schemas_import():
    from ml.inference.schemas import (
        PredictRequest, BatchPredictRequest,
        OpinionPrediction, PredictResponse,
        ModelInfoResponse, HealthResponse,
    )
