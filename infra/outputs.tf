output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.id
}

output "frontend_website_url" {
  value = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "backend_service_url" {
  value = aws_apprunner_service.flask_api.service_url
}

output "sqs_queue_url" {
  value = aws_sqs_queue.campaign_send_requests.id
}

output "lambda_function_name" {
  value = aws_lambda_function.email_sender.function_name
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "RDS PostgreSQL endpoint"
}

output "rds_database_name" {
  value       = aws_db_instance.postgres.db_name
  description = "RDS database name"
}

output "database_url" {
  value       = "postgresql://${var.db_username}:***@${aws_db_instance.postgres.endpoint}/emailops"
  description = "PostgreSQL connection string (password masked)"
  sensitive   = true
}
