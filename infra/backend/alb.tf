# Route 53 Zone Data Source
# safely LOOKS UP the Hosted Zone the frontend created
data "aws_route53_zone" "primary" {
  name = var.domain_name
}

# ACM Certificate for the API
# certificate is for backend (api.tarific.rocks)
resource "aws_acm_certificate" "api_cert" {
  domain_name = "${var.backend_subdomain}.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# DNS Validation for the Certificate
# create the CNAME record in Route 53 to prove ownership of the domain
resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = data.aws_route53_zone.primary.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

# wait for validation to complete
resource "aws_acm_certificate_validation" "api_cert_validation" {
  certificate_arn         = aws_acm_certificate.api_cert.arn
  validation_record_fqdns = [for rec in aws_route53_record.api_cert_validation : rec.fqdn]
}

# Application Load Balancer (ALB)
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false # This is public-facing
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  # place the ALB in public subnets
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# Target Groups (Pools of Containers)
# One for each backend service from docker-compose.yml
resource "aws_lb_target_group" "tariff" {
  name        = "${var.project_name}-tariff"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # Required for ECS

  health_check {
    path = "/api/v1/health"
  }
}

resource "aws_lb_target_group" "mcp_gateway" {
  name        = "${var.project_name}-mcp-gtw"
  port        = 8090
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/mcp/api/v1/health"
  }
}

resource "aws_lb_target_group" "mcp_chatbot" {
  name        = "${var.project_name}-mcp-chat"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  # enables "stickiness" for WebSocket connections
  stickiness {
    type    = "lb_cookie"
    enabled = true
  }

  health_check {
    path = "/chat/health"
  }
}

# NOTE: mcp-server does not get a target group, because it is NOT public-facing. It will be discovered using internal DNS.

# The HTTPS Listener
# "front door" of the ALB
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate_validation.api_cert_validation.certificate_arn

  # send unmatched requests to the main tariff backend
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tariff.arn
  }
}

# Listener Rules
# These rules route traffic based on the URL path.

# /api/v1/* -> tariff-backend
resource "aws_lb_listener_rule" "tariff_rule" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tariff.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/*"]
    }
  }
}

# /mcp/api/v1/* -> mcp-gateway-backend
resource "aws_lb_listener_rule" "mcp_gateway_rule" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp_gateway.arn
  }

  condition {
    path_pattern {
      values = ["/mcp/api/v1/*"]
    }
  }
}

# /chat/* -> mcp-chatbot-backend
resource "aws_lb_listener_rule" "mcp_chatbot_rule" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 80

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp_chatbot.arn
  }

  condition {
    path_pattern {
      values = ["/chat/*"]
    }
  }
}
