# ALB Security Group
# allow public inbound HTTPS traffic and all outbound traffic
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allows inbound HTTPS traffic"
  vpc_id      = aws_vpc.main.id

  # inbound: allow HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # outbound: allow all traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# ECS Service Security Group
# allow inbound traffic ONLY from the ALB and allows all outbound traffic
resource "aws_security_group" "ecs_service" {
  name        = "${var.project_name}-ecs-service-sg"
  description = "Allows inbound traffic from ALB"
  vpc_id      = aws_vpc.main.id

  # allow containers in this group to talk to each other
  # mcp-chatbot -> mcp-server communication.
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
    description = "Allow internal container-to-container traffic"
  }

  # inbound: allow all traffic from the ALB's security group
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb.id]
  }

  # outbound: allow all traffic
  # lets containers talk to the internet for APIs and talk to RDS database
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-service-sg"
  }
}
