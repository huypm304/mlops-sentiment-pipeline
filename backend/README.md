# ABSA Inference API (local demo)

FastAPI service wrapping the trained ViBERTa ABSA checkpoint in `model/best_model.pt`.

## Prerequisites

- Python 3.10+
- `model/best_model.pt` and `model/config.json` (or `run_config.json`) in the repo
- First run downloads `Fsoft-AIC/videberta-base` from Hugging Face

## Setup

```bash
cd /path/to/mlops-sentiment-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r model/requirements.txt
```

## Run

From repository root:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or:

```bash
python -m backend.app.main
```

## Endpoints

- `GET /health` — model load status
- `POST /predict` — run inference

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Sản phẩm đẹp nhưng giao hàng chậm"}'
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `ABSA_MODEL_DIR` | `./model` | Model checkpoint directory |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed frontend origins |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Bind port |

### Optional AWS registry (DynamoDB)

When these are set, uploads/audits/predictions/pipeline runs sync to DynamoDB (see `backend/.env.example`):

| Variable | Purpose |
|----------|---------|
| `ARTIFACTS_BUCKET` | S3 artifact bucket |
| `RETRAIN_STATE_MACHINE_ARN` | Step Functions training pipeline |
| `DATASETS_TABLE` | Dataset registry |
| `TRAINING_RUNS_TABLE` | Pipeline run records |
| `MODELS_TABLE` | Model registry |
| `PREDICTIONS_TABLE` | Inference log summaries |
| `MONITORING_TABLE` | Monitoring snapshots |
| `APPROVAL_TABLE` | Human approval requests |
| `REVIEW_QUEUE_TABLE` | Low-confidence review queue |

Seed baseline production model after deploy:

```bash
export MODELS_TABLE=absa-mlops-demo-models ARTIFACTS_BUCKET=absa-mlops-demo-artifacts
python scripts/seed_registry.py
```

## Frontend

Set in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
