# Pipeline Lambda

Handles training pipeline triggers, approval callbacks, and Step Functions task steps.

Environment variables are injected by Terraform (`STATE_MACHINE_ARN`, DynamoDB table names, `ARTIFACTS_BUCKET`).
