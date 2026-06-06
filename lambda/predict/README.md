# Predict Lambda

HTTP API handler for Vietnamese ABSA inference.

## Routes (via API Gateway)

- `POST /predict` — run inference on review text
- `GET /health` — readiness probe

## Environment

| Variable | Description |
|----------|-------------|
| `ARTIFACTS_BUCKET` | S3 bucket for model artifacts |
| `SAGEMAKER_ENDPOINT_NAME` | Optional SageMaker endpoint |

## Local test

```bash
python -c "from handler import lambda_handler; print(lambda_handler({'body':'{\"text\":\"san pham dep\"}','rawPath':'/predict'}, None))"
```

Deploy via Terraform runtime stack (`./scripts/runtime_apply.sh`) or GitHub workflow **Deploy Runtime**.
