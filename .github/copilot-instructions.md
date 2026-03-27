# Project Context for AI Agent / GitHub Copilot

## 1. Project Overview
- **Project Name:** Design and Implementation of an Automated MLOps System for Customer Sentiment Analysis on AWS.
- **Goal:** Build a fully automated MLOps pipeline for continuous training and deployment of a Vietnamese Sentiment Analysis model.
- **Core ML Approach:** Fine-tuning the State-of-the-Art Vietnamese Transformer model (**ViDeBERTa**) for Sequence Classification to handle complex semantics, idioms, and customer slang.
- **Target Audience:** Enterprise systems needing automated, scalable, and low-latency feedback analysis.

## 2. Tech Stack & Infrastructure
- **Machine Learning:** Python 3.12, PyTorch, Hugging Face `transformers`, `scikit-learn`.
- **Cloud Provider:** Amazon Web Services (AWS).
- **MLOps Services:** - Model Training: AWS SageMaker.
  - Workflow Orchestration: AWS Step Functions.
  - Event Triggers: AWS Lambda, Amazon S3.
  - Model Registry: AWS SageMaker Model Registry / S3.
- **Deployment & API:** Amazon API Gateway, AWS Lambda (Serverless Inference), Amazon DynamoDB (Metadata & Feedback loop).
- **DevOps & IaC:** Docker (Containerization), Terraform (Infrastructure setup), GitHub Actions (CI/CD).

## 3. Architecture & Workflows

### 3.1. Automated Training Pipeline (Continuous Training)
1. **Data Ingestion:** New customer feedback data is uploaded to a specific S3 bucket.
2. **Trigger:** An AWS Lambda function detects the S3 upload and evaluates retraining conditions (e.g., data drift, new row count > threshold).
3. **Orchestration:** If conditions are met, Lambda triggers an AWS Step Functions state machine.
4. **Training Job:** Step Functions launches a SageMaker Training Job to fine-tune the ViDeBERTa model.
5. **Evaluation & Registry:** The model is evaluated. If the F1-Score improves compared to the previous version, the new artifact (`model.tar.gz`) is saved to S3 and registered in the Model Registry.

### 3.2. Real-time Inference Pipeline
1. **Client Request:** User sends a text payload to API Gateway.
2. **Processing:** API Gateway routes the request to an Inference Lambda function (or SageMaker Endpoint).
3. **Prediction:** The model processes the text and returns a Sentiment label (Positive/Negative) and a Confidence Score.
4. **Storage:** The result and the original text are logged into DynamoDB for future monitoring and Human-in-the-loop validation.

## 4. Recommended Folder Structure
Please follow this standard MLOps directory structure when generating or modifying files:

```text
├── .github/workflows/   # CI/CD pipelines (GitHub Actions)
├── data/                # Local data testing (ignored in git)
├── infrastructure/      # Terraform scripts for AWS resources
├── model/               # ML logic
│   ├── preprocess.py    # Text cleaning and tokenization
│   ├── train.py         # ViDeBERTa fine-tuning script
│   └── evaluate.py      # Model scoring and validation
├── deployment/          # Inference & API logic
│   ├── inference.py     # Lambda handler for real-time predictions
│   └── Dockerfile       # Container setup for SageMaker/Lambda
├── tests/               # Unit and integration tests
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation