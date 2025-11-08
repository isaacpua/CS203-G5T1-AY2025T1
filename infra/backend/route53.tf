# Create the "A" record for api.tarific.rocks
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "${var.backend_subdomain}.${var.domain_name}" # api.tarific.rocks
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
