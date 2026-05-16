# Retrain Trigger Lambda

Starts the Step Functions retraining pipeline.

## Route

- `POST /retrain` — body: `{ "dataset_key": "datasets/raw/my.jsonl" }`

## Environment

| Variable | Description |
|----------|-------------|
| `RETRAIN_STATE_MACHINE_ARN` | Step Functions state machine ARN |
| `ARTIFACTS_BUCKET` | S3 artifacts bucket |

## Workflow

Upload → Audit → Clean → Train → Evaluate → Register → Deploy

See `infrastructure/step-functions/retrain-pipeline.asl.json`.

Deploy with `scripts/deploy_lambda.sh retrain_trigger`.
