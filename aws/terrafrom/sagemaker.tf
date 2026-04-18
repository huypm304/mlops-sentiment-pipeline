# Tạo ID ngẫu nhiên để tên Bucket không bị trùng trên toàn cầu
resource "random_id" "id" {
  byte_length = 4
}

# 1. Khai báo cái thùng chứa
resource "aws_s3_bucket" "model_bucket" {
  bucket = "${var.project_name}-artifacts-${random_id.id.hex}"
}

# 2. Lệnh đẩy file từ máy Huy lên S3
resource "aws_s3_object" "model_artifact" {
  bucket = aws_s3_bucket.model_bucket.id
  key    = "model.tar.gz"
  source = "model.tar.gz" # File này phải nằm cùng thư mục với file .tf
  etag   = filemd5("model.tar.gz")
}

# 3. Định nghĩa Model SageMaker
resource "aws_sagemaker_model" "absa_model" {
  name               = "${var.project_name}-model"
  execution_role_arn = aws_iam_role.sagemaker_execution_role.arn

  depends_on = [aws_s3_object.model_artifact]

  primary_container {
    image          = "763104351884.dkr.ecr.ap-southeast-1.amazonaws.com/pytorch-inference:1.12.1-cpu-py38"
    model_data_url = "s3://${aws_s3_bucket.model_bucket.bucket}/${aws_s3_object.model_artifact.key}"

    environment = {
      SAGEMAKER_PROGRAM = "inference.py"
    }
  }
}