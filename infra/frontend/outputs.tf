output "route53_zone_id" {
  value = aws_route53_zone.primary.zone_id
}

output "route53_ns" {
  value = aws_route53_zone.primary.name_servers
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.spa.domain_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.spa.bucket
}
