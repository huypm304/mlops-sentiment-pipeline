# Data management — dual-track architecture

This project uses **two complementary data paths**:

| Data type | Management | Purpose |
|-----------|------------|---------|
| Official benchmark (train/dev/test) | **DVC + Git + S3 `dvc-store/`** | Reproducible research baseline |
| Admin UI uploads | **S3 pending → audit → approved + DynamoDB** | Operational ingestion |
| Prediction feedback | **DynamoDB review queue + S3** | Retraining signals |

Cloud training **never runs DVC inside SageMaker**. It reads human-readable paths:

```text
s3://absa-mlops-demo-artifacts/
  dvc-store/                 # DVC content-addressed blobs (opaque)
  datasets/
    pending/                 # Admin uploads awaiting audit
    approved/                # Training-ready splits + DVC publishes
    manifests/               # dataset_manifest.json per dataset_id
  models/
  reports/audit/
```

## Track 1 — Official benchmark (DVC)

### One-time setup

```bash
./scripts/dvc_setup.sh
# or: pip install 'dvc[s3]' && dvc init
```

Remote (committed in `.dvc/config`):

```text
s3://absa-mlops-demo-artifacts/dvc-store
```

### Version a dataset locally

```bash
# 1. Preprocess → place files here
datasets/processed/train.jsonl
datasets/processed/dev.jsonl
datasets/processed/test.jsonl

# 2. Track with DVC
cd datasets/processed
dvc add train.jsonl dev.jsonl test.jsonl
dvc push
cd ../..
git add datasets/processed/*.dvc datasets/processed/.gitignore .dvc/config
git commit -m "Track benchmark dataset v1 with DVC"
```

### Publish to cloud (bridge script)

After `dvc pull` on any machine:

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

Optional DVC stage:

```bash
dvc repro publish
```

### One-time audit (recommended)

```bash
curl -X POST "https://api.minhhuy.me/datasets/dataset-v1/audit" \
  -H 'Content-Type: application/json' -d '{}'

curl -X POST "https://api.minhhuy.me/datasets/dataset-v1/approve" \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approve"}'
```

## Track 2 — Admin platform upload

Unchanged operational flow:

```text
Admin UI → presign upload → datasets/pending/{id}/
         → POST /audit
         → POST /approve
         → training pipeline
```

Manifest schema is shared; `"source": "platform_upload"` distinguishes from DVC publishes.

## What NOT to DVC-track

- Raw crawl data
- Temporary preprocessing files
- Prediction logs
- Model checkpoints (use S3 `models/` prefixes)
- Frontend/backend build output

## Thesis narrative

> **Research reproducibility** is enforced by DVC + Git lineage.  
> **Production MLOps** is enforced by S3 lifecycle, audit benchmarks, and DynamoDB registry.  
> The publish script connects both worlds without duplicating orchestration.

Future work: run `dvc pull` inside SageMaker training container (requires Git + IAM in training image).
