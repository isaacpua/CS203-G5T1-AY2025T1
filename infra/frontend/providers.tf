terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

# default provider
provider "aws" {
  region = "ap-southeast-1"
}

# provider exclusively for CloudFront ACM cert
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
