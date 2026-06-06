output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC provider."
  value       = aws_iam_openid_connect_provider.github.arn
}

output "github_deploy_role_arn" {
  description = "ARN of the GitHub Actions deploy role. Use this as AWS_ROLE_ARN in the repository's Action secrets."
  value       = aws_iam_role.github_deploy.arn
}

output "github_deploy_role_name" {
  value = aws_iam_role.github_deploy.name
}
