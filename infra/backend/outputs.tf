output "api_endpoint" {
  description = "The publicly accessible URL for the backend API"
  value       = "https://${aws_route53_record.api.fqdn}"
}
