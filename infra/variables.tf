variable "aws_region" {
  type        = string
  description = "AWS region for deployment."
  default     = "us-west-2"
}

variable "project_name" {
  type        = string
  description = "Name prefix for created resources."
  default     = "store-email-ops"
}

variable "environment" {
  type        = string
  description = "Environment name."
  default     = "dev"
}

variable "backend_image_tag" {
  type        = string
  description = "Docker image tag for the Flask API container."
  default     = "latest"
}

variable "frontend_build_dir" {
  type        = string
  description = "Local path to the built frontend assets."
  default     = "../frontend/dist"
}

variable "ses_from_email" {
  type        = string
  description = "Verified SES sender email."
}

variable "internal_api_token" {
  type        = string
  description = "Shared token used by Lambda to post delivery results back to the API."
  sensitive   = true
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class for PostgreSQL database."
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage for RDS database in GB."
  default     = 20
}

variable "db_engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "15"
}

variable "db_username" {
  type        = string
  description = "Master username for RDS database."
  default     = "dbadmin"
}

variable "db_password" {
  type        = string
  description = "Master password for RDS database."
  sensitive   = true
}
