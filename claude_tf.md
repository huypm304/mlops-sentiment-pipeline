# TERRAFORM INFRASTRUCTURE SPECIFICATION (AWS)
You are a Cloud Architect & DevOps Engineer. I need to provision the infrastructure for my ABSA (Aspect-Based Sentiment Analysis) system on AWS using Terraform.

## 1. TARGET ARCHITECTURE
The infrastructure must support:
- **ML Layer:** S3 Bucket for artifacts, IAM Roles for SageMaker, and a SageMaker Real-time Endpoint.
- **App Layer:** An EC2 Instance (t3.medium or larger) to host Dockerized Next.js & FastAPI.
- **Database Layer:** (Optional) RDS PostgreSQL or a Dockerized DB on EC2. Let's start with Dockerized DB on EC2 for cost-saving, but keep VPC security groups ready.
- **Security:** VPC, Public/Private Subnets, Security Groups for HTTP (80), HTTPS (443), and FastAPI (8000).

## 2. TERRAFORM RESOURCE REQUIREMENTS

### A. Networking & Security
- VPC with Public Subnets.
- Security Group for EC2: Allow Port 22 (SSH), 80/443 (Web), 8000 (API).
- Security Group for SageMaker: Allow communication from EC2.

### B. Machine Learning (SageMaker)
- **S3 Bucket:** Create a bucket named `absa-model-artifacts-[random-suffix]`.
- **IAM Role:** A SageMaker Execution Role with `AmazonS3FullAccess` and `AmazonSageMakerFullAccess`.
- **SageMaker Model:** Pointing to the `model.tar.gz` in S3.
- **SageMaker Endpoint Config:** Instance type `ml.t2.medium` (or `ml.m5.large` for production).
- **SageMaker Endpoint:** The actual real-time inference URL.

### C. Compute (EC2)
- **EC2 Instance:** Ubuntu 22.04 LTS.
- **User Data Script:** Automated script to install Docker, Docker Compose, and AWS CLI.
- **IAM Instance Profile:** Allow EC2 to call `sagemaker:InvokeEndpoint`.

## 3. TASK FOR CLAUDE
Please generate the Terraform HCL code organized into:
1. `provider.tf`: AWS Region and provider config.
2. `variables.tf`: For region, instance types, and bucket names.
3. `vpc.tf`: Networking setup.
4. `iam.tf`: Roles for EC2 and SageMaker.
5. `sagemaker.tf`: The core ML endpoint infrastructure.
6. `ec2.tf`: The web server hosting Next.js and FastAPI.
7. `outputs.tf`: Display the EC2 Public IP and SageMaker Endpoint Name.

## 4. EXECUTION STRATEGY
- Start by generating the **IAM and S3** parts first to ensure permissions are correct.
- Then, provide the **SageMaker Endpoint** configuration.
- Finally, provide the **EC2 User Data** script that will pull the Docker images (Next.js/FastAPI) and run them.

Please confirm you can handle this Terraform architecture and let's start with the `iam.tf` and `sagemaker.tf` files.