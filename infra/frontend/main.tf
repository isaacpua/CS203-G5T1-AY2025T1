# ---------- Route53 hosted zone ----------
resource "aws_route53_zone" "primary" {
  name = var.domain_name
}

resource "aws_route53_record" "www_alias" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "www"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.spa.domain_name
    zone_id                = aws_cloudfront_distribution.spa.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "root_alias" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = var.domain_name
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.spa.domain_name
    zone_id                = aws_cloudfront_distribution.spa.hosted_zone_id
    evaluate_target_health = false
  }
}

# ---------- S3 bucket for SPA ----------
resource "aws_s3_bucket" "spa" {
  bucket        = var.bucket_name
  force_destroy = true
}

# Ownership & ACL
resource "aws_s3_bucket_ownership_controls" "spa" {
  bucket = aws_s3_bucket.spa.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# resource "aws_s3_bucket_acl" "spa" {
#   bucket     = aws_s3_bucket.spa.id
#   acl        = "private"
#   depends_on = [aws_s3_bucket_ownership_controls.spa]
# }

# Versioning
resource "aws_s3_bucket_versioning" "spa" {
  bucket = aws_s3_bucket.spa.id
  versioning_configuration {
    status = "Disabled"
  }
}

# Lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "spa" {
  bucket = aws_s3_bucket.spa.id

  rule {
    id     = "cleanup"
    status = "Enabled"

    # This means "apply to all objects"
    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}


# Block all public access
resource "aws_s3_bucket_public_access_block" "spa_block" {
  bucket                  = aws_s3_bucket.spa.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- CloudFront Origin Access Identity ----------
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for ${var.domain_name} SPA"
}

data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions = ["s3:GetObject"]
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.oai.iam_arn]
    }
    resources = ["${aws_s3_bucket.spa.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "spa_policy" {
  bucket = aws_s3_bucket.spa.id
  policy = data.aws_iam_policy_document.s3_policy.json
}

# ---------- ACM certificate in us-east-1 for CloudFront ----------
resource "aws_acm_certificate" "cf_cert" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "www.${var.domain_name}"
  ]
  lifecycle {
    create_before_destroy = true
  }
}

# DNS validation record in Route53 for the us-east-1 cert
# Use the certificate's domain_validation_options to create records automatically
resource "aws_route53_record" "cf_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cf_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id    = aws_route53_zone.primary.zone_id
  name       = each.value.name
  type       = each.value.type
  ttl        = 60
  records    = [each.value.record]
  depends_on = [aws_acm_certificate.cf_cert]
}

# Wait for the cert to be validated
resource "aws_acm_certificate_validation" "cf_cert_validation" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cf_cert.arn
  validation_record_fqdns = [for rec in aws_route53_record.cf_cert_validation : rec.fqdn]
}

# ---------- CloudFront distribution ----------
resource "aws_cloudfront_distribution" "spa" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "CloudFront for ${var.domain_name}"
  depends_on = [aws_acm_certificate_validation.cf_cert_validation]

  aliases = [var.domain_name, "www.${var.domain_name}"]

  origin {
    domain_name = aws_s3_bucket.spa.bucket_regional_domain_name
    origin_id   = "s3-spa-origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-spa-origin"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.cf_cert.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2019"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  price_class = "PriceClass_100" # cheapest edge locations — adjust as needed

  # routes all 403 (Access Denied) and 404 (Not Found) errors
  # back to index.html, allowing the client-side SPA router to work
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }
}
