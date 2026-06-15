# AI-Powered ABSA MLOps Platform on AWS

## Overview

This project is a production-inspired AI/MLOps platform for Vietnamese Aspect-Based Sentiment Analysis (ABSA) using a serverless-first AWS architecture.

The platform focuses on:
- AI inference
- data quality auditing
- analytics
- retraining pipelines
- monitoring
- CI/CD
- Infrastructure as Code

The system is designed for:
- graduation thesis
- portfolio project
- real-world AI platform simulation

---

# System Architecture

```text
                    ┌────────────────────┐
                    │      User/Admin     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Next.js Frontend   │
                    │ (Vercel/CloudFront)│
                    └─────────┬──────────┘
                              │ HTTPS
                              ▼
                    ┌────────────────────┐
                    │   API Gateway      │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
 ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
 │ Predict Lambda │ │ Audit Lambda   │ │ Analytics Fn   │
 └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
          │                  │                  │
          ▼                  ▼                  ▼
 ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
 │ SageMaker EP   │ │ S3 Dataset     │ │ PostgreSQL RDS │
 │ ABSA Model     │ │ Audit Reports  │ │ Feedback Data  │
 └────────────────┘ └────────────────┘ └────────────────┘

                              │
                              ▼
                    ┌────────────────────┐
                    │ Step Functions     │
                    │ Retraining Flow    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ SageMaker Training │
                    └────────────────────┘
```

---

# Frontend

Tech stack:
- Next.js
- TypeScript
- TailwindCSS
- shadcn/ui
- Recharts
- Framer Motion

Pages:
1. Prediction page
2. Analytics dashboard
3. Admin dashboard
4. Monitoring dashboard

Frontend style:
- modern SaaS UI
- dark mode
- responsive
- enterprise-inspired

---

# Backend

Backend architecture:
- AWS Lambda
- Python
- FastAPI-style architecture
- modular services

Main Lambda functions:
- Predict Lambda
- Batch Predict Lambda
- Audit Lambda
- Analytics Lambda
- Retrain Trigger Lambda

---

# AI Model

Task:
Vietnamese Aspect-Based Sentiment Analysis

Architecture:
- ViBERTa encoder
- BIO tagging
- CRF decoding
- multi-task learning

Three heads:
1. Aspect extraction
2. Sentiment classification
3. Global sentiment

Frameworks:
- PyTorch
- HuggingFace Transformers

---

# Dataset Pipeline

Pipeline:

Raw Data
→ Normalize
→ Audit
→ Clean
→ Split
→ Train
→ Evaluate

Audit features:
- BIO validation
- span offset validation
- polarity consistency
- contradiction collapse
- duplicate semantic opinions
- weak targets
- global consistency

---

# Retraining Pipeline

AWS Step Functions workflow:

Upload Dataset
→ Audit Dataset
→ Clean Dataset
→ Train Model
→ Evaluate Model
→ Generate Metrics
→ Register Model
→ Deploy Endpoint

Artifacts:
- best_model.pt
- metrics.json
- confusion_matrix.png
- training_curves.png

---

# Storage Layer

Amazon S3 buckets:
- datasets bucket
- models bucket
- reports bucket

PostgreSQL RDS:
- inference history
- feedback data
- analytics metadata
- model versions

---

# Monitoring

CloudWatch monitoring:
- Lambda logs
- API metrics
- inference latency
- error rates
- model confidence
- retraining logs

---

# CI/CD

GitHub Actions workflows:

Frontend:
- build
- lint
- deploy

Backend:
- test
- package
- deploy lambda

Terraform:
- terraform fmt
- terraform validate
- terraform plan
- terraform apply
- terraform destroy

---

# Infrastructure as Code

Terraform modules:
- Lambda
- API Gateway
- S3
- IAM
- SageMaker
- Step Functions
- CloudWatch
- Route53
- ACM

---

# Repository Structure

```text
absa-mlops-platform/
│
├── frontend/
├── backend/
├── lambda/
├── training/
├── model/
├── infrastructure/
│   └── terraform/
│       ├── bootstrap/
│       ├── core/
│       ├── runtime/
│       └── modules/
├── scripts/
├── docs/
└── .github/workflows/
```

---

# Architecture Principles

The project follows:
- cloud-native design
- serverless-first architecture
- event-driven workflow
- production-inspired MLOps
- maintainable structure
- scalable modularity

Avoid:
- Kubernetes/EKS
- Kafka
- unnecessary complexity
- overengineering

---

# Development Roadmap

Phase 1:
- local inference
- frontend MVP

Phase 2:
- Lambda deployment
- API Gateway
- SageMaker endpoint

Phase 3:
- analytics dashboard
- admin dashboard

Phase 4:
- Terraform
- CI/CD

Phase 5:
- monitoring

Phase 6:
- retraining pipeline