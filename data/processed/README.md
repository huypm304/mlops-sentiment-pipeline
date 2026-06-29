# Official benchmark splits

Place the **canonical** train/dev/test JSONL files here after local preprocessing.

Operational uploads from the admin UI use `datasets/pending/` on S3 instead.

## Publish to cloud

```bash
# After placing train.jsonl, dev.jsonl, test.jsonl in this folder:
python scripts/publish_approved_dataset.py \
  --dataset-id dataset-v1 \
  --name "ABSA Benchmark v1"
```

See [docs/data-management.md](../../docs/data-management.md) for the full data architecture.
