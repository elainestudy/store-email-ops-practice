locals {
  name_prefix = "${var.project_name}-${var.environment}"
  mime_types = {
    css  = "text/css"
    html = "text/html"
    js   = "application/javascript"
    json = "application/json"
    png  = "image/png"
    svg  = "image/svg+xml"
  }
}

resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.name_prefix}-frontend-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "frontend_public" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

resource "aws_s3_object" "frontend_files" {
  for_each = fileset(var.frontend_build_dir, "**/*")

  bucket       = aws_s3_bucket.frontend.id
  key          = each.value
  source       = "${var.frontend_build_dir}/${each.value}"
  etag         = filemd5("${var.frontend_build_dir}/${each.value}")
  content_type = lookup(local.mime_types, reverse(split(".", each.value))[0], "application/octet-stream")
}

resource "aws_sqs_queue" "campaign_send_requests" {
  name                       = "${local.name_prefix}-campaign-send-requests"
  visibility_timeout_seconds = 60
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "MUTABLE"
}

resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${local.name_prefix}-apprunner-ecr-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_apprunner_service" "flask_api" {
  service_name = "${local.name_prefix}-api"

  source_configuration {
    auto_deployments_enabled = false
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          ENVIRONMENT        = var.environment
          MESSAGE_BUS_BACKEND = "sqs"
          SQS_QUEUE_URL      = aws_sqs_queue.campaign_send_requests.id
          INTERNAL_API_TOKEN = var.internal_api_token
          DATABASE_URL       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/emailops"
        }
      }
    }
  }
}

data "archive_file" "lambda_email_sender" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/email_sender"
  output_path = "${path.module}/build/email_sender.zip"
}

resource "aws_iam_role" "lambda_email_sender" {
  name = "${local.name_prefix}-lambda-email-sender"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_email_sender.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_ses_access" {
  name = "${local.name_prefix}-lambda-ses-access"
  role = aws_iam_role.lambda_email_sender.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "email_sender" {
  function_name = "${local.name_prefix}-email-sender"
  role          = aws_iam_role.lambda_email_sender.arn
  handler       = "handler.handler"
  runtime       = "python3.13"
  filename      = data.archive_file.lambda_email_sender.output_path
  source_code_hash = data.archive_file.lambda_email_sender.output_base64sha256
  timeout       = 60

  environment {
    variables = {
      SES_FROM_EMAIL    = var.ses_from_email
      BACKEND_BASE_URL  = "https://${aws_apprunner_service.flask_api.service_url}"
      INTERNAL_API_TOKEN = var.internal_api_token
      DATABASE_URL      = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/emailops"
    }
  }

  depends_on = [aws_db_instance.postgres]
}

resource "aws_lambda_event_source_mapping" "email_sender_sqs" {
  event_source_arn = aws_sqs_queue.campaign_send_requests.arn
  function_name    = aws_lambda_function.email_sender.arn
  batch_size       = 1
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Security group for RDS database"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "${local.name_prefix}-db"
  engine                 = "postgres"
  engine_version         = var.db_engine_version
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp2"

  db_name  = "emailops"
  username = var.db_username
  password = var.db_password

  publicly_accessible    = true
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}
