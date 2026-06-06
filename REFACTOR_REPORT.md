# ABSA Training Refactor Report

**Date:** June 2026  
**Baseline model:** `model/best_model.pt` (epoch 41, `tas_relaxed_f1 ≈ 0.5799`)  
**Original script:** `train/train.py` (1745 lines, unchanged)

---

## 1. Files Created

### `src/absa/` — Core modules

| File | Lines | Source |
|------|-------|--------|
| `src/absa/__init__.py` | 22 | New |
| `src/absa/labels.py` | 22 | Verbatim from `train/train.py` lines 58–70, 252–253 |
| `src/absa/utils.py` | 85 | Verbatim (`nfc`, `set_seed`, `is_gold_contrast`, `autocast_context`) + new IO helpers |
| `src/absa/dataset.py` | 213 | Verbatim from `train/train.py` lines 89–244, 314–370 |
| `src/absa/model.py` | 175 | Verbatim from `train/train.py` lines 279–520 |
| `src/absa/losses.py` | 173 | Verbatim from `train/train.py` lines 526–692 |
| `src/absa/metrics.py` | 68 | Extracted helpers from `evaluate()` |
| `src/absa/evaluation.py` | 286 | Verbatim `evaluate()` (lines 820–1157) + report wrappers |
| `src/absa/postprocess.py` | 230 | New — spec-based, inference-only, no eval impact |
| `src/absa/inference.py` | 210 | New — strict=True load, 2-pass forward matching `evaluate()` |
| `src/absa/schemas.py` | 65 | New — Pydantic schemas for FastAPI |
| `src/__init__.py` | 1 | New |

### `training/`

| File | Description |
|------|-------------|
| `training/train_absa_full_kaggle.py` | Copy of `train/train.py` + frozen docstring header |

### `scripts/`

| File | Description |
|------|-------------|
| `scripts/eval_model.py` | Load + evaluate; MD5 logging; strict=True gate; baseline parity check |
| `scripts/make_learning_curves.py` | 6 matplotlib plots from `train_log.csv` |
| `scripts/make_confusion_plots.py` | Confusion matrix plots from JSON/JSONL |
| `scripts/make_data_reports.py` | Dataset manifests, distributions, leakage report |
| `scripts/generate_reports.py` | Orchestrator: calls all report scripts + summary JSON |
| `scripts/export_model_artifacts.py` | model_card.json, label_mapping, checksum, tokenizer_info |
| `scripts/package_final_artifacts.py` | Validate + manifest + optional zip |

### `api/`

| File | Description |
|------|-------------|
| `api/__init__.py` | Package marker |
| `api/main.py` | FastAPI: `/health`, `/model-info`, `/predict`, `/predict-batch`, `/metrics/demo` |

### `final_artifacts/` (bootstrapped)

| Path | Contents |
|------|----------|
| `final_artifacts/model/` | `model_card.json`, `label_mapping.json`, `run_config.json`, `tokenizer_info.json`, `postprocess_config.json`, `requirements.txt`, `checksum.txt`, `pointer.txt`, `README.md` |
| `final_artifacts/evaluation/` | `train_log.csv` (copy) |
| `final_artifacts/figures/` | 9 PNG plots (learning curves × 6, confusion × 3) |
| `final_artifacts/demo/` | `demo_success_30.jsonl` (3 sample outputs) |

### Tests

| File | Description |
|------|-------------|
| `tests/test_imports.py` | Import gates for all core modules |
| `tests/test_strict_load.py` | Load `model/best_model.pt` with strict=True |
| `tests/test_inference_smoke.py` | Predict single Vietnamese sentence |
| `tests/test_eval_consistency.py` | Run `evaluate()` on mini dev fixture |
| `tests/fixtures/dev_mini.jsonl` | 3-row mini dev set for CI |

---

## 2. Files Modified

| File | Change |
|------|--------|
| `model/inference.py` | Added deprecation docstring at top (no logic changed) |
| `README.md` | Added new sections: src/absa structure, eval/training/API commands, dataset schema, final_artifacts layout, SageMaker path, troubleshooting |

**Not modified:** `train/train.py`, `training/train_absa_full_kaggle.py` (frozen), `backend/`, `lambda/`, `frontend/`, `infrastructure/`

---

## 3. Logic Preserved Verbatim

The following code was copied character-for-character from `train/train.py`:

- `ASPECTS` list and order
- `N_SENT = 3` and sentiment ID mapping `{0: NEG, 1: POS, 2: NEU}`
- `build_bio_labels()` — BIO label order
- `ABSAModel.__init__` — all layer names and configurations
- `ABSAModel.forward` — complete forward pass
- `extract_contrast_feature` — char-offset based contrast detection
- `compute_clause_position` and `compute_clause_aware_window`
- `collect_valid_ops`, `build_gold_span_targets`, `build_predicted_span_inputs`
- `build_predicted_span_labels`
- `ABSADataset.__init__` — tokenizer batch size, padding, offset mapping
- `evaluate()` — entire function body including all metric computations
- All loss functions: `focal_loss`, `smoothed_cross_entropy`, `symmetric_kl_loss`, `contrast_loss_fn`
- `LBTWWeighter` — EMA-based task weight computation

---

## 4. New Additions

### `src/absa/postprocess.py`
- Confidence thresholds, bad target filtering, phrase expansion
- Span IoU deduplication
- `need_review` / `review_reasons` flags (argmax preserved, not suppressed)
- Global sentiment reconciliation (mixed POS+NEG → blend toward NEU)
- **Does not affect evaluation** — `evaluate()` uses raw model outputs

### `src/absa/inference.py`
- `load_model()` with `strict=True` — raises `RuntimeError` on mismatch
- `predict_one()` / `predict_batch()` — full response schema including `need_review`, `guardrail_status`
- 2-pass forward: BIO decode → predicted spans → sentiment/global (matches `evaluate()`)

### `api/main.py`
- Model loaded once at startup via FastAPI lifespan
- `/metrics/demo` endpoint for monitoring latency

### `scripts/` report suite
- Learning curves with best-epoch markers
- Confusion matrix plots (raw + normalized)
- Dataset manifest, distributions, leakage detection
- Model card with known limitations

---

## 5. Running Evaluation

```bash
python scripts/eval_model.py \
  --model-path model/best_model.pt \
  --eval-file  /path/to/dev_clean.jsonl \
  --output-dir final_artifacts/evaluation \
  --strict-load true
```

Expected: `tas_relaxed_f1 ≈ 0.58`, deviation > 0.05 triggers WARNING.

---

## 6. Running Inference API

```bash
export ABSA_MODEL_DIR=final_artifacts/model
export ABSA_DEVICE=cpu
uvicorn api.main:app --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Giá mềm, chất vải mát, nhưng giao hàng chậm."}'
```

---

## 7. Running Report Generation

```bash
# Learning curves + confusion plots + summary
python scripts/generate_reports.py \
  --train-log      model/train_log.csv \
  --confusion-file model/confusion_matrices.jsonl \
  --output-dir     final_artifacts

# Export model card + label mapping
python scripts/export_model_artifacts.py \
  --model-path model/best_model.pt \
  --train-log  model/train_log.csv \
  --output-dir final_artifacts/model

# Package for submission/S3
python scripts/package_final_artifacts.py \
  --artifacts-dir final_artifacts \
  --output-zip    final_artifacts/absa_model_package.zip
```

---

## 8. Remaining Risks

| Risk | Mitigation |
|------|------------|
| `model/inference.py` still uses `strict=False` | Deprecated with header comment; `backend/` still works; new code uses `src.absa.inference` |
| Dev file not in repo | `scripts/eval_model.py` requires explicit `--eval-file` path; CI uses `tests/fixtures/dev_mini.jsonl` |
| `best_model.pt` gitignored | Tests conditionally skip strict-load and smoke tests if checkpoint absent |
| `src/absa/postprocess.py` schema differs from `model/postprocess.py` | New postprocess is inference-only; eval metrics are unaffected |
| SageMaker inference handler not written | `final_artifacts/` layout is container-ready; handler is a separate step |
| `api/main.py` uses `ABSA_MODEL_DIR` env var | Must point to directory with `best_model.pt` AND `run_config.json` |

---

## 9. Test Checklist

Run from repo root with `PYTHONPATH=.`:

```bash
pytest tests/ -v
```

| Test | Expected |
|------|----------|
| `test_imports.py` | PASS — 10/10 (all modules importable) |
| `test_strict_load.py` | PASS — 2/2 (strict=True, key count match) |
| `test_inference_smoke.py` | PASS — 3/3 (schema, aspects, batch) |
| `test_eval_consistency.py` | PASS — 2/2 (evaluate() runs, schema check) |
| **Total** | **17/17 PASS** |

**Note on `.float()` fix:** `model.float()` is called after loading the checkpoint in
`src/absa/inference.py` and `scripts/eval_model.py`. This matches `train/train.py` which
initializes the model with `.to(device).float()`. Without this cast, the backbone emits
float16 on CPU while LSTM weights remain float32, causing a dtype mismatch. The fix does
not affect model architecture or metric correctness.

---

## 10. Architecture Invariant Verification

The `ABSAModel.state_dict()` key set must be identical between `src/absa/model.py` and the checkpoint. Verify:

```python
import sys; sys.path.insert(0, ".")
import torch
from src.absa.model import ABSAModel
m = ABSAModel("Fsoft-AIC/videberta-base", max_ops=6)
state = torch.load("model/best_model.pt", map_location="cpu")
missing, unexpected = m.load_state_dict(state, strict=False)
assert not missing,    f"Missing keys: {missing}"
assert not unexpected, f"Unexpected keys: {unexpected}"
print("OK — architecture matches checkpoint")
```
