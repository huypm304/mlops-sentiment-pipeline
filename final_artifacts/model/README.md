# ABSA Model Artifacts

Version: **absa-v2b**

## Contents

| File | Description |
|------|-------------|
| `best_model.pt` / `pointer.txt` | Checkpoint or path pointer |
| `run_config.json` | Hyperparameters used during training |
| `label_mapping.json` | ASPECTS, BIO labels, sentiment mapping |
| `tokenizer_info.json` | Tokenizer configuration |
| `postprocess_config.json` | Inference post-processing thresholds |
| `model_card.json` | Full model card (architecture, metrics, limitations) |
| `requirements.txt` | Python dependencies |
| `checksum.txt` | MD5 checksums for all files |

## Quick inference

```python
import sys; sys.path.insert(0, ".")
from src.absa.inference import load_model, predict_one

bundle = load_model("final_artifacts/model")
result = predict_one("Giá mềm nhưng giao hàng chậm", bundle)
print(result)
```

## Metrics (best epoch)

{
  "tas_strict_f1": 0.5821,
  "tas_relaxed_f1": 0.593,
  "span_f1": 0.821,
  "sent_matched_f1": 0.6615,
  "global_f1": 0.6602
}

## Known limitations

- Weak on implicit/sarcastic opinions
- Boundary errors on very short targets
- Confidence threshold + review queue recommended for production
