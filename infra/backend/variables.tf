variable "aws_region" {
  description = "The AWS region to deploy the backend infrastructure."
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "A name for the project, used to prefix all resources."
  type        = string
  default     = "tarific"
}

variable "vpc_cidr" {
  description = "The CIDR block for the main VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "domain_name" {
  description = "The root domain name"
  type        = string
}

variable "backend_subdomain" {
  description = "The subdomain for the backend API"
  type        = string
  default     = "api"
}

variable "instance_type" {
  description = "EC2 instance type for the backend services"
  type        = string
  default     = "t3.small"
}
