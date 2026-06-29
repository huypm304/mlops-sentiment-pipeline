resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name = var.domain_name
  }
}

data "aws_route53_zone" "existing" {
  count = var.create_hosted_zone ? 0 : 1

  zone_id = var.zone_id != "" ? var.zone_id : null
  name    = var.zone_id == "" ? var.domain_name : null
}

locals {
  zone_id = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
}

resource "aws_route53_record" "www" {
  count = var.www_cname_target != "" ? 1 : 0

  zone_id = local.zone_id
  name    = "www"
  type    = "CNAME"
  ttl     = 300
  records = [var.www_cname_target]
}
