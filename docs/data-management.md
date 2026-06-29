# Data management

This project uses **two complementary data paths**:

| Data type | Management | Purpose |
|-----------|------------|---------|
| Local benchmark (train/dev/test) | **Git + `publish_approved_dataset.py` → S3** | Reproducible research baseline |
| Admin UI uploads | **S3 pending → audit → approved + DynamoDB** | Operational ingestion |
| Prediction feedback | **DynamoDB review queue + S3** | Retraining signals |

Cloud training reads human-readable paths on S3:

```text
s3://absa-mlops-demo-artifacts/
  datasets/
    pending/                 # Admin uploads awaiting audit
    approved/                # Training-ready splits
    manifests/               # dataset_manifest.json per dataset_id
  models/
  reports/audit/
```

## Track 1 — Local benchmark publish

Place preprocessed splits under `data/processed/`:

```text
data/processed/train.jsonl
data/processed/dev.jsonl
data/processed/test.jsonl
```

Publish to cloud:

```bash
export ARTIFACTS_BUCKET=absa-mlops-demo-artifacts
export AWS_REGION=ap-southeast-1

python scripts/publish_approved_dataset.py \
  --dataset-id dataset-v1 \
  --name "ABSA Benchmark v1"
```

This uploads to:

- `datasets/approved/dataset-v1/{train,dev,test}.jsonl`
- `datasets/pending/dataset-v1/` (mirror for audit Lambda)
- `datasets/manifests/dataset-v1.json`
- DynamoDB `datasets` table (status `APPROVED`)

Manifest uses `"source": "local_publish"` and records the current Git commit in `lineage.git_commit`.

### One-time audit (recommended)

```bash
curl -X POST "https://api.minhhuy.me/datasets/dataset-v1/audit" \
  -H 'Content-Type: application/json' -d '{}'

curl -X POST "https://api.minhhuy.me/datasets/dataset-v1/approve" \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approve"}'
```

## Track 2 — Admin platform upload

Operational flow:

```text
Admin UI → presign upload → datasets/pending/{id}/
         → POST /audit
         → POST /approve
         → training pipeline
```

Manifest schema is shared; `"source": "platform_upload"` distinguishes UI uploads from script publishes.

## What not to commit to Git

- Large raw crawl dumps (use S3 or local-only paths)
- Prediction logs
- Model checkpoints (use S3 `models/` prefixes)
- Frontend/backend build output

## Thesis narrative

> **Research reproducibility** is enforced by Git commit lineage in manifests plus checksums per split.  
> **Production MLOps** is enforced by S3 lifecycle, audit benchmarks, and DynamoDB registry.
