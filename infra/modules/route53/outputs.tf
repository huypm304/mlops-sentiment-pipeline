output "zone_id" {
  value = local.zone_id
}

output "zone_arn" {
  value = var.create_hosted_zone ? aws_route53_zone.main[0].arn : data.aws_route53_zone.existing[0].arn
}

output "name_servers" {
  description = "Set these as custom nameservers in Namecheap."
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : data.aws_route53_zone.existing[0].name_servers
}
