output "certificate_arn" {
  value = local.certificate_arn
}

output "domain_name" {
  value = aws_acm_certificate.main.domain_name
}
