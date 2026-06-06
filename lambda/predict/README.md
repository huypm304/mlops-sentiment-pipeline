# Predict Lambda

HTTP API handler for Vietnamese ABSA inference.

## Routes (via API Gateway)

- `POST /predict` — run inference on review text
- `GET /health` — readiness probe

## Inference modes

| Mode | When | Result |
|------|------|--------|
| **Stub** | `ENABLE_SAGEMAKER_ENDPOINT=false` (default) | Empty opinions, neutral sentiment |
| **SageMaker** | Endpoint enabled + model uploaded | Real ABSA via `InvokeEndpoint` |

## Environment

| Variable | Description |
|----------|-------------|
| `ARTIFACTS_BUCKET` | S3 bucket for model artifacts |
| `SAGEMAKER_ENDPOINT_NAME` | SageMaker endpoint (e.g. `absa-mlops-demo-endpoint`) |
| `ENABLE_SAGEMAKER_ENDPOINT` | `true` to invoke SageMaker |
| `PRODUCTION_MODEL_ID` | Model id stored in DynamoDB predictions log |
| `AWS_REGION` | Region for SageMaker Runtime client |

## Deploy real inference on AWS

1. Export model artifacts locally:

```bash
python scripts/export_model_artifacts.py \
  --copy-checkpoint \
  --output-dir final_artifacts/model
```

2. Package and upload SageMaker tarball:

```bash
chmod +x scripts/package_sagemaker_model.sh
./scripts/package_sagemaker_model.sh --upload --bucket absa-mlops-demo-artifacts
```

Upload target: `s3://<bucket>/models/production/model.tar.gz`

3. Deploy Runtime with SageMaker enabled (`enable_sagemaker_endpoint=true`, cost acknowledgement).

4. Smoke test:

```bash
curl -s https://api.minhhuy.me/health | jq
curl -s -X POST https://api.minhhuy.me/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Giá mềm nhưng giao hàng chậm"}' | jq
```

## Local test

```bash
python -c "from handler import lambda_handler; print(lambda_handler({'body':'{\"text\":\"san pham dep\"}','rawPath':'/predict'}, None))"
```

Deploy via GitHub workflow **Deploy Runtime**.
