resource "aws_key_pair" "deployer" {
  key_name   = "my-ssh-key-v2"
  public_key = file("~/.ssh/id_rsa.pub") 
}

resource "aws_instance" "web_server" {
  key_name             = aws_key_pair.deployer.key_name
  ami                  = "ami-0e7ff22101b84bcff" 
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y git docker.io docker-compose
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ubuntu
              
              echo "SAGEMAKER_ENDPOINT_NAME=${aws_sagemaker_endpoint.endpoint.name}" >> /etc/environment
              echo "AWS_REGION=${var.aws_region}" >> /etc/environment
              source /etc/environment

              cd /home/ubuntu
              git clone https://github.com/huypm304/mlops-sentiment-pipeline.git repo
              
              cd repo
              git checkout feature/test
              git pull origin feature/test

              cd /home/ubuntu
              chown -R ubuntu:ubuntu repo

              cd repo
              docker-compose up --build -d
              EOF

  tags = { Name = "ABSA-Web-Portal" }
}

# Lấy trực tiếp IP Public động của Instance
output "public_ip" {
  value       = aws_instance.web_server.public_ip

}