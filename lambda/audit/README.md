# Audit Lambda

Train+dev data benchmark audit powered by `data_benchmark/` (schema, spans, labels, distribution, global sentiment, leakage).

## Checks (6 modules)

| Module | Scope |
|--------|--------|
| `schema_audit` | Required fields, valid aspect/sentiment labels |
| `span_offset_audit` | Opinion span offsets match text |
| `label_consistency_audit` | Suspicious aspect/sentiment patterns |
| `distribution_audit` | Per-aspect and cell counts |
| `global_sentiment_audit` | Global sentiment vs opinion rule |
| `leakage_audit` | Exact/near duplicate train↔dev |

Overall pass: `data_level_status != "fail"` (warnings allowed).

## API

- `POST /audit` (API Gateway) — body `{ "dataset_key": "datasets/pending/{id}/train.jsonl" }`
- Step Functions — payload `{ "action": "validate", "dataset_id": "...", "dataset_key": "..." }`

Both train and dev JSONL must exist under the same S3 prefix.

Reports written to `s3://<bucket>/reports/audit/<report_id>.json`.

## Build for deploy

```bash
bash scripts/build_audit_lambda.sh
```

Bundles `data_benchmark/` into `lambda/.build/audit/` (used by Terraform runtime stack).

## Local engine

```bash
PYTHONPATH=lambda/audit python3 -c "
from pathlib import Path
from dataset_audit import run_dataset_audit
report = run_dataset_audit(
    Path('datasets/local/my-batch/train.jsonl'),
    Path('datasets/local/my-batch/dev.jsonl'),
    dataset_id='my-batch',
)
print(report['passed'], report['data_level_status'])
"
```

Admin dashboard uses backend `POST /audit/run` or `POST /datasets/{id}/audit` (same engine).
