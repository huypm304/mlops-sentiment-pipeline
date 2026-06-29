# AI-Powered ABSA MLOps Platform

Nền tảng MLOps production-inspired cho **Phân tích cảm xúc theo khía cạnh tiếng Việt (Vietnamese ABSA)** — kiến trúc **cloud-native, serverless-first** trên AWS, phù hợp luận văn tốt nghiệp và portfolio kỹ sư ML/AI.

---

## Mục tiêu hệ thống

| Khả năng | Mô tả ngắn |
|----------|------------|
| **Suy luận AI** | Trích xuất aspect/target, sentiment từng ý kiến và sentiment tổng thể |
| **Kiểm định dataset** | Audit chất lượng JSONL (BIO, span, polarity, trùng lặp, global consistency) |
| **Dashboard phân tích** | Biểu đồ, metrics huấn luyện, confusion matrix |
| **Pipeline tái huấn luyện** | Step Functions: Upload → Audit → Train → Evaluate → Compare → Register → Promote → Deploy |
| **Giám sát** | Runtime API, drift so với baseline train, inference log |
| **IaC & CI/CD** | Terraform module hóa; GitHub Actions plan/apply/destroy |

**Nguyên tắc:** serverless AWS, không Kubernetes/Kafka; một engineer có thể triển khai và demo được.

---

## Kiến trúc tổng quan

```text
                    ┌────────────────────┐
                    │   User / Admin     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  Next.js Frontend  │
                    │  (S3 + CloudFront) │
                    └─────────┬──────────┘
                              │ HTTPS
                              ▼
                    ┌────────────────────┐
                    │   API Gateway      │
                    │   (HTTP API)       │
                    └─────────┬──────────┘
              ┌───────────────┼───────────────┬──────────────┐
              ▼               ▼               ▼              ▼
         Predict          Audit          Pipeline       Metrics
          Lambda          Lambda          Lambda         Lambda
              │               │               │              │
              ▼               ▼               ▼              ▼
         SageMaker         S3            Step Functions   DynamoDB
         (optional)    datasets/         Retrain           + S3
                       models/           Pipeline
                       reports/              │
                                             ▼
                                    SageMaker Training Job
                                    (ml.g4dn.xlarge, T4 GPU)
```

Chi tiết: [`docs/architecture.md`](docs/architecture.md) · Terraform: [`infra/README.md`](infra/README.md)

---

## Công nghệ

| Lớp | Stack |
|-----|--------|
| **Frontend** | Next.js App Router (static export), TypeScript, TailwindCSS, shadcn/ui |
| **API** | API Gateway HTTP API → Lambda |
| **Orchestration** | Step Functions Standard Workflow |
| **Training** | SageMaker Training (`ml.g4dn.xlarge`, T4) hoặc mock copy baseline |
| **Storage** | S3 artifacts + DynamoDB registry |
| **IaC** | Terraform (`infra/bootstrap`, `core`, `runtime`) |
| **CI/CD** | GitHub Actions |
| **ML** | PyTorch, HuggingFace Transformers, **PhoBERT** (`vinai/phobert-base`), CRF, multi-task |

---

## Cấu trúc repository

```text
mlops-sentiment-pipeline/
│
├── apps/
│   ├── frontend/                 # Console Next.js (training runs, pipeline, datasets, …)
│   │   ├── app/                  # App Router pages
│   │   ├── components/           # UI + pipeline stage stepper, training config form
│   │   ├── lib/api/              # Client gọi API Gateway
│   │   └── types/                # pipeline.ts, dataset types, …
│   │
│   └── backend/
│       ├── lambda/
│       │   ├── predict/          # POST /predict, GET /health
│       │   ├── audit/            # Dataset audit + presign upload
│       │   ├── pipeline/         # Step Functions tasks + POST /pipeline/trigger
│       │   └── metrics/          # Monitoring, drift, review queue
│       └── registry/             # DynamoDB + S3 helpers (models, runs, artifacts)
│
├── ml/
│   ├── training/
│   │   ├── train_kaggle.py       # Script train chính (50 epoch, PhoBERT)
│   │   ├── sagemaker_train.py    # Entry point SageMaker → gọi train_kaggle
│   │   └── train_legacy.py       # Bản legacy (tham khảo)
│   ├── inference/                # ABSAModel, inference, evaluation (SageMaker package)
│   ├── configs/                  # run_config.json, requirements.txt
│   └── data_processing/          # Chuẩn hóa / benchmark dataset
│
├── infra/
│   ├── bootstrap/                # TF state bucket + lock
│   ├── core/                     # S3 artifacts + DynamoDB tables
│   ├── runtime/                  # Lambda, API GW, Step Functions, optional SageMaker endpoint
│   └── modules/                  # Terraform modules
│
├── scripts/
│   ├── build_training_package.sh # Đóng gói train_kaggle → source.tar.gz lên S3
│   ├── enable_real_training.sh   # Upload package + checklist bật SageMaker training
│   ├── prepare_lambda_bundles.sh # Bundle Lambda trước terraform apply
│   ├── upload_model.sh           # Upload baseline models/v1/
│   ├── upload_dataset.sh
│   ├── seed_registry.py          # Seed production model metrics vào DynamoDB
│   ├── eval_model.py
│   └── demo_e2e_pipeline.sh      # Trigger + poll pipeline qua API
│
├── tests/                        # pytest (pipeline, artifacts, audit, …)
├── docs/                         # architecture.md, data-management.md
└── .github/workflows/            # deploy-bootstrap/core/runtime, plan, destroy
```

---

## Mô hình AI (ABSA)

**Nhiệm vụ:** Từ một câu đánh giá tiếng Việt:

1. **Aspect extraction** — BIO tagging + CRF decode (`Fashion`, `Price`, `Service`, …)
2. **Sentiment theo opinion** — Negative / Positive / Neutral (0/1/2)
3. **Global sentiment** — Cảm xúc tổng thể câu

**Encoder:** `vinai/phobert-base` (PhoBERT)

**Artifact chính:** `best_model.pt`, `run_config.json`, `train_log.csv`, `best_confusion_matrices.json`

**Inference code:** `ml/inference/` (đóng gói cùng SageMaker training source)

---

## Training

### Local / Kaggle

```bash
python ml/training/train_kaggle.py \
  --train-file /path/to/train.jsonl \
  --val-file   /path/to/dev.jsonl \
  --output-dir ./model \
  --epochs 50 \
  --batch-size 24 \
  --lambda-cons 0.03 \
  --lambda-contrast 0.1
```

Hyperparameter mặc định pipeline (UI + Lambda): `apps/backend/lambda/pipeline/default_training_config.json`

| Tham số quan trọng | Giá trị mặc định |
|--------------------|------------------|
| `epochs` | 50 |
| `patience` | 8 |
| `batch_size` | 24 |
| `lr_backbone` / `lr_heads` | 8e-6 / 3e-5 |
| `lambda_bio` / `lambda_sent` / `lambda_global` | 1.1 / 1.4 / 0.2 |
| `lambda_cons` / `lambda_contrast` | 0.03 / 0.1 |
| `sagemaker_instance_type` | `ml.g4dn.xlarge` (T4 GPU) |

### SageMaker (train thật trên AWS)

1. Đóng gói & upload source:

```bash
export ARTIFACTS_BUCKET=absa-mlops-demo-artifacts
./scripts/build_training_package.sh
# → s3://$ARTIFACTS_BUCKET/training/source/source.tar.gz
```

2. Deploy Runtime với `enable_sagemaker_training=true` (GitHub Actions **Deploy Runtime**).

3. Dataset trên S3 cần **cả hai file** trong cùng prefix:
   - `datasets/pending/<dataset_id>/train.jsonl`
   - `datasets/pending/<dataset_id>/dev.jsonl`

4. Trigger từ console (**New training run**) hoặc `POST /pipeline/trigger`.

**Thời gian:** ~3–4 giờ wall-clock trên `ml.g4dn.xlarge` (tương đương Kaggle T4).

### Mock training (demo nhanh)

Khi `ENABLE_SAGEMAKER_TRAINING=false` (Lambda env):

- Không tạo SageMaker job
- Copy artifact production `models/v1/` → `training-runs/{run_id}/`
- Pipeline chạy Evaluate → Compare → … trong vài giây
- Dùng để demo Step Functions / UI, **không** tạo model mới

Kiểm tra mode:

```bash
curl -s https://api.minhhuy.me/pipeline/config | jq '.training_mode, .sagemaker_training_enabled'
# "sagemaker" / true  → train thật
# "mock" / false      → giả lập
```

---

## Pipeline tái huấn luyện (Step Functions)

Định nghĩa: [`infra/modules/step_functions/training_pipeline.asl.json`](infra/modules/step_functions/training_pipeline.asl.json)

```text
StartTraining
  → CheckTrainingStatus  (poll SageMaker, mỗi 60s)
  → WaitForTraining      (lặp đến Completed)
  → EvaluateCandidate    (parse train_log.csv trên S3)
  → CompareToProduction  (candidate vs production baseline)
  → RegisterCandidate
  → PromoteGate          (tas_relaxed_f1 >= baseline?)
       ├─ promote=true  → SmokeTest → PromoteModel → DeployModel → COMPLETED
       └─ promote=false → REJECTED (train xong nhưng không lên production)
```

**Lineage mỗi run:** `code_version`, `training_source_uri`, `dataset_id`, `training_config` (lưu DynamoDB + hiển thị UI).

**Sau Deploy:** artifact candidate được copy vào `models/v1/` (S3). Cập nhật SageMaker **inference endpoint** cần redeploy runtime với `model_package_version` mới (endpoint tắt mặc định).

---

## Evaluation (local)

```bash
python scripts/eval_model.py \
  --model-path path/to/best_model.pt \
  --model-name vinai/phobert-base \
  --eval-file  path/to/dev.jsonl \
  --output-dir ./eval_out \
  --strict-load true
```

---

## Dataset schema

```jsonc
{
  "text": "Giá mềm, chất vải mát.",
  "opinions": [
    {
      "target": "Giá",
      "aspect": "Price",
      "sentiment": 1,
      "start": 0,
      "end": 3
    }
  ],
  "global_sentiment": 1
}
```

---

## Lambda (AWS)

| Function | Vai trò |
|----------|---------|
| **predict** | `POST /predict`, `GET /health` — SageMaker endpoint hoặc stub |
| **audit** | Audit S3 JSONL; presign upload `train.jsonl` + `dev.jsonl` |
| **pipeline** | Step Functions tasks; `POST /pipeline/trigger`, `GET /pipeline/runs`, cancel run |
| **metrics** | Monitoring snapshots, drift, review queue |

Bundle trước deploy: `./scripts/prepare_lambda_bundles.sh` (CI chạy tự động qua `build_audit_lambda.sh`).

---

## Frontend

| Route | Mục đích |
|-------|----------|
| `/training-runs` | Danh sách + chi tiết run (metrics, comparison, lineage) |
| `/datasets` | Upload / audit dataset |
| `/admin/pipeline` | Trigger pipeline + config form |
| `/prediction`, `/analytics`, `/monitoring` | Demo sản phẩm |
| `/admin/models`, `/admin/evaluation` | Registry, so sánh model |

Cấu hình: `apps/frontend/.env.local` — `NEXT_PUBLIC_API_URL=https://api.minhhuy.me`

---

## Hạ tầng Terraform

| Stack | Thư mục | Nội dung |
|-------|---------|----------|
| Bootstrap | `infra/bootstrap/` | S3 state, DynamoDB lock |
| Core | `infra/core/` | S3 artifacts, DynamoDB registry |
| Runtime | `infra/runtime/` | Lambda, API GW, Step Functions, optional SageMaker endpoint |

Feature flags runtime (`infra/runtime/terraform.tfvars.example`):

| Biến | Mặc định example | Ý nghĩa |
|------|------------------|---------|
| `enable_sagemaker_training` | `true` | Train thật qua SageMaker (tắt = mock) |
| `enable_sagemaker_endpoint` | `false` | Inference endpoint (tốn phí) |
| `sagemaker_instance_type` | `ml.m5.large` | Chỉ cho **endpoint**; training dùng `ml.g4dn.xlarge` từ training config |

Chi tiết: [`infra/README.md`](infra/README.md)

---

## CI/CD (GitHub Actions)

| Workflow | Mục đích |
|----------|----------|
| `deploy-bootstrap.yml` | Bootstrap (1 lần/account) |
| `deploy-core.yml` | S3 + DynamoDB |
| `plan-runtime.yml` | Terraform plan |
| `deploy-runtime.yml` | Deploy runtime; upload training source nếu `enable_sagemaker_training=true` |
| `deploy-frontend.yml` | Build static Next.js → S3/CloudFront |
| `destroy-runtime.yml` | Hủy runtime (giữ core data) |

**Deploy Runtime** (workflow_dispatch):

- `enable_sagemaker_training`: mặc định **true** — bật train GPU thật
- `enable_sagemaker_endpoint`: mặc định **false** — tránh chi phí endpoint

Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

---

## Triển khai AWS (checklist)

1. **Deploy Bootstrap** → **Deploy Core**
2. Upload baseline model: `./scripts/upload_model.sh <local-dir> models/v1`
3. Seed registry: `python scripts/seed_registry.py --model-id absa-v2b`
4. **Deploy Runtime** với `enable_sagemaker_training=true`
5. `./scripts/build_training_package.sh` (hoặc để CI upload khi deploy)
6. **Deploy Frontend**
7. Upload dataset (`train.jsonl` + `dev.jsonl`) qua UI Datasets
8. Trigger training từ console; theo dõi SageMaker Training Jobs + Step Functions execution

Demo nhanh (mock): `./scripts/demo_e2e_pipeline.sh` với `API_URL` + `DATASET_ID`.

---

## SageMaker inference (optional)

```bash
./scripts/package_sagemaker_model.sh --upload --bucket absa-mlops-demo-artifacts
```

Deploy Runtime với `enable_sagemaker_endpoint=true` + `model_package_version` bump.

---

## Troubleshooting pipeline

| Triệu chứng | Nguyên nhân thường gặp |
|-------------|------------------------|
| Run **REJECTED** ngay, Best F1 = 0 | Mock mode + metric gate; hoặc candidate < production baseline |
| Run **FAILED** sau SageMaker Completed | Sync `model.tar.gz` → `training-runs/` (Lambda memory / SFN 120s timeout) |
| Không có SageMaker job | `ENABLE_SAGEMAKER_TRAINING=false` — vẫn mock |
| Evaluate fail | Thiếu `train_log.csv` tại `training-runs/{run_id}/` |
| Train job fail sớm | Thiếu `dev.jsonl` trên S3 channel |

---

## Known limitations

- Weak on implicit opinions and sarcasm
- Model trained on Vietnamese e-commerce; domain khác cần retrain
- Deploy pipeline chỉ cập nhật S3 `models/v1/`; endpoint inference cần redeploy riêng
- Confidence threshold + review queue khuyến nghị cho production

---

## Tài liệu liên quan

- [`infra/README.md`](infra/README.md) — Terraform stacks & feature flags
- [`docs/architecture.md`](docs/architecture.md) — kiến trúc chi tiết
- [`docs/data-management.md`](docs/data-management.md) — dataset versioning, S3 publish
- [`apps/backend/lambda/audit/README.md`](apps/backend/lambda/audit/README.md) — quy tắc audit

---

## License & ghi chú

Dự án **portfolio / luận văn**. Predict Lambda có thể chạy stub khi SageMaker endpoint tắt. Training mock phù hợp demo UI; training thesis/production cần `enable_sagemaker_training=true` và dataset đủ `train` + `dev` trên S3.
