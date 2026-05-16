module "platform" {
  source = "../.."

  aws_region   = var.aws_region
  project_name = var.project_name
  environment  = "prod"

  lambda_memory_mb          = var.lambda_memory_mb
  lambda_timeout_seconds    = var.lambda_timeout_seconds
  enable_sagemaker_endpoint = var.enable_sagemaker_endpoint
  sagemaker_instance_type   = var.sagemaker_instance_type
  cors_allow_origins = var.cors_allow_origins

  domain_name          = var.domain_name
  enable_custom_domain = var.enable_custom_domain
  create_hosted_zone   = var.create_hosted_zone
  route53_zone_id      = var.route53_zone_id
  api_subdomain        = var.api_subdomain
  www_cname_target     = var.www_cname_target
}
