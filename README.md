# AI-Powered ABSA MLOps Platform

Nền tảng MLOps production-inspired cho **Phân tích cảm xúc theo khía cạnh tiếng Việt (Vietnamese ABSA)** — kiến trúc **cloud-native, serverless-first** trên AWS, phù hợp luận văn tốt nghiệp và portfolio kỹ sư ML/AI.

---

## Mục tiêu hệ thống

| Khả năng | Mô tả ngắn |
|----------|------------|
| **Suy luận AI** | Trích xuất aspect/target, sentiment từng ý kiến và sentiment tổng thể |
| **Kiểm định dataset** | Audit chất lượng JSONL (BIO, span, polarity, trùng lặp, global consistency) |
| **Dashboard phân tích** | Biểu đồ, metrics huấn luyện, confusion matrix |
| **Pipeline tái huấn luyện** | Step Functions: Upload → Audit → Clean → Train → Evaluate → Register → Deploy |
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
                    │  (local / Vercel)  │
                    └─────────┬──────────┘
                              │ HTTPS
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌────────────────────┐          ┌────────────────────┐
    │ FastAPI (local dev)│          │   API Gateway      │
    └─────────┬──────────┘          └─────────┬──────────┘
              │                               │
              │                   ┌───────────┼───────────┐
              │                   ▼           ▼           ▼
              │            Predict      Audit    Retrain-trigger
              │            Lambda       Lambda   Lambda
              │                   │           │           │
              └───────────────────┼───────────┼───────────┘
                                  ▼           ▼
                         ┌────────────┐  ┌────────────┐
                         │ SageMaker  │  │ S3 Reports │
                         │ Endpoint   │  │ Datasets   │
                         └────────────┘  └────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │  Step Functions    │
                         │  Retrain Pipeline  │
                         └────────────────────┘
```

Chi tiết kiến trúc: [`docs/architecture.md`](docs/architecture.md).

---

## Công nghệ

| Lớp | Stack |
|-----|--------|
| **Frontend** | Next.js App Router, TypeScript, TailwindCSS, shadcn/ui, Recharts, Framer Motion |
| **Backend (dev)** | Python, FastAPI, Uvicorn |
| **Serverless** | AWS Lambda, API Gateway, Step Functions, SageMaker, S3, CloudWatch |
| **IaC** | Terraform (modules: lambda, api_gateway, s3, iam, sagemaker, step_functions, cloudwatch, route53, acm) |
| **CI/CD** | GitHub Actions (terraform plan/apply/destroy, PR validation) |
| **ML** | PyTorch, HuggingFace Transformers, ViBERTa, CRF, multi-task learning |

---

## Cấu trúc repository

```text
mlops-sentiment-pipeline/
│
├── frontend/                 # Dashboard Next.js (SaaS-style, dark mode)
│   ├── app/
│   │   ├── prediction/       # Trang dự đoán ABSA
│   │   ├── analytics/        # Dashboard phân tích
│   │   ├── monitoring/       # Giám sán inference & drift
│   │   ├── (customer)/         # Reviews, Insights (giao diện end-user)
│   │   └── (admin)/admin/    # Admin: audit, pipeline, models, evaluation, …
│   ├── components/           # UI theo domain (prediction, admin, charts, …)
│   ├── lib/api/              # Client gọi FastAPI / API Gateway
│   └── types/                # TypeScript types (audit, pipeline, …)
│
├── backend/                  # API FastAPI cho phát triển local & admin
│   └── app/
│       ├── routes/           # predict, audit, pipeline, metrics
│       ├── services/         # inference, audit, drift, pipeline, metrics, runtime
│       ├── schemas/          # Pydantic request/response
│       └── config/           # MODEL_DIR, CORS, Step Functions ARN, …
│
├── model/                    # Mã nguồn & artifact mô hình ABSA
│   ├── train.py              # Huấn luyện multi-task (BIO + sentiment + global)
│   ├── inference.py          # Load checkpoint, predict một câu
│   ├── postprocess.py        # Hậu xử lý span/opinion
│   ├── config.json           # Hyperparameters & postprocess config
│   ├── best_model.pt         # Checkpoint (cần có khi chạy inference)
│   └── *.jsonl               # Dữ liệu train/demo mẫu
│
├── train/                    # Notebook/script huấn luyện phiên bản Kaggle (legacy)
│
├── lambda/                   # Handlers triển khai AWS
│   ├── predict/              # Inference API
│   ├── audit/                # Dataset audit + presign upload
│   │   └── dataset_audit/    # Engine: validators, benchmarks, engine
│   ├── pipeline/             # Training pipeline trigger + Step Functions tasks
│   └── metrics/              # Monitoring, drift, review queue
│
├── infrastructure/
│   ├── terraform/
│   │   ├── bootstrap/        # State bucket, lock table, budget
│   │   ├── core/             # S3 artifacts, DynamoDB registry
│   │   ├── runtime/          # Lambda, API, Step Functions, CloudWatch
│   │   └── modules/
│   └── README.md
│
├── scripts/                  # bootstrap/core/runtime apply, upload S3, DNS
├── reports/                  # Audit JSON & inference log (local, gitignored một phần)
├── docs/                     # Tài liệu kiến trúc
└── .github/workflows/        # deploy-bootstrap/core/runtime, destroy, pr-validate
```

---

## Mô hình AI (ABSA)

**Nhiệm vụ:** Từ một câu đánh giá tiếng Việt, hệ thống trả về:

1. **Aspect extraction** — BIO tagging + CRF decode (Fashion, Price, Service, …)
2. **Sentiment theo opinion** — Negative / Positive / Neutral (0/1/2)
3. **Global sentiment** — Cảm xúc tổng thể câu

**Kiến trúc:** Encoder `Fsoft-AIC/videberta-base`, multi-task heads, hậu xử lý span trong `model/postprocess.py`.

**Artifact chính:** `model/best_model.pt`, `model/config.json`, `model/train_log.csv`, `model/confusion_matrices.jsonl`.

---

## Backend API (FastAPI — local)

Chạy từ repo root (model được load lúc startup):

| Endpoint | Chức năng |
|----------|-----------|
| `POST /predict` | Suy luận ABSA; ghi inference log & drift |
| `GET /health` | Trạng thái model + runtime stats |
| `POST /audit/run` | Chạy audit trên dataset (`train`, `demo`, hoặc path) |
| `GET /audit/reports` | Danh sách báo cáo audit |
| `GET /audit/reports/{id}` | Chi tiết báo cáo |
| `GET /metrics/models` | Danh sách phiên bản model |
| `GET /metrics/models/{version}` | Evaluation, confusion matrix |
| `GET /metrics/training/history` | Lịch sử epoch từ `train_log.csv` |
| `GET /metrics/monitoring` | Runtime + báo cáo drift |
| `GET /pipeline/config` | Cấu hình Step Functions (hoặc demo mode) |
| `GET /pipeline/runs` | Lịch sử execution |
| `POST /pipeline/trigger` | Kích hoạt pipeline retrain |

Biến môi trường quan trọng (`backend/app/config/settings.py`):

- `ABSA_MODEL_DIR` — thư mục chứa `best_model.pt` (mặc định: `model/`)
- `RETRAIN_STATE_MACHINE_ARN`, `ARTIFACTS_BUCKET` — kết nối AWS thật
- `PIPELINE_DEMO_MODE` — mô phỏng pipeline khi chưa có Step Functions

---

## Lambda (AWS)

| Function | Vai trò |
|----------|---------|
| **predict** | `POST /predict`, `GET /health` qua API Gateway; nhắm SageMaker endpoint |
| **audit** | Audit file trên S3; báo cáo `reports/audit/`; tích hợp Step Functions stage Audit |
| **analytics** | Scaffold analytics serverless |
| **retrain-trigger** | Start execution Step Functions retrain |

Engine audit dùng chung giữa Lambda và backend: `lambda/audit/dataset_audit/`.

---

## Frontend

| Route | Mục đích |
|-------|----------|
| `/prediction` | Nhập văn bản, xem opinions + global sentiment |
| `/analytics` | Metrics huấn luyện, biểu đồ |
| `/monitoring` | Latency, errors, drift |
| `/reviews`, `/insights` | Luồng customer (demo sản phẩm) |
| `/admin` | Trang quản trị tổng |
| `/admin/audit` | Dashboard kiểm định dataset |
| `/admin/pipeline` | Theo dõi & trigger pipeline retrain |
| `/admin/monitoring` | Ops view cho admin |
| `/admin/models`, `/admin/evaluation`, … | Phiên bản model, so sánh, triển khai |

Cấu hình: `frontend/.env.local` — `NEXT_PUBLIC_API_URL=http://localhost:8000` (xem `.env.local.example`).

---

## Pipeline dữ liệu & tái huấn luyện

**Luồng dữ liệu:**

```text
Raw JSONL → Normalize → Audit → Clean → Split → Train → Evaluate
```

**Audit kiểm tra:** parse JSONL, span offset, schema aspect, polarity, duplicate opinions, global consistency (xem `lambda/audit/README.md`).

**Step Functions** (`infrastructure/terraform/modules/step_functions/training_pipeline.asl.json`):

`ValidateDataset → EstimateCost → CheckApproval → StartTraining → Evaluate → Calibrate → Compare → Gate → Register → SmokeTest → Promote/Reject → Notify`

Báo cáo audit local lưu tại `reports/audit/`; inference log tại `reports/monitoring/inference_log.jsonl`.

---

## Hạ tầng Terraform

Kiến trúc mới tách thành 3 stack độc lập (một môi trường `demo`):

| Stack | Thư mục | Nội dung |
|---|---|---|
| Bootstrap | `infrastructure/terraform/bootstrap/` | S3 state, DynamoDB lock |
| Core | `infrastructure/terraform/core/` | S3 artifacts, DynamoDB registry |
| Runtime | `infrastructure/terraform/runtime/` | Lambda, API Gateway, Step Functions, CloudWatch |

Chi tiết: [`infrastructure/README.md`](infrastructure/README.md)

Scripts:

```bash
./scripts/bootstrap_apply.sh   # once per account
./scripts/core_apply.sh
./scripts/runtime_apply.sh
./scripts/runtime_destroy.sh     # safe — keeps core data
./scripts/upload_model.sh
./scripts/upload_dataset.sh
```

---

## CI/CD (GitHub Actions)

| Workflow | Mục đích |
|----------|----------|
| `pr-validate.yml` | Validate Terraform + frontend trên PR |
| `deploy-bootstrap.yml` | Bootstrap (1 lần/account) |
| `deploy-core.yml` | Deploy core/stateful |
| `plan-runtime.yml` | Xem plan + cost flags (không apply) |
| `deploy-runtime.yml` | Deploy runtime — SageMaker **tắt mặc định** |
| `destroy-runtime.yml` | Hủy runtime (giữ artifacts + registry) |
| `destroy-all-danger.yml` | Hủy runtime + core (nguy hiểm) |

**Kiểm soát chi phí khi Deploy Runtime:**

- `enable_sagemaker_endpoint` = `false` (mặc định) — tránh ~$50+/tháng
- `enable_sagemaker_training` = `false` (mặc định) — tránh ~$1–10+/job
- Bật SageMaker → phải gõ `I-ACCEPT-SAGEMAKER-COST` vào `cost_acknowledgement`
- Dùng **Plan Runtime** trước khi apply để xem thay đổi

Cần cấu hình GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`  
Variables: `AWS_REGION`, `TF_STATE_BUCKET`, `TF_STATE_LOCK_TABLE`

---

## Chạy local (nhanh)

### 1. Backend + model

```bash
cd /path/to/mlops-sentiment-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# Đảm bảo model/best_model.pt tồn tại
python -m backend.app.main
# API: http://localhost:8000 — docs: /docs
```

### 2. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# http://localhost:3000
```

### 3. Audit engine (không cần API)

```bash
PYTHONPATH=lambda/audit python3 -c "
from dataset_audit import run_dataset_audit
from pathlib import Path
print(run_dataset_audit(Path('model/demo_10.jsonl'))['passed'])
"
```

---

## Triển khai AWS (tóm tắt)

1. Tạo IAM user + access key trên AWS
2. Cấu hình GitHub Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) và Variables
3. Chạy workflow **Deploy Bootstrap**
4. Chạy **Deploy Core**
5. Chạy **Deploy Runtime**
6. Upload model baseline: `./scripts/upload_model.sh model models/v1`
7. Trỏ frontend `NEXT_PUBLIC_API_URL` tới `api_url` output

---

## Báo cáo & artifact

| Đường dẫn | Nội dung |
|-----------|----------|
| `reports/audit/*.json` | Kết quả audit từng lần chạy |
| `reports/monitoring/inference_log.jsonl` | Log suy luận phục vụ drift |
| `model/train_log.csv` | Metric theo epoch |
| `model/confusion_matrices.jsonl` | Ma trận nhầm lẫn theo epoch |

---

## Roadmap phát triển

| Phase | Nội dung |
|-------|----------|
| 1 | Inference local + frontend MVP |
| 2 | Lambda + API Gateway + SageMaker endpoint |
| 3 | Analytics & admin dashboard |
| 4 | Terraform + CI/CD |
| 5 | Monitoring & drift |
| 6 | Pipeline retrain end-to-end trên AWS |

---

## Tài liệu liên quan

- [`docs/architecture.md`](docs/architecture.md) — kiến trúc chi tiết (tiếng Anh)
- [`lambda/audit/README.md`](lambda/audit/README.md) — quy tắc audit dataset
- [`.cursorrules`](.cursorrules) — quy ước dự án cho AI/dev

---

## License & ghi chú

Dự án mang tính **portfolio / luận văn**: một số Lambda (predict, analytics) là **scaffold** — cần nối SageMaker Runtime hoặc package inference trước khi production. Backend FastAPI và `model/inference.py` hỗ trợ demo đầy đủ trên máy local khi có `best_model.pt`.
