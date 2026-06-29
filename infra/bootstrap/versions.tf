terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Bootstrap uses local state because it manages the remote state bucket.
  # After first apply, commit the generated terraform.tfstate to a safe location
  # or move it manually to the created bucket.
  backend "local" {}
}
