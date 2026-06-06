# Audit Lambda

VLSP / ABSA dataset quality audit: span offsets, aspect schema, sentiment polarity, duplicates, global consistency.

## Checks

- JSONL parse success
- Span `text[start:end]` matches `target`
- Aspects in training schema (Fashion, Price, …)
- Sentiment 0/1/2
- Duplicate (target, aspect) per sentence
- Global sentiment vs majority opinion (warning)

## API

- `POST /audit` (API Gateway) — body `{ "dataset_key": "datasets/raw/foo.jsonl" }`
- Step Functions — payload `{ "action": "audit", "dataset_key": "..." }`

Reports written to `s3://<bucket>/reports/audit/<report_id>.json`.

## Local engine

```bash
PYTHONPATH=lambda/audit python3 -c "
from dataset_audit import run_dataset_audit
from pathlib import Path
print(run_dataset_audit(Path('model/demo_10.jsonl'))['passed'])
"
```

Admin dashboard uses backend `POST /audit/run` (same engine).
