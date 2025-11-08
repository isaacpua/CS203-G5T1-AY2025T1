variable "domain_name" {
  type        = string
  description = "The domain name"
}

variable "bucket_name" {
  type        = string
  description = "S3 bucket name for the frontend"
}

variable "aws_account_id" {
  type        = string
  description = "AWS Account ID"
}
