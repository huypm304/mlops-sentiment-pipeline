# Official benchmark splits (DVC-tracked)

Place the **canonical** train/dev/test JSONL files here after local preprocessing.

These three files are the only dataset artifacts managed by DVC in this project.
Operational uploads from the admin UI use `datasets/pending/` on S3 instead.

## Quick start

```bash
# One-time setup
./scripts/dvc_setup.sh

# After placing train.jsonl, dev.jsonl, test.jsonl in this folder:
dvc add train.jsonl dev.jsonl test.jsonl
dvc push
git add train.jsonl.dvc dev.jsonl.dvc test.jsonl.dvc .gitignore
git commit -m "Track benchmark dataset v1 with DVC"

# Publish approved copy + manifest to S3 (requires AWS credentials)
python scripts/publish_approved_dataset.py \
  --dataset-id dataset-v1 \
  --name "ABSA Benchmark v1"
```

See [docs/data-management.md](../../docs/data-management.md) for the full dual-track architecture.
