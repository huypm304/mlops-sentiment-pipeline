# Infrastructure — ABSA MLOps Platform

This directory contains all Terraform code for the Vietnamese ABSA MLOps demo platform on AWS.

## Architecture overview

The infrastructure is split into three independent Terraform state stacks, deployed in order:

```
bootstrap  →  core  →  runtime
```

```
bootstrap/      Terraform state bucket, state lock table, GitHub OIDC provider,
                GitHub Actions deploy role, optional AWS budget.
                Uses local backend. Applied once per AWS account. Rarely destroyed.

core/           Artifact S3 bucket (datasets, models, reports, prediction logs).
                DynamoDB registry tables for all MLOps lifecycle entities.
                Uses S3 backend from bootstrap. Resources protected by prevent_destroy.
                Never destroyed by default.

runtime/        Lambda functions, HTTP API Gateway, Step Functions pipeline,
                EventBridge schedules, CloudWatch dashboard and alarms,
                optional SageMaker endpoint. Safe to destroy after a demo.
```

```
modules/
  s3_artifacts/           Versioned, encrypted, lifecycle-managed artifact bucket.
  dynamodb_registry/      Seven DynamoDB tables for the MLOps data model.
  iam_github_oidc/        GitHub Actions OIDC provider and deploy role.
  iam_runtime/            Lambda, Step Functions, and SageMaker IAM roles.
  lambda_function/        Lambda function with zip or image packaging.
  api_gateway_http/       HTTP API Gateway with all platform routes.
  step_functions/         Training pipeline Standard Workflow + embedded ASL.
  eventbridge/            Monitoring snapshot and retrain-check schedules.
  cloudwatch/             Dashboard, Lambda error alarms, API 5xx alarm, SFN failure alarm.
  sagemaker_optional/     SageMaker model + endpoint (disabled by default).
  route53/                Hosted zone management (optional).
  acm/                    TLS certificate via DNS validation (optional).
```

---

## Prerequisites

- Terraform >= 1.5
- AWS credentials configured (or GitHub OIDC for CI/CD)
- The bootstrap stack applied at least once

---

## Deploy order

### Step 1 — Bootstrap (once per account)

```bash
cd infrastructure/terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GitHub org/repo and email

terraform init
terraform plan
terraform apply
```

After apply, note the outputs:
- `tf_state_bucket`     → backend bucket for core and runtime
- `tf_lock_table`       → DynamoDB lock table name
- `github_deploy_role_arn` → set as `AWS_ROLE_ARN` in GitHub secrets

> Bootstrap state is stored locally (`terraform.tfstate`). Keep this file safe or store it manually in the state bucket.

### Step 2 — Core (stateful resources)

```bash
cd infrastructure/terraform/core
cp terraform.tfvars.example terraform.tfvars

terraform init \
  -backend-config="bucket=absa-mlops-demo-tf-state" \
  -backend-config="key=core/terraform.tfstate" \
  -backend-config="region=ap-southeast-1" \
  -backend-config="dynamodb_table=absa-mlops-demo-tf-locks"

terraform plan
terraform apply
```

### Step 3 — Runtime (destroyable services)

```bash
cd infrastructure/terraform/runtime
cp terraform.tfvars.example terraform.tfvars
# Fill in artifact_bucket_name, table names from core outputs
# OR set core_state_bucket to read them automatically

terraform init \
  -backend-config="bucket=absa-mlops-demo-tf-state" \
  -backend-config="key=runtime/terraform.tfstate" \
  -backend-config="region=ap-southeast-1" \
  -backend-config="dynamodb_table=absa-mlops-demo-tf-locks"

terraform plan
terraform apply
```

After apply, the key outputs are:
- `api_url`                 → set as `NEXT_PUBLIC_API_URL` in the frontend
- `step_functions_arn`      → shown in the pipeline dashboard
- `cloudwatch_dashboard_url` → monitoring link

---

## Naming convention

All resources follow the pattern `${project}-${environment}-${resource}`:

```
absa-mlops-demo-artifacts         S3 artifact bucket
absa-mlops-demo-datasets          DynamoDB datasets table
absa-mlops-demo-models            DynamoDB model registry
absa-mlops-demo-predict           Lambda predict function
absa-mlops-demo-api               HTTP API Gateway
absa-mlops-demo-retrain           Step Functions state machine
absa-mlops-demo-tf-state          Terraform state bucket
```

---

## Destroy strategy

### Safe to destroy — `runtime`

```bash
cd infrastructure/terraform/runtime
terraform destroy
```

**Destroyed:** Lambda functions, API Gateway, Step Functions, EventBridge rules, CloudWatch dashboard and alarms, IAM runtime roles, optional SageMaker endpoint.

**Preserved:** All S3 artifacts (models, datasets, reports), all DynamoDB registry records, the Terraform state bucket, the GitHub OIDC provider and role.

### Preserve by default — `core`

```bash
# DANGER — This will attempt to destroy model artifacts and registry history.
# The artifact bucket is protected by prevent_destroy and will block the destroy.
# To remove core, first manually remove the lifecycle { prevent_destroy = true }
# blocks from modules/s3_artifacts/main.tf, then re-plan.

cd infrastructure/terraform/core
terraform destroy   # will FAIL at the artifact bucket unless prevent_destroy is removed
```

### Almost never — `bootstrap`

```bash
# DANGER — Destroys the Terraform state bucket (all other stacks must be destroyed first)
# and the GitHub OIDC provider (CI/CD will stop working).

cd infrastructure/terraform/bootstrap
terraform destroy
```

---

## Feature flags (runtime)

| Variable | Default | Effect |
|---|---|---|
| `enable_sagemaker_endpoint` | `false` | Create a live SageMaker inference endpoint (costly) |
| `enable_sagemaker_training` | `false` | Route training through real SageMaker jobs |
| `enable_eventbridge_monitoring` | `true` | Schedule periodic monitoring snapshots |
| `log_retention_days` | `14` | CloudWatch log retention |

The cheapest demo configuration leaves both SageMaker flags at `false` and uses mock Lambda responses for training and inference.

---

## S3 artifact prefix layout

```
datasets/pending/         Uploaded, awaiting audit
datasets/approved/        Audit passed, approved for training
datasets/rejected/        Audit failed — auto-expired after 30 days
datasets/manifests/       Dataset metadata manifests
models/v1/                Baseline production model (absa-v1)
models/candidates/        Candidate models under evaluation
models/production/        Promoted production model
models/archived/          Old production models
reports/audit/            Dataset audit reports
reports/evaluation/       Model evaluation reports
reports/calibration/      Model calibration reports
prediction-logs/raw/      Raw inference logs — tiered to IA after 14d, expired after 30d
prediction-logs/aggregated/ Aggregated monitoring data
feedback/labeled/         Human-labeled review queue items (never expired)
training-checkpoints/     Intermediate training checkpoints — expired after 7 days
temp/                     Scratch space — expired after 3 days
```

---

## DynamoDB tables

| Table | PK | SK | Purpose |
|---|---|---|---|
| `datasets` | `dataset_id` | `created_at` | Dataset lifecycle state |
| `training-runs` | `run_id` | `created_at` | Pipeline run records |
| `models` | `model_id` | `version` | Model registry |
| `predictions` | `prediction_id` | `created_at` | Inference logs |
| `monitoring-snapshots` | `snapshot_id` | `period_start` | Drift and quality snapshots |
| `approval-requests` | `approval_id` | `created_at` | Human approval callbacks |
| `review-queue` | `review_id` | `created_at` | Low-confidence predictions for review |

---

## CI/CD (GitHub Actions)

Configure repository **Variables** and **Secrets** first:

| Name | Type | Example |
|---|---|---|
| `AWS_REGION` | Variable | `ap-southeast-1` |
| `TF_STATE_BUCKET` | Variable | `absa-mlops-demo-tf-state` |
| `TF_STATE_LOCK_TABLE` | Variable | `absa-mlops-demo-tf-locks` |
| `BUDGET_ALERT_EMAIL` | Variable | your email (optional) |
| `AWS_ROLE_TO_ASSUME` | Secret | ARN from bootstrap output (or admin role for first bootstrap) |

Deploy order on GitHub:

| Workflow | Purpose |
|---|---|
| `deploy-bootstrap.yml` | Once per account — state bucket, OIDC, deploy role |
| `deploy-core.yml` | S3 artifacts + DynamoDB registry |
| `plan-runtime.yml` | Preview runtime plan + cost flags (no changes) |
| `deploy-runtime.yml` | Lambda, API, Step Functions — **SageMaker OFF by default** |
| `destroy-runtime.yml` | Remove runtime only (keeps core data) |
| `destroy-all-danger.yml` | Destroy runtime + core (artifact bucket blocked by default) |
| `pr-validate.yml` | fmt + validate on pull requests |

### Cost control on Deploy Runtime

Expensive services are **disabled by default**. When running **Deploy Runtime** on GitHub:

| Input | Default | Est. cost |
|---|---|---|
| `enable_sagemaker_endpoint` | `false` | ~$50+/month (ml.m5.large always-on) |
| `enable_sagemaker_training` | `false` | ~$1–10+ per training job |
| `enable_eventbridge_monitoring` | `true` | ~$0–1/month |
| `sagemaker_instance_type` | `ml.m5.large` | only applies when endpoint enabled |

If either SageMaker flag is `true`, you must type **`I-ACCEPT-SAGEMAKER-COST`** in `cost_acknowledgement`.

**Demo-safe defaults:** leave both SageMaker flags at `false`. Use **Plan Runtime** first to preview changes without applying.

Composite action: `.github/actions/terraform-stack/`.

Local scripts: `scripts/bootstrap_apply.sh`, `core_apply.sh`, `runtime_apply.sh`, `runtime_destroy.sh`.
