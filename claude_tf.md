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
# TERRAFORM FULL-STACK AUTOMATION (MLOPS PORTAL)

I want to build a Terraform project where running `terraform apply` provisions EVERYTHING so that the system is immediately ready for user feedback.

## 1. INFRASTRUCTURE REQUIREMENTS (AWS)
- **VPC & Networking:** Setup a standard VPC with a Public Subnet and Security Groups.
- **S3 Bucket:** Create a bucket and upload `model.tar.gz` (use `aws_s3_object`).
- **SageMaker Endpoint:** - `aws_sagemaker_model`: Point to the S3 artifact and use a PyTorch inference container.
    - `aws_sagemaker_endpoint_configuration`: Use `ml.t2.medium` for cost-saving.
    - `aws_sagemaker_endpoint`: The live URL for inference.
- **EC2 Instance (The Host):**
    - Type: `t3.medium` (Ubuntu 22.04).
    - IAM Role: Assign a role with `SageMakerFullAccess` so the backend can call the endpoint.

## 2. THE "MAGIC" USER DATA (BOOTSTRAP SCRIPT)
The EC2 instance must automatically:
1. Install Docker and Docker Compose.
2. Clone my Github Repository (or pull pre-built Docker images).
3. Generate an `.env` file dynamically: 
    - Insert the `SAGEMAKER_ENDPOINT_NAME` (exported from Terraform).
    - Insert `AWS_REGION`.
4. Run `docker-compose up -d`.

## 3. PROJECT STRUCTURE FOR TERRAFORM
Please generate the following files:
- `main.tf`: Provider and VPC setup.
- `s3_sagemaker.tf`: S3 bucket, model artifact upload, and SageMaker Endpoint.
- `ec2_app.tf`: EC2 provisioning with the `user_data` script to start the Web/API containers.
- `iam.tf`: Roles for EC2 to talk to SageMaker.
- `outputs.tf`: Final Public IP of the web portal.

## 4. INTEGRATION LOGIC
- The **FastAPI Backend** inside the Docker container must use `boto3` to call the SageMaker endpoint name provided in the `.env`.
- The **Next.js Frontend** must point to the FastAPI service.

Please write the complete Terraform HCL code. For the EC2 `user_data`, make it robust enough to handle the Docker installation and environment injection.