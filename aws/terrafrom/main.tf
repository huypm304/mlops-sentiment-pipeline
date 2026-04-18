# 1. Khai báo Security Group (Mở cổng 80 cho Web và 8000 cho API)
resource "aws_security_group" "web_sg" {
  name        = "${var.project_name}-web-sg"
  description = "Allow HTTP and API traffic"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Cổng SSH để Huy có thể vào debug nếu cần
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Khai báo SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "config" {
  name = "${var.project_name}-config"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.absa_model.name
    initial_instance_count = 1
    instance_type          = "ml.t2.medium" 
  }
}
# 3. Khai báo SageMaker Endpoint (Cái mà EC2 đang đợi tên đây)
resource "aws_sagemaker_endpoint" "endpoint" {
  name                 = "${var.project_name}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.config.name
}