# Store Email Ops Practice

[![Tests & Quality](https://github.com/elainestudy/store-email-ops-practice/actions/workflows/tests.yml/badge.svg)](https://github.com/elainestudy/store-email-ops-practice/actions)
[![codecov](https://codecov.io/gh/elainestudy/store-email-ops-practice/branch/main/graph/badge.svg)](https://codecov.io/gh/elainestudy/store-email-ops-practice)

This repository is a focused practice project for a store email operations tool.

The project goal is to simulate an internal tool that store teams can use to send email communication to customers.

## Project Story

We are building a small internal email operations platform:

- Store users create email campaigns
- The back-end stores campaign data and recipient information
- Email send jobs are processed asynchronously
- Delivery attempts and failures are tracked
- The system is designed with testing, security, and AWS deployment in mind

This single project lets us practice:

- Python with Flask
- JavaScript with React
- SQLAlchemy / SQLModel
- AWS architecture with Lambda, SQS and RDS
- Terraform
- BDD Testing patterns
- Security-minded implementation choices

## Architecture Overview

### Core Components

**Flask API** (`app/api/`)
- Health check endpoint
- Campaign CRUD endpoints
- Campaign send endpoint (triggers async processing)
- Delivery attempt tracking endpoints
- Request validation with Pydantic schemas

**Data Models** (`app/models.py`)
- `Campaign`: Campaign metadata (name, subject, body, store_id, status)
- `Recipient`: Email recipients per campaign with delivery status
- `DeliveryAttempt`: Operational records of email send attempts
- `AuditLog`: Audit trail for campaign lifecycle events

**Service Layer** (`app/services/`)
- `CampaignService`: Business logic for campaign operations
  - Create campaigns with recipients
  - Enqueue campaigns for async sending
  - Retrieve delivery attempts and results
  - Audit logging on every operation
- `FakeEmailSender`: Simulated email sending (for local testing)

**Message Queue Abstraction** (`app/messaging/`)
- Pluggable message bus interface
- `MemoryBus`: In-memory queue (default for local development)
- `KafkaProducer`: Kafka integration for production-like testing
- `SQSProducer`: AWS SQS integration for cloud deployment

**Worker Process** (`app/worker.py`)
- Long-running worker that consumes send requests from the queue
- Simulates email sending
- Records delivery attempts with status and retry logic
- Updates campaign status

**Database Layer** (`app/db.py`)
- SQLModel ORM with SQLAlchemy
- SQLite for local development (configurable via `DATABASE_URL`)
- Session management and connection pooling

### Request Flow

```
1. POST /campaigns          → Create campaign with recipients
2. POST /campaigns/{id}/send → Publish send request to queue
3. Worker consumes message   → Attempts email delivery
4. GET /campaigns/{id}/delivery-attempts → Check delivery status
```

### Key Features

- ✅ **Campaign Management**: Create, list, and manage email campaigns
- ✅ **Async Workflow**: Decouple request handling from email delivery
- ✅ **Reliable Delivery Tracking**: Record all send attempts with timestamps and messages
- ✅ **Audit Trail**: Log all important system events for compliance
- ✅ **Pluggable Queue Backend**: Switch between in-memory, Kafka, or SQS
- ✅ **Retry Support**: Configurable retry logic for failed attempts
- ✅ **Testing Ready**: Full BDD test suite with pytest and pytest-bdd