# Analytics Lambda

Serves aggregated metrics for the analytics dashboard.

## Route

- `GET /analytics/summary`

## Environment

| Variable | Description |
|----------|-------------|
| `ARTIFACTS_BUCKET` | S3 bucket (reports, evaluation prefixes) |

Deploy with `scripts/deploy_lambda.sh analytics`.
