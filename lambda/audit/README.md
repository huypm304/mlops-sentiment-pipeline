# Audit Lambda

Runs dataset quality auditing before retraining.

## Triggers

- `POST /audit` via API Gateway
- Step Functions `Audit` state in the retraining workflow

## Environment

| Variable | Description |
|----------|-------------|
| `ARTIFACTS_BUCKET` | S3 bucket containing `datasets/` |

Deploy with `scripts/deploy_lambda.sh audit`.
