# Terraform Notes

This folder provisions:

- An S3 bucket for the React frontend
- An SQS queue for asynchronous campaign send requests
- An App Runner service for the Flask API
- A Lambda function that consumes SQS messages and sends emails through SES

Expected deployment flow:

1. Build the frontend with `npm run build` in `frontend/`
2. Build and push the Flask API image to the ECR repository Terraform creates
3. Run `terraform apply`

The Flask service is configured to publish send jobs to SQS. The Lambda function consumes those jobs, sends emails, and posts delivery results back to the Flask internal API.
