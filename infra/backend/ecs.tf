# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  # container insights for better monitoring
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Central Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name = "/ecs/${var.project_name}"
  retention_in_days = 7
}

# Internal DNS for mcp-server
resource "aws_service_discovery_private_dns_namespace" "internal" {
  name = "${var.project_name}.local" # tarific.local
  vpc  = aws_vpc.main.id
}

# EC2 Instance Configuration
# tell the EC2 instances which cluster to join
data "template_file" "ecs_user_data" {
  template = <<-EOF
    #!/bin/bash
    echo "ECS_CLUSTER=${aws_ecs_cluster.main.name}" >> /etc/ecs/ecs.config
  EOF
}

# EC2 Launch Template, blueprint for t3.smalls
data "aws_ssm_parameter" "ecs_optimized_ami" {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
}

resource "aws_launch_template" "ecs" {
  name          = "${var.project_name}-ecs-lt"
  image_id      = data.aws_ssm_parameter.ecs_optimized_ami.value
  instance_type = var.instance_type
  
  iam_instance_profile {
    arn = aws_iam_instance_profile.ecs_instance_profile.arn
  }

  # assign the ECS service security group to the instances
  network_interfaces {
    security_groups = [aws_security_group.ecs_service.id]
    # set this to true to associate with private subnets
    associate_public_ip_address = false 
  }

  user_data = base64encode(data.template_file.ecs_user_data.rendered)
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-ecs-instance"
    }
  }
}

resource "aws_launch_template" "ecs_mcp_server" {
  name          = "${var.project_name}-ecs-mcp-server-lt"
  image_id      = data.aws_ssm_parameter.ecs_optimized_ami.value
  instance_type = "m7i-flex.large"

  iam_instance_profile {
    arn = aws_iam_instance_profile.ecs_instance_profile.arn
  }

  network_interfaces {
    security_groups = [aws_security_group.ecs_service.id]
    associate_public_ip_address = false 
  }

  user_data = base64encode(data.template_file.ecs_user_data.rendered)
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-ecs-mcp-server-instance"
    }
  }
}

# Auto Scaling Group (ASG) for tariff-backend
resource "aws_autoscaling_group" "tariff" {
  name = "${var.project_name}-tariff-asg"
  
  # run in private, secure subnets
  vpc_zone_identifier = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  
  # start with 1 instance, scale up to 3 if needed
  min_size         = 1
  max_size         = 3
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.ecs.id
    version = "$Latest"
  }

  # this tag is CRITICAL. It tells ECS which instances to use.
  tag {
    key                 = "AmazonECSManaged"
    value               = ""
    propagate_at_launch = true
  }
}

# Auto Scaling Group (ASG) for MCP-Gateway
resource "aws_autoscaling_group" "mcp_gateway" {
  name = "${var.project_name}-mcp-gateway-asg"
  
  vpc_zone_identifier = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  
  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.ecs.id
    version = "$Latest"
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = ""
    propagate_at_launch = true
  }
}

# Auto Scaling Group (ASG) for MCP-Chatbot
resource "aws_autoscaling_group" "mcp_chatbot" {
  name = "${var.project_name}-mcp-chatbot-asg"
  
  vpc_zone_identifier = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  
  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.ecs.id # Uses the t3.small template
    version = "$Latest"
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = ""
    propagate_at_launch = true
  }
}

# Auto Scaling Group (ASG) for MCP-Server
# runs on its own dedicated instance
resource "aws_autoscaling_group" "mcp_server" {
  name = "${var.project_name}-mcp-server-asg"
  
  vpc_zone_identifier = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  
  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.ecs_mcp_server.id
    version = "$Latest"
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = ""
    propagate_at_launch = true
  }
}

# ECS Capacity Providers (Link ASGs to Cluster)
resource "aws_ecs_capacity_provider" "tariff_cp" {
  name = "tariff-cp"
  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.tariff.arn
    managed_scaling {
      status = "ENABLED"
      target_capacity = 100
    }
  }
}


# Capacity Provider for MCP-Gateway
resource "aws_ecs_capacity_provider" "mcp_gateway_cp" {
  name = "mcp-gateway-cp"
  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.mcp_gateway.arn
    managed_scaling {
      status = "ENABLED"
      target_capacity = 100
    }
  }
}

# Capacity Provider for MCP-Chatbot
resource "aws_ecs_capacity_provider" "mcp_chatbot_cp" {
  name = "mcp-chatbot-cp"
  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.mcp_chatbot.arn
    managed_scaling {
      status = "ENABLED"
      target_capacity = 100
    }
  }
}

resource "aws_ecs_capacity_provider" "mcp_server_cp" {
  name = "mcp-server-cp"
  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.mcp_server.arn
    managed_scaling {
      status = "ENABLED"
      target_capacity = 100
    }
  }
}

# ASSOCIATE CAPACITY PROVIDERS WITH THE CLUSTER
# tell the cluster it is allowed to use these providers.
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = [
    aws_ecs_capacity_provider.tariff_cp.name,
    aws_ecs_capacity_provider.mcp_gateway_cp.name,
    aws_ecs_capacity_provider.mcp_chatbot_cp.name,
    aws_ecs_capacity_provider.mcp_server_cp.name
  ]

  # We also set a default strategy for any services that don't specify one
  default_capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.tariff_cp.name
    weight            = 1
  }
}

# TASK: tariff-backend
resource "aws_ecs_task_definition" "tariff" {
  family                   = "${var.project_name}-tariff"
  network_mode             = "awsvpc" # Required for security
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  # define the container
  container_definitions = jsonencode([{
    name  = "tariff-backend"
    image = "${aws_ecr_repository.backend_repos["tariff-backend"].repository_url}:latest"
    memoryReservation = 1664
    portMappings = [{
      containerPort = 8080
      hostPort      = 8080
      protocol      = "tcp"
    }]
    
    # inject secrets as env var
    secrets = [
      { name = "DB_URL", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_URL::" },
      { name = "DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_USERNAME::" },
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_PASSWORD::" },
      { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:OPENAI_API_KEY::" },
      { name = "JWT_SECRET", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:JWT_SECRET::" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "tariff-backend"
      }
    }
  }])
}

# TASK: mcp-gateway-backend
resource "aws_ecs_task_definition" "mcp_gateway" {
  family                   = "${var.project_name}-mcp-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "mcp-gateway-backend"
    image = "${aws_ecr_repository.backend_repos["mcp-gateway-backend"].repository_url}:latest"
    memoryReservation = 1664
    portMappings = [{
      containerPort = 8090
      hostPort      = 8090
      protocol      = "tcp"
    }]
    
    # inject secrets as env var
    secrets = [
      { name = "DB_URL", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_URL::" },
      { name = "DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_USERNAME::" },
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_PASSWORD::" },
      { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:OPENAI_API_KEY::" }
    ]

    # Change internal DNS name
    # replaces BASE_URL: "http://mcp-server-backend:8000" with http://mcp-server.tarific.local:8000
    environment = [
      { name = "BASE_URL", value = "http://mcp-server.${aws_service_discovery_private_dns_namespace.internal.name}:8000" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "mcp-gateway"
      }
    }
  }])
}

# TASK: mcp-chatbot-backend
resource "aws_ecs_task_definition" "mcp_chatbot" {
  family                   = "${var.project_name}-mcp-chatbot"
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "mcp-chatbot-backend"
    image = "${aws_ecr_repository.backend_repos["mcp-chatbot-backend"].repository_url}:latest"
    memoryReservation = 1664
    portMappings = [{
      containerPort = 8001
      hostPort      = 8001
      protocol      = "tcp"
    }]
    
    # inject secrets as env var
    secrets = [
      { name = "DB_URL", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_URL::" },
      { name = "DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_USERNAME::" },
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_PASSWORD::" },
      { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:OPENAI_API_KEY::" }
    ]
    
    # replaces BASE_URL: "http://mcp-server-backend:8000" with http://mcp-server.tarific.local:8000
    environment = [
      { name = "BASE_URL", value = "http://mcp-server.${aws_service_discovery_private_dns_namespace.internal.name}:8000" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "mcp-chatbot"
      }
    }
  }])
}

# TASK: mcp-server-backend
resource "aws_ecs_task_definition" "mcp_server" {
  family                   = "${var.project_name}-mcp-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "mcp-server-backend"
    image = "${aws_ecr_repository.backend_repos["mcp-server-backend"].repository_url}:latest"
    memoryReservation = 1536 # Reserve 1.5 GB
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]
    
    # inject secrets as env var
    secrets = [
      { name = "DB_URL", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_URL::" },
      { name = "DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_USERNAME::" },
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:DB_PASSWORD::" },
      { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.backend_env.arn}:OPENAI_API_KEY::" },
      
      # injects JSON files as env var
      { name = "TOKEN_JSON", valueFrom = aws_secretsmanager_secret.mcp_token_json.arn }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "mcp-server"
      }
    }
  }])
}


# The ECS Services (Run and manage the tasks)
# SERVICE: tariff-backend
resource "aws_ecs_service" "tariff" {
  name    = "${var.project_name}-tariff"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.tariff.arn
  desired_count = 1
  enable_execute_command = true

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.tariff_cp.name
    weight            = 1
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tariff.arn
    container_name   = "tariff-backend"
    container_port   = 8080
  }

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_groups = [aws_security_group.ecs_service.id]
  }
}

# SERVICE: mcp-gateway-backend
resource "aws_ecs_service" "mcp_gateway" {
  name    = "${var.project_name}-mcp-gateway"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_gateway.arn
  desired_count = 1
  enable_execute_command = true

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.mcp_gateway_cp.name
    weight            = 1
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.mcp_gateway.arn
    container_name   = "mcp-gateway-backend"
    container_port   = 8090
  }

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_groups = [aws_security_group.ecs_service.id]
  }
}

# SERVICE: mcp-chatbot-backend
resource "aws_ecs_service" "mcp_chatbot" {
  name    = "${var.project_name}-mcp-chatbot"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_chatbot.arn
  desired_count = 1
  enable_execute_command = true

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.mcp_chatbot_cp.name
    weight            = 1
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.mcp_chatbot.arn
    container_name   = "mcp-chatbot-backend"
    container_port   = 8001
  }

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_groups = [aws_security_group.ecs_service.id]
  }
}

# SERVICE: mcp-server-backend
resource "aws_ecs_service" "mcp_server" {
  name    = "${var.project_name}-mcp-server"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_server.arn
  desired_count = 1
  enable_execute_command = true

  # key: it runs on its DEDICATED capacity provider
  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.mcp_server_cp.name
    weight            = 1
  }

  # Internal Service Discovery
  # register the service at mcp-server.tarific.local
  service_registries {
    registry_arn = aws_service_discovery_service.mcp_server.arn
  }

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_groups = [aws_security_group.ecs_service.id]
  }

  # NO load balancer, internal-only.
}

# create the mcp-server.tarific.local DNS record
resource "aws_service_discovery_service" "mcp_server" {
  name = "mcp-server"
  
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.internal.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}
