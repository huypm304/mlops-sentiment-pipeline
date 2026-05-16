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

| Variable | Default |
|----------|---------|
| `ABSA_MODEL_DIR` | `./model` |
| `CORS_ORIGINS` | `http://localhost:3000,...` |
| `API_HOST` | `0.0.0.0` |
| `API_PORT` | `8000` |

## Frontend

Set in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
